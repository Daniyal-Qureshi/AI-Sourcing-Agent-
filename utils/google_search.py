"""
Google Search Utility for LinkedIn Profiles
Combines the logic from deepseek-ai-web-crawler with modern search approaches
"""
import asyncio
import logging
import re
from typing import List, Optional, Set
from urllib.parse import urlencode, quote_plus
from datetime import datetime

from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from bs4 import BeautifulSoup

from models.linkedin_profile import SearchResult, validate_linkedin_url, clean_linkedin_url
from config.settings import (
    get_browser_config, 
    get_search_config, 
    GOOGLE_SEARCH_BASE_URL,
    REQUEST_DELAY,
    MAX_RETRIES,
    RETRY_DELAY
)

logger = logging.getLogger(__name__)


class GoogleSearchError(Exception):
    """Custom exception for Google search errors."""
    pass


class LinkedInSearcher:
    """
    LinkedIn profile searcher using Google search.
    Combines deepseek crawler logic with Playwright automation.
    """
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.search_config = get_search_config()
        self.browser_config = get_browser_config()
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start_browser()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close_browser()
        
    async def start_browser(self) -> None:
        """Start the browser and create context."""
        playwright = await async_playwright().start()
        
        self.browser = await playwright.chromium.launch(
            headless=self.browser_config["headless"],
            args=self.browser_config["args"]
        )
        
        self.context = await self.browser.new_context(
            user_agent=self.browser_config["user_agent"],
            viewport=self.browser_config["viewport"]
        )
        
        self.page = await self.context.new_page()
        logger.info("✅ Browser started successfully")
        
    async def close_browser(self) -> None:
        """Close the browser and cleanup."""
        if self.browser:
            await self.browser.close()
            logger.info("🔒 Browser closed")
    
    def construct_search_query(self, search_terms: List[str]) -> str:
        """
        Construct Google search query for LinkedIn profiles.
        Format: site:linkedin.com/in "term1" "term2" "term3"
        """
        # Add site restriction for LinkedIn profiles
        query_parts = ["site:linkedin.com/in"]
        
        # Add quoted search terms
        for term in search_terms:
            # Clean and quote the term
            clean_term = term.strip().strip('"')
            if clean_term:
                query_parts.append(f'"{clean_term}"')
        
        search_query = " ".join(query_parts)
        logger.info(f"🔍 Constructed search query: {search_query}")
        return search_query
    
    def construct_search_url(self, search_query: str, start: int = 0) -> str:
        """Construct the complete Google search URL."""
        params = {
            "q": search_query,
            "num": 50,  # Number of results per page
            "start": start,  # Starting index for pagination
            "hl": "en",  # Language
            "gl": "us"   # Geolocation
        }
        
        return f"{GOOGLE_SEARCH_BASE_URL}?{urlencode(params)}"
    
    async def handle_google_consent(self) -> None:
        """Handle Google consent/cookie popup if it appears."""
        try:
            # Wait a bit for popup to appear
            await self.page.wait_for_timeout(2000)
            
            # Common consent button selectors
            consent_selectors = [
                'button:has-text("Accept all")',
                'button:has-text("I agree")',
                'button:has-text("Accept")',
                '[aria-label*="Accept"]',
                '#L2AGLb',  # Google's "I agree" button ID
                'button[jsname="b3VHJd"]'  # Alternative Google consent button
            ]
            
            for selector in consent_selectors:
                try:
                    consent_button = self.page.locator(selector).first
                    if await consent_button.is_visible():
                        await consent_button.click()
                        logger.info("✅ Clicked Google consent button")
                        await self.page.wait_for_timeout(2000)
                        return
                except Exception:
                    continue
                    
        except Exception as e:
            logger.debug(f"No consent popup found or error handling it: {e}")
    
    async def extract_linkedin_urls_from_page(self) -> Set[str]:
        """Extract LinkedIn profile URLs from the current Google search results page."""
        try:
            # Wait for search results to load
            await self.page.wait_for_selector('div[data-sokoban-container]', timeout=10000)
        except Exception:
            logger.warning("Could not find search results container")
        
        # Get page content
        content = await self.page.content()
        
        # Use BeautifulSoup for reliable HTML parsing
        soup = BeautifulSoup(content, 'html.parser')
        
        # Extract all links that point to LinkedIn profiles
        linkedin_urls = set()
        
        # Find all anchor tags with href containing linkedin.com/in
        links = soup.find_all('a', href=lambda href: href and 'linkedin.com/in' in href)
        
        for link in links:
            url = link.get('href', '')
            
            # Clean and validate the URL
            if self._is_valid_linkedin_profile_url(url):
                clean_url = clean_linkedin_url(url)
                linkedin_urls.add(clean_url)
        
        # Also use JavaScript evaluation as backup
        try:
            js_urls = await self.page.evaluate("""
                () => {
                    const links = Array.from(document.querySelectorAll('a[href*="linkedin.com/in"]'));
                    return links
                        .map(link => link.href)
                        .filter(href => href.includes('linkedin.com/in/'))
                        .map(href => href.split('?')[0].split('#')[0]);
                }
            """)
            
            for url in js_urls:
                if self._is_valid_linkedin_profile_url(url):
                    clean_url = clean_linkedin_url(url)
                    linkedin_urls.add(clean_url)
                    
        except Exception as e:
            logger.warning(f"JavaScript URL extraction failed: {e}")
        
        logger.info(f"📊 Extracted {len(linkedin_urls)} LinkedIn URLs from page")
        return linkedin_urls
    
    def _is_valid_linkedin_profile_url(self, url: str) -> bool:
        """Check if URL is a valid LinkedIn profile URL."""
        if not url or not isinstance(url, str):
            return False
            
        # Remove URL prefixes from Google redirects
        if url.startswith('/url?'):
            # Extract the actual URL from Google redirect
            import urllib.parse
            parsed = urllib.parse.parse_qs(url[5:])  # Remove '/url?'
            if 'q' in parsed:
                url = parsed['q'][0]
        
        return validate_linkedin_url(url)
    
    async def search_with_retry(self, search_terms: List[str], max_results: int = 50) -> SearchResult:
        """
        Search for LinkedIn profiles with retry logic.
        """
        search_query = self.construct_search_query(search_terms)
        all_urls = set()
        start_index = 0
        
        logger.info(f"🚀 Starting LinkedIn profile search")
        logger.info(f"🔍 Search terms: {search_terms}")
        logger.info(f"📊 Target: {max_results} profiles")
        
        while len(all_urls) < max_results:
            retry_count = 0
            page_urls = set()
            
            while retry_count < MAX_RETRIES:
                try:
                    search_url = self.construct_search_url(search_query, start_index)
                    logger.info(f"📱 Loading search page {start_index // 50 + 1}: {search_url}")
                    
                    # Navigate to search URL
                    await self.page.goto(search_url, wait_until="domcontentloaded")
                    
                    # Handle consent popup
                    await self.handle_google_consent()
                    
                    # Wait for results to load
                    await self.page.wait_for_timeout(3000)
                    
                    # Extract URLs from this page
                    page_urls = await self.extract_linkedin_urls_from_page()
                    
                    if page_urls:
                        break  # Success, exit retry loop
                    
                except Exception as e:
                        logger.error(f"❌ Search attempt {retry_count + 1} failed: {e}")
                        retry_count += 1
                        
                        if retry_count < MAX_RETRIES:
                            logger.info(f"⏳ Retrying in {RETRY_DELAY} seconds...")
                            await asyncio.sleep(RETRY_DELAY)
            
            if not page_urls and retry_count >= MAX_RETRIES:
                logger.warning(f"⚠️ Failed to get results after {MAX_RETRIES} retries")
                break
            
            # Add new URLs to our collection
            new_urls = page_urls - all_urls
            all_urls.update(new_urls)
            
            logger.info(f"✅ Found {len(new_urls)} new URLs, total: {len(all_urls)}")
            
            # Check if we got any new results (if not, we've probably reached the end)
            if not new_urls:
                logger.info("🏁 No new results found, ending search")
                break
            
            # Check if we have enough results
            if len(all_urls) >= max_results:
                logger.info(f"🎯 Reached target of {max_results} profiles")
                break
            
            # Move to next page
            start_index += 50
            
            # Add delay between requests
            logger.info(f"⏳ Waiting {REQUEST_DELAY} seconds before next page...")
            await asyncio.sleep(REQUEST_DELAY)
        
        # Create result object
        result = SearchResult(
            search_query=search_query,
            search_terms=search_terms,
            total_results=len(all_urls),
            profiles=list(all_urls)[:max_results],  # Limit to max_results
            searched_at=datetime.now()
        )
        
        logger.info(f"🎉 Search completed: {result.total_results} profiles found")
        return result
    
    async def search_linkedin_profiles(self, search_terms: List[str], max_results: int = 50) -> SearchResult:
        """
        Main method to search for LinkedIn profiles.
        
        Args:
            search_terms: List of search terms (will be quoted)
            max_results: Maximum number of profiles to return
            
        Returns:
            SearchResult object with found LinkedIn profile URLs
        """
        if not search_terms:
            raise ValueError("Search terms cannot be empty")
        
        if not self.page:
            raise GoogleSearchError("Browser not initialized. Use async context manager.")
        
        try:
            result = await self.search_with_retry(search_terms, max_results)
            return result
            
        except Exception as e:
            logger.error(f"❌ Search failed: {e}")
            raise GoogleSearchError(f"Failed to search LinkedIn profiles: {e}")


# Standalone function for easier usage
async def search_linkedin_profiles(search_terms: List[str], max_results: int = 50) -> SearchResult:
    """
    Standalone function to search for LinkedIn profiles.
    
    Example usage:
        result = await search_linkedin_profiles(["backend engineer", "fintech", "San Francisco"])
    """
    async with LinkedInSearcher() as searcher:
        return await searcher.search_linkedin_profiles(search_terms, max_results) 