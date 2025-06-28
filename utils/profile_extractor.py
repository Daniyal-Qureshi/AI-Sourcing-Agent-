"""
LinkedIn Profile Extractor using OpenAI
Combines Playwright automation with OpenAI for intelligent data extraction
Based on the logic from the TypeScript playwright script
"""
import asyncio
import json
import logging
import os
import re
import time
from typing import List, Optional, Dict, Any
from datetime import datetime

from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from openai import OpenAI
from bs4 import BeautifulSoup

from models.linkedin_profile import (
    LinkedInProfile, 
    ExperienceEntry, 
    EducationEntry, 
    ExtractionResult,
    BatchExtractionResult,
    SessionData
)
from config.settings import (
    get_browser_config, 
    get_openai_config,
    LINKEDIN_EMAIL,
    LINKEDIN_PASSWORD,
    HTML_DIR,
    JSON_DIR,
    SESSIONS_DIR,
    REQUEST_DELAY,
    MAX_RETRIES,
    RETRY_DELAY
)

logger = logging.getLogger(__name__)


class ProfileExtractionError(Exception):
    """Custom exception for profile extraction errors."""
    pass


class LinkedInProfileExtractor:
    """
    LinkedIn profile extractor using Playwright + OpenAI.
    Replicates the functionality from the TypeScript playwright script.
    """
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.browser_config = get_browser_config()
        self.openai_config = get_openai_config()
        
        # Initialize OpenAI client with error handling
        try:
            # Simple initialization with just the API key
            self.openai_client = OpenAI(api_key=self.openai_config["api_key"])
            logger.info("✅ OpenAI client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            raise ProfileExtractionError(f"OpenAI initialization failed: {e}")
        
        self.session_file = os.path.join(SESSIONS_DIR, "linkedin_session.json")
        
        # Ensure output directories exist
        os.makedirs(HTML_DIR, exist_ok=True)
        os.makedirs(JSON_DIR, exist_ok=True)
        os.makedirs(SESSIONS_DIR, exist_ok=True)
        
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
        
        # Try to load existing session
        session_data = await self.load_linkedin_session()
        
        if session_data:
            logger.info("🔄 Using saved LinkedIn session...")
            self.context = await self.browser.new_context(
                user_agent=session_data.user_agent,
                viewport=self.browser_config["viewport"]
            )
            # Add saved cookies
            await self.context.add_cookies(session_data.cookies)
        else:
            logger.info("🆕 Creating new browser context...")
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
    
    async def login_to_linkedin(self) -> bool:
        """
        Login to LinkedIn using credentials.
        Replicates the loginToLinkedIn function from TypeScript.
        """
        if not LINKEDIN_EMAIL or not LINKEDIN_PASSWORD:
            logger.error("❌ LinkedIn credentials not provided")
            return False
            
        logger.info("🔐 Starting LinkedIn login process...")
        
        try:
            logger.info("📱 Loading LinkedIn login page...")
            await self.page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded")
            
            # Wait for login form
            await self.page.wait_for_selector("#username", timeout=10000)
            
            # Fill login credentials
            logger.info("📝 Filling login credentials...")
            await self.page.fill("#username", LINKEDIN_EMAIL)
            await self.page.fill("#password", LINKEDIN_PASSWORD)
            
            # Submit login form
            logger.info("🚀 Submitting login form...")
            await self.page.click('button[type="submit"]')
            
            # Wait for login to complete
            logger.info("⏳ Waiting for login completion...")
            try:
                # Wait for either the feed page or any LinkedIn authenticated page
                await self.page.wait_for_url("**/feed/**", timeout=15000)
                logger.info("✅ Login successful - redirected to feed")
            except:
                # Check if we're on any LinkedIn authenticated page
                await self.page.wait_for_timeout(5000)
                current_url = self.page.url
                if "linkedin.com" in current_url and "/login" not in current_url:
                    logger.info("✅ Login successful - on LinkedIn authenticated page")
                else:
                    raise Exception("Login failed - still on login page")
            
            # Save session cookies
            logger.info("💾 Saving session cookies...")
            cookies = await self.context.cookies()
            user_agent = self.browser_config["user_agent"]
            session_data = SessionData(
                cookies=cookies,
                timestamp=int(time.time()),
                user_agent=user_agent,
                is_valid=True
            )
            
            with open(self.session_file, 'w') as f:
                json.dump(session_data.dict(), f, indent=2)
            
            logger.info(f"💾 Session saved to: {self.session_file}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Login failed: {e}")
            return False
    
    async def load_linkedin_session(self) -> Optional[SessionData]:
        """Load existing LinkedIn session from file."""
        try:
            if not os.path.exists(self.session_file):
                logger.info("⚠️ No saved LinkedIn session found")
                return None
            
            with open(self.session_file, 'r') as f:
                session_dict = json.load(f)
            
            session_data = SessionData(**session_dict)
            
            # Check if session is not too old (24 hours)
            session_age = time.time() - session_data.timestamp
            max_age = 24 * 60 * 60  # 24 hours
            
            if session_age > max_age:
                logger.info("⚠️ Saved session is too old, will need to re-login")
                return None
            
            logger.info("✅ Loaded saved LinkedIn session")
            return session_data
            
        except Exception as e:
            logger.error(f"❌ Error loading session: {e}")
            return None
    
    def clean_html(self, html_content: str) -> str:
        """
        Clean HTML to keep only important sections for AI processing.
        Replicates the cleanHTML function from TypeScript.
        """
        logger.info("🧹 Cleaning HTML content...")
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Target div IDs to find and preserve their parent sections
        target_div_ids = ['experience', 'education', 'projects', 'skills', 'about']
        sections_to_keep = []
        
        # Try to find main tag first
        main_element = soup.find('main')
        if main_element:
            logger.info("✅ Found main tag, extracting specific sections only")
            
            # Get the first section inside main
            first_section = main_element.find('section')
            if first_section:
                sections_to_keep.append(first_section)
                logger.info("✅ Added first section inside main")
            
            # Find divs with target IDs and get their parent sections
            for div_id in target_div_ids:
                target_div = soup.find('div', id=div_id)
                if target_div:
                    # Find the closest parent section
                    parent_section = target_div.find_parent('section')
                    if parent_section and parent_section not in sections_to_keep:
                        sections_to_keep.append(parent_section)
                        logger.info(f"✅ Added section for div with ID: {div_id}")
            
            # Create new main element with only the sections we want to keep
            if sections_to_keep:
                new_main = soup.new_tag('main')
                # Copy main element's attributes
                for attr_name, attr_value in main_element.attrs.items():
                    new_main[attr_name] = attr_value
                
                # Add all sections we want to keep
                for section in sections_to_keep:
                    new_main.append(section.extract())
                
                cleaned_html = str(new_main)
                logger.info(f"✅ Created cleaned HTML with {len(sections_to_keep)} sections")
            else:
                logger.info("⚠️ No target sections found, using original main content")
                cleaned_html = str(main_element)
        else:
            logger.info("⚠️ No main tag found, using original content")
            cleaned_html = html_content
        
        # Optimize HTML for AI processing
        logger.info("🤖 Optimizing HTML for AI processing...")
        
        # Remove HTML comments
        cleaned_html = re.sub(r'<!--[\s\S]*?-->', '', cleaned_html)
        
        # Remove excessive whitespace between tags
        cleaned_html = re.sub(r'>\s+<', '><', cleaned_html)
        
        # Remove multiple spaces, tabs, and newlines
        cleaned_html = re.sub(r'\s+', ' ', cleaned_html)
        
        # Remove leading and trailing whitespace
        cleaned_html = cleaned_html.strip()
        
        # Remove empty attributes
        cleaned_html = re.sub(r'\s+[a-zA-Z-]+=""\s*', ' ', cleaned_html)
        
        # Remove extra spaces around attributes
        cleaned_html = re.sub(r'\s+=', '=', cleaned_html)
        cleaned_html = re.sub(r'=\s+', '=', cleaned_html)
        
        # Remove spaces before closing tags
        cleaned_html = re.sub(r'\s+>', '>', cleaned_html)
        
        # Final cleanup of any remaining double spaces
        cleaned_html = re.sub(r'\s{2,}', ' ', cleaned_html)
        
        logger.info("✨ HTML optimized for AI processing with target sections only")
        return cleaned_html
    
    def determine_section_type(self, section_html: str) -> str:
        """Determine the type of LinkedIn section based on content."""
        html_lower = section_html.lower()
        
        if 'id="experience"' in html_lower or ('experience' in html_lower and ('company' in html_lower or 'title' in html_lower)):
            return 'experience'
        if 'id="education"' in html_lower or ('education' in html_lower and ('school' in html_lower or 'degree' in html_lower)):
            return 'education'
        if 'id="skills"' in html_lower or 'skills' in html_lower:
            return 'skills'
        if 'id="about"' in html_lower or 'about' in html_lower:
            return 'about'
        if 'id="projects"' in html_lower or 'projects' in html_lower:
            return 'projects'
        if 'profile-picture' in html_lower or 'pv-top-card' in html_lower or 'text-heading-xlarge' in html_lower:
            return 'profile_header'
        
        return 'unknown'
    
    def get_section_extraction_prompt(self, section_type: str, section_html: str) -> str:
        """Get appropriate prompt for OpenAI based on section type."""
        base_prompt = f"Extract data from this LinkedIn profile HTML section. Return only valid JSON without any markdown formatting or explanations.\n\nHTML:\n{section_html}\n\n"
        
        prompts = {
            'profile_header': base_prompt + """Extract profile header data in this JSON format:
{
  "name": "Full Name",
  "headline": "Job Title/Headline",
  "location": "City, State, Country",
  "connections": "X connections",
  "profileImage": "image_url_if_available"
}""",
            
            'about': base_prompt + """Extract the about/summary section in this JSON format:
{
  "summary": "Full about text/summary"
}""",
            
            'experience': base_prompt + """Extract all work experience entries in this JSON format:
{
  "experience": [
    {
      "title": "Job Title",
      "company": "Company Name",
      "date_range": "Start Date - End Date",
      "duration": "X yrs Y mos",
      "description": "Job description if available"
    }
  ]
}""",
            
            'education': base_prompt + """Extract all education entries in this JSON format:
{
  "education": [
    {
      "school": "School Name",
      "degree": "Degree Type",
      "field_of_study": "Field of Study",
      "date_range": "Start Date - End Date"
    }
  ]
}""",
            
            'skills': base_prompt + """Extract all skills in this JSON format:
{
  "skills": ["skill1", "skill2", "skill3"]
}"""
        }
        
        return prompts.get(section_type, base_prompt + "Extract any relevant profile information from this section and return it as JSON.")
    
    async def merge_extracted_data(self, profile: LinkedInProfile, json_result: str, section_type: str) -> None:
        """Merge extracted data into the profile object."""
        try:
            # Clean the JSON result - remove any markdown formatting
            clean_json = json_result.replace('```json\n', '').replace('```\n', '').replace('```', '').strip()
            
            extracted = json.loads(clean_json)
            
            # Merge based on section type
            if section_type == 'profile_header':
                if extracted.get('name'):
                    profile.name = extracted['name']
                if extracted.get('headline'):
                    profile.headline = extracted['headline']
                if extracted.get('location'):
                    profile.location = extracted['location']
                if extracted.get('connections'):
                    profile.connections = extracted['connections']
                if extracted.get('profileImage'):
                    profile.profile_image = extracted['profileImage']
                    
            elif section_type == 'about':
                if extracted.get('summary'):
                    profile.summary = extracted['summary']
                    
            elif section_type == 'experience':
                if extracted.get('experience') and isinstance(extracted['experience'], list):
                    if not profile.experience:
                        profile.experience = []
                    for exp in extracted['experience']:
                        experience_entry = ExperienceEntry(
                            title=exp.get('title', ''),
                            company=exp.get('company', ''),
                            duration=exp.get('duration') or exp.get('date_range', ''),
                            location=exp.get('location', ''),
                            description=exp.get('description', '')
                        )
                        profile.experience.append(experience_entry)
                        
            elif section_type == 'education':
                if extracted.get('education') and isinstance(extracted['education'], list):
                    if not profile.education:
                        profile.education = []
                    for edu in extracted['education']:
                        education_entry = EducationEntry(
                            school=edu.get('school', ''),
                            degree=edu.get('degree', ''),
                            field_of_study=edu.get('field_of_study') or edu.get('field', ''),
                            date_range=edu.get('date_range') or edu.get('duration', '')
                        )
                        profile.education.append(education_entry)
                        
            elif section_type == 'skills':
                if extracted.get('skills') and isinstance(extracted['skills'], list):
                    if not profile.skills:
                        profile.skills = []
                    profile.skills.extend(extracted['skills'])
                    
        except json.JSONDecodeError as e:
            logger.error(f"❌ Error parsing JSON result for {section_type}: {e}")
            logger.error(f"Raw result: {json_result}")
        except Exception as e:
            logger.error(f"❌ Error merging data for {section_type}: {e}")
    
    async def extract_profile_data_from_html(self, html_content: str, profile_url: str) -> LinkedInProfile:
        """
        Extract profile data from HTML using OpenAI.
        Replicates the extractProfileDataFromHTML function from TypeScript.
        """
        logger.info("🤖 Extracting profile data using OpenAI...")
        
        # Parse HTML content
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Initialize profile object
        profile = LinkedInProfile(
            name='',
            linkedin_url=profile_url,
            extracted_at=datetime.now(),
            extraction_method="OpenAI + Playwright"
        )
        
        # Get all sections from HTML
        sections = soup.find_all('section')
        logger.info(f"🔍 Found {len(sections)} sections to process")
        
        # Process each section with OpenAI
        for i, section in enumerate(sections):
            section_html = str(section)
            
            # Skip if section is too small
            if len(section_html) < 100:
                logger.info(f"⏩ Skipping small section {i + 1}")
                continue
            
            logger.info(f"🔄 Processing section {i + 1}/{len(sections)}...")
            
            try:
                # Determine section type
                section_type = self.determine_section_type(section_html)
                logger.info(f"📋 Section type: {section_type}")
                
                # Get appropriate prompt
                prompt = self.get_section_extraction_prompt(section_type, section_html)
                
                # Call OpenAI to extract data
                try:
                    response = self.openai_client.chat.completions.create(
                        model=self.openai_config["model"],
                        messages=[
                            {
                                "role": "system",
                                "content": "You are a LinkedIn profile data extraction expert. Extract structured data from HTML sections and return valid JSON only. No explanations or additional text."
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        temperature=self.openai_config["temperature"],
                        max_tokens=self.openai_config["max_tokens"]
                    )
                except Exception as e:
                    logger.error(f"OpenAI API call failed: {e}")
                    continue
                
                result = response.choices[0].message.content.strip()
                if result:
                    # Parse and merge the result
                    await self.merge_extracted_data(profile, result, section_type)
                    logger.info(f"✅ Processed {section_type} section")
                
                # Add delay to avoid rate limits
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"❌ Error processing section {i + 1}: {e}")
        
        logger.info(f"🎉 Profile extraction completed for: {profile.name or 'Unknown'}")
        return profile
    
    async def scrape_linkedin_profile(self, profile_url: str, use_login: bool = True) -> ExtractionResult:
        """
        Scrape a single LinkedIn profile.
        Replicates the scrapeLinkedInProfile function from TypeScript.
        """
        start_time = time.time()
        logger.info(f"🚀 Starting LinkedIn profile extraction for: {profile_url}")
        
        try:
            # Check if we need to login
            if use_login:
                # Check if we have a valid session or need to login
                current_url = self.page.url if self.page else ""
                if not current_url or "linkedin.com" not in current_url:
                    # Try to access a LinkedIn page to test session
                    await self.page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded")
                    await self.page.wait_for_timeout(3000)
                    
                    if "/login" in self.page.url or "/authwall" in self.page.url:
                        logger.info("⚠️ Session expired or invalid, need to login")
                        login_success = await self.login_to_linkedin()
                        if not login_success:
                            raise ProfileExtractionError("Login failed")
            
            # Navigate to profile URL
            logger.info("📱 Loading LinkedIn profile...")
            await self.page.goto(profile_url, wait_until="domcontentloaded")
            
            # Check if we're redirected to login
            await self.page.wait_for_timeout(3000)
            current_url = self.page.url
            
            if "/login" in current_url or "/authwall" in current_url:
                if use_login:
                    logger.info("⚠️ Session expired, attempting login...")
                    login_success = await self.login_to_linkedin()
                    if not login_success:
                        raise ProfileExtractionError("Login failed after redirect")
                    # Retry profile access
                    await self.page.goto(profile_url, wait_until="domcontentloaded")
                else:
                    raise ProfileExtractionError("Profile requires authentication")
            
            logger.info("✅ Successfully accessed LinkedIn profile")
            
            # Scroll through page to load all content
            logger.info("📜 Scrolling to load all profile content...")
            await self.page.evaluate("""
                async () => {
                    await new Promise((resolve) => {
                        let totalHeight = 0;
                        const distance = 100;
                        const timer = setInterval(() => {
                            const scrollHeight = document.body.scrollHeight;
                            window.scrollBy(0, distance);
                            totalHeight += distance;

                            if(totalHeight >= scrollHeight){
                                clearInterval(timer);
                                resolve();
                            }
                        }, 100);
                    });
                }
            """)
            
            # Wait for dynamic content to load
            await self.page.wait_for_timeout(2000)
            
            # Get profile ID for file naming
            profile_id = profile_url.split('/')[-1].replace('/', '') or 'unknown'
            profile_id = re.sub(r'[^a-zA-Z0-9_-]', '_', profile_id)
            
            # Get page content
            content = await self.page.content()
            
            # Save original HTML
            html_filename = os.path.join(HTML_DIR, f"{profile_id}_original.html")
            with open(html_filename, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"💾 Saved original HTML to: {html_filename}")
            
            # Clean and save cleaned HTML
            cleaned_html = self.clean_html(content)
            cleaned_filename = os.path.join(HTML_DIR, f"{profile_id}_cleaned.html")
            with open(cleaned_filename, 'w', encoding='utf-8') as f:
                f.write(cleaned_html)
            
            logger.info(f"💾 Saved cleaned HTML to: {cleaned_filename}")
            reduction = round((1 - len(cleaned_html)/len(content)) * 100)
            logger.info(f"📏 HTML size reduced from {len(content)} to {len(cleaned_html)} characters ({reduction}% reduction)")
            
            # Extract structured profile data from cleaned HTML
            logger.info("📊 Extracting data from cleaned HTML...")
            profile_data = await self.extract_profile_data_from_html(cleaned_html, profile_url)
            
            # Save JSON
            json_filename = os.path.join(JSON_DIR, f"{profile_id}.json")
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(profile_data.dict(), f, indent=2, default=str)
            logger.info(f"💾 Saved JSON to: {json_filename}")
            
            extraction_time = time.time() - start_time
            
            return ExtractionResult(
                success=True,
                profile=profile_data,
                extraction_time=extraction_time
            )
            
        except Exception as e:
            extraction_time = time.time() - start_time
            error_msg = f"Profile extraction failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            
            return ExtractionResult(
                success=False,
                error=error_msg,
                extraction_time=extraction_time
            )
    
    async def batch_extract_profiles(self, profile_urls: List[str], use_login: bool = True) -> BatchExtractionResult:
        """Extract multiple LinkedIn profiles in batch."""
        start_time = time.time()
        logger.info(f"🚀 Starting batch extraction of {len(profile_urls)} profiles")
        
        results = []
        errors = []
        
        for i, url in enumerate(profile_urls):
            logger.info(f"\n📍 Processing profile {i + 1}/{len(profile_urls)}: {url}")
            
            try:
                result = await self.scrape_linkedin_profile(url, use_login)
                if result.success:
                    results.append(result.profile)
                    logger.info(f"✅ Successfully extracted: {result.profile.name}")
                else:
                    errors.append(f"{url}: {result.error}")
                    logger.error(f"❌ Failed to extract profile: {result.error}")
                
                # Add delay between requests
                if i < len(profile_urls) - 1:
                    logger.info(f"⏳ Waiting {REQUEST_DELAY} seconds before next profile...")
                    await asyncio.sleep(REQUEST_DELAY)
                    
            except Exception as e:
                error_msg = f"{url}: {str(e)}"
                errors.append(error_msg)
                logger.error(f"❌ Failed to extract profile {url}: {e}")
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Save batch results
        batch_result = BatchExtractionResult(
            total_profiles=len(profile_urls),
            successful_extractions=len(results),
            failed_extractions=len(errors),
            profiles=results,
            errors=errors,
            extraction_started_at=datetime.fromtimestamp(start_time),
            extraction_completed_at=datetime.fromtimestamp(end_time),
            total_time=total_time
        )
        
        batch_filename = os.path.join(JSON_DIR, f"batch_profiles_{int(start_time)}.json")
        with open(batch_filename, 'w', encoding='utf-8') as f:
            json.dump(batch_result.dict(), f, indent=2, default=str)
        
        logger.info(f"\n💾 Batch results saved to: {batch_filename}")
        logger.info(f"📊 Successfully extracted {len(results)}/{len(profile_urls)} profiles")
        
        return batch_result


# Standalone functions for easier usage
async def extract_single_profile(profile_url: str, use_login: bool = True) -> ExtractionResult:
    """
    Standalone function to extract a single LinkedIn profile.
    
    Example usage:
        result = await extract_single_profile("https://www.linkedin.com/in/example/")
    """
    async with LinkedInProfileExtractor() as extractor:
        return await extractor.scrape_linkedin_profile(profile_url, use_login)


async def extract_multiple_profiles(profile_urls: List[str], use_login: bool = True) -> BatchExtractionResult:
    """
    Standalone function to extract multiple LinkedIn profiles.
    
    Example usage:
        urls = ["https://www.linkedin.com/in/example1/", "https://www.linkedin.com/in/example2/"]
        result = await extract_multiple_profiles(urls)
    """
    async with LinkedInProfileExtractor() as extractor:
        return await extractor.batch_extract_profiles(profile_urls, use_login) 