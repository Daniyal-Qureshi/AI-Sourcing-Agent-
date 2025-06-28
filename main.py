"""
LinkedIn Profile Extractor - Main Application
Combines Google search functionality with LinkedIn profile extraction using OpenAI
"""
import asyncio
import json
import logging
import os
import time
from typing import List, Optional
from datetime import datetime

from config.settings import (
    validate_config,
    DEFAULT_SEARCH_QUERY,
    MAX_PROFILES,
    LOG_LEVEL,
    LOG_FORMAT
)
from models.linkedin_profile import (
    LinkedInProfile,
    SearchResult,
    BatchExtractionResult
)
from utils.google_search import search_linkedin_profiles
from utils.profile_extractor import (
    LinkedInProfileExtractor,
    extract_single_profile,
    extract_multiple_profiles
)

# Setup logging
logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)


class LinkedInSourcer:
    """
    Main LinkedIn sourcing class that combines search and extraction.
    """
    
    def __init__(self):
        self.search_results: Optional[SearchResult] = None
        self.extraction_results: Optional[BatchExtractionResult] = None
        
    async def search_profiles(self, search_terms: List[str], max_results: int = MAX_PROFILES) -> SearchResult:
        """Search for LinkedIn profiles using Google."""
        logger.info("🔍 Starting LinkedIn profile search...")
        logger.info(f"Search terms: {search_terms}")
        logger.info(f"Max results: {max_results}")
        
        self.search_results = await search_linkedin_profiles(search_terms, max_results)
        
        logger.info(f"✅ Search completed: {self.search_results.total_results} profiles found")
        
        # Save search results
        search_filename = f"search_results_{int(time.time())}.json"
        with open(search_filename, 'w') as f:
            json.dump(self.search_results.dict(), f, indent=2, default=str)
        logger.info(f"💾 Search results saved to: {search_filename}")
        
        return self.search_results
    
    async def extract_profiles(self, profile_urls: List[str], use_login: bool = True) -> BatchExtractionResult:
        """Extract detailed data from LinkedIn profiles."""
        logger.info(f"📊 Starting profile extraction for {len(profile_urls)} profiles...")
        
        self.extraction_results = await extract_multiple_profiles(profile_urls, use_login)
        
        success_rate = (self.extraction_results.successful_extractions / 
                       self.extraction_results.total_profiles * 100)
        
        logger.info(f"✅ Extraction completed: {self.extraction_results.successful_extractions}/{self.extraction_results.total_profiles} profiles ({success_rate:.1f}% success)")
        
        return self.extraction_results
    
    async def search_and_extract(self, 
                                search_terms: List[str], 
                                max_search_results: int = MAX_PROFILES,
                                max_extractions: int = None,
                                use_login: bool = True) -> tuple[SearchResult, BatchExtractionResult]:
        """
        Complete workflow: Search for profiles, then extract detailed data.
        
        Args:
            search_terms: List of search terms for Google search
            max_search_results: Maximum number of profiles to find in search
            max_extractions: Maximum number of profiles to extract (if None, extracts all found)
            use_login: Whether to use LinkedIn login for authenticated access
            
        Returns:
            Tuple of (search_results, extraction_results)
        """
        start_time = time.time()
        logger.info("🚀 Starting complete LinkedIn sourcing workflow...")
        
        # Step 1: Search for profiles
        search_results = await self.search_profiles(search_terms, max_search_results)
        
        if not search_results.profiles:
            logger.warning("⚠️ No profiles found in search, cannot proceed with extraction")
            return search_results, None
        
        # Step 2: Extract profile data
        profiles_to_extract = search_results.profiles
        if max_extractions and max_extractions < len(profiles_to_extract):
            profiles_to_extract = profiles_to_extract[:max_extractions]
            logger.info(f"📊 Limiting extraction to first {max_extractions} profiles")
        
        extraction_results = await self.extract_profiles(profiles_to_extract, use_login)
        
        # Summary
        total_time = time.time() - start_time
        logger.info("\n" + "="*50)
        logger.info("📊 LINKEDIN SOURCING COMPLETE")
        logger.info("="*50)
        logger.info(f"🔍 Search Results: {search_results.total_results} profiles found")
        logger.info(f"📊 Extraction Results: {extraction_results.successful_extractions}/{extraction_results.total_profiles} profiles extracted")
        logger.info(f"⏱️  Total Time: {total_time:.1f} seconds")
        
        if extraction_results.errors:
            logger.info(f"❌ Errors: {len(extraction_results.errors)}")
            for error in extraction_results.errors[:3]:  # Show first 3 errors
                logger.info(f"   - {error}")
            if len(extraction_results.errors) > 3:
                logger.info(f"   ... and {len(extraction_results.errors) - 3} more")
        
        return search_results, extraction_results
    
    def get_summary(self) -> dict:
        """Get a summary of the current session."""
        summary = {
            "session_timestamp": datetime.now().isoformat(),
            "search_completed": self.search_results is not None,
            "extraction_completed": self.extraction_results is not None
        }
        
        if self.search_results:
            summary["search_summary"] = {
                "search_query": self.search_results.search_query,
                "search_terms": self.search_results.search_terms,
                "total_profiles_found": self.search_results.total_results,
                "searched_at": self.search_results.searched_at.isoformat()
            }
        
        if self.extraction_results:
            summary["extraction_summary"] = {
                "total_profiles": self.extraction_results.total_profiles,
                "successful_extractions": self.extraction_results.successful_extractions,
                "failed_extractions": self.extraction_results.failed_extractions,
                "success_rate": f"{(self.extraction_results.successful_extractions / self.extraction_results.total_profiles * 100):.1f}%",
                "total_time": f"{self.extraction_results.total_time:.1f}s",
                "extracted_profiles": [
                    {
                        "name": profile.name,
                        "headline": profile.headline,
                        "location": profile.location,
                        "linkedin_url": profile.linkedin_url,
                        "experience_count": len(profile.experience) if profile.experience else 0,
                        "education_count": len(profile.education) if profile.education else 0,
                        "skills_count": len(profile.skills) if profile.skills else 0
                    }
                    for profile in self.extraction_results.profiles
                ]
            }
        
        return summary


async def search_only_mode(search_terms: List[str], max_results: int = MAX_PROFILES) -> SearchResult:
    """
    Safe mode: Only search for LinkedIn profile URLs without accessing LinkedIn directly.
    """
    logger.info("🛡️  SAFE MODE: Only extracting LinkedIn URLs from Google search")
    logger.info("   This mode does NOT access LinkedIn directly - your account is safe!")
    
    sourcer = LinkedInSourcer()
    return await sourcer.search_profiles(search_terms, max_results)


async def extract_only_mode(profile_urls: List[str], use_login: bool = True) -> BatchExtractionResult:
    """
    Extract profiles from a provided list of URLs.
    """
    logger.info("📊 EXTRACTION MODE: Processing provided LinkedIn URLs")
    
    sourcer = LinkedInSourcer()
    return await sourcer.extract_profiles(profile_urls, use_login)


async def full_workflow_mode(search_terms: List[str], 
                           max_search_results: int = MAX_PROFILES,
                           max_extractions: int = None,
                           use_login: bool = True) -> tuple[SearchResult, BatchExtractionResult]:
    """
    Complete workflow: Search + Extract profiles.
    """
    logger.info("🚀 FULL WORKFLOW MODE: Search + Extract LinkedIn profiles")
    
    sourcer = LinkedInSourcer()
    return await sourcer.search_and_extract(
        search_terms, 
        max_search_results, 
        max_extractions, 
        use_login
    )


def parse_search_query(query_string: str) -> List[str]:
    """Parse a search query string into individual terms."""
    # Handle quoted terms and individual words
    import re
    
    # Find quoted terms
    quoted_terms = re.findall(r'"([^"]*)"', query_string)
    
    # Remove quoted terms from string and split remaining words
    remaining = re.sub(r'"[^"]*"', '', query_string)
    individual_words = [word.strip() for word in remaining.split() if word.strip()]
    
    # Combine quoted terms and individual words
    all_terms = quoted_terms + individual_words
    
    # Filter out common words and site restrictions
    filtered_terms = [
        term for term in all_terms 
        if term and not term.startswith('site:') and term.lower() not in ['and', 'or', 'the', 'a', 'an']
    ]
    
    return filtered_terms


async def interactive_mode():
    """Interactive mode for user input."""
    print("\n" + "="*60)
    print("🔍 LINKEDIN PROFILE SOURCER - Interactive Mode")
    print("="*60)
    
    try:
        validate_config()
    except ValueError as e:
        print(f"❌ Configuration Error: {e}")
        print("\n💡 Please check your .env file and ensure all required variables are set.")
        return
    
    print("\nChoose your mode:")
    print("1. 🛡️  Search Only (Safe - No LinkedIn login required)")
    print("2. 📊 Extract Only (Provide URLs)")
    print("3. 🚀 Full Workflow (Search + Extract)")
    print("4. ❌ Exit")
    
    while True:
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            # Search only mode
            search_input = input(f"\nEnter search terms (default: {DEFAULT_SEARCH_QUERY}): ").strip()
            if not search_input:
                search_input = DEFAULT_SEARCH_QUERY
            
            search_terms = parse_search_query(search_input)
            max_results = int(input(f"Max results (default: {MAX_PROFILES}): ") or MAX_PROFILES)
            
            print(f"\n🔍 Searching for: {search_terms}")
            print(f"📊 Max results: {max_results}")
            
            result = await search_only_mode(search_terms, max_results)
            
            print(f"\n✅ Found {result.total_results} LinkedIn profiles:")
            for i, url in enumerate(result.profiles[:10], 1):  # Show first 10
                print(f"  {i}. {url}")
            if len(result.profiles) > 10:
                print(f"  ... and {len(result.profiles) - 10} more")
            
            break
            
        elif choice == "2":
            # Extract only mode
            print("\nEnter LinkedIn profile URLs (one per line, empty line to finish):")
            urls = []
            while True:
                url = input().strip()
                if not url:
                    break
                if "linkedin.com/in/" in url:
                    urls.append(url)
                else:
                    print("⚠️  Invalid LinkedIn URL, skipping...")
            
            if not urls:
                print("❌ No valid URLs provided")
                continue
            
            use_login = input("Use LinkedIn login for authenticated access? (y/N): ").strip().lower() == 'y'
            
            print(f"\n📊 Extracting {len(urls)} profiles...")
            result = await extract_only_mode(urls, use_login)
            
            print(f"\n✅ Extraction completed:")
            print(f"   Success: {result.successful_extractions}/{result.total_profiles}")
            print(f"   Time: {result.total_time:.1f}s")
            
            break
            
        elif choice == "3":
            # Full workflow mode
            search_input = input(f"\nEnter search terms (default: {DEFAULT_SEARCH_QUERY}): ").strip()
            if not search_input:
                search_input = DEFAULT_SEARCH_QUERY
            
            search_terms = parse_search_query(search_input)
            max_search = int(input(f"Max search results (default: {MAX_PROFILES}): ") or MAX_PROFILES)
            max_extract = input(f"Max extractions (default: all found): ").strip()
            max_extract = int(max_extract) if max_extract else None
            
            use_login = input("Use LinkedIn login for authenticated access? (y/N): ").strip().lower() == 'y'
            
            print(f"\n🚀 Starting full workflow:")
            print(f"   Search terms: {search_terms}")
            print(f"   Max search results: {max_search}")
            print(f"   Max extractions: {max_extract or 'all'}")
            print(f"   Use login: {use_login}")
            
            search_result, extract_result = await full_workflow_mode(
                search_terms, max_search, max_extract, use_login
            )
            
            # Show summary
            sourcer = LinkedInSourcer()
            sourcer.search_results = search_result
            sourcer.extraction_results = extract_result
            summary = sourcer.get_summary()
            
            print(f"\n📋 Session Summary:")
            print(json.dumps(summary, indent=2, default=str))
            
            break
            
        elif choice == "4":
            print("👋 Goodbye!")
            break
            
        else:
            print("❌ Invalid choice, please try again.")


async def main():
    """Main entry point."""
    import sys
    
    if len(sys.argv) > 1:
        # Command line mode
        if sys.argv[1] == "search":
            # python main.py search "backend engineer" "fintech" "San Francisco"
            search_terms = sys.argv[2:] if len(sys.argv) > 2 else parse_search_query(DEFAULT_SEARCH_QUERY)
            result = await search_only_mode(search_terms)
            
            print(f"Found {result.total_results} profiles:")
            for url in result.profiles:
                print(url)
                
        elif sys.argv[1] == "extract":
            # python main.py extract https://linkedin.com/in/profile1 https://linkedin.com/in/profile2
            urls = sys.argv[2:]
            if not urls:
                print("❌ No URLs provided")
                return
            
            result = await extract_only_mode(urls)
            print(f"Extracted {result.successful_extractions}/{result.total_profiles} profiles")
            
        elif sys.argv[1] == "workflow":
            # python main.py workflow "backend engineer" "fintech" "San Francisco"
            search_terms = sys.argv[2:] if len(sys.argv) > 2 else parse_search_query(DEFAULT_SEARCH_QUERY)
            search_result, extract_result = await full_workflow_mode(search_terms)
            
            print(f"Search: {search_result.total_results} profiles found")
            print(f"Extract: {extract_result.successful_extractions}/{extract_result.total_profiles} profiles extracted")
            
        else:
            print("❌ Unknown command. Use: search, extract, or workflow")
    else:
        # Interactive mode
        await interactive_mode()


if __name__ == "__main__":
    asyncio.run(main()) 