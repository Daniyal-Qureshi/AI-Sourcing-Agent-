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
        
        return 'profile_header'
    
    def get_section_extraction_prompt(self, section_type: str, section_html: str) -> str:
        """Get appropriate prompt for OpenAI based on section type."""
        base_prompt = (
            "Extract data from this LinkedIn profile HTML section. "
            "Return only valid JSON without any markdown formatting or explanations.\n\n"
            f"HTML:\n{section_html}\n\n"
        )

        prompts = {
            'profile_header': base_prompt + (
                "Extract profile header data in this JSON format:\n"
                "{\n"
                '  "name": "Full Name",\n'
                '  "headline": "Job Title/Headline",\n'
                '  "location": "City, State, Country",\n'
                '  "connections": "X connections",\n'
                '  "profileImage": "image_url_if_available"\n'
                "}"
            ),

            'about': base_prompt + (
                "Extract the about/summary section in this JSON format:\n"
                "{\n"
                '  "summary": "Full about text/summary"\n'
                "}"
            ),

            'experience': base_prompt + (
                "Extract all work experience entries in this JSON format:\n"
                "{\n"
                '  "experience": [\n'
                "    {\n"
                '      "title": "Job Title",\n'
                '      "company": "Company Name",\n'
                '      "date_range": "Start Date - End Date",\n'
                '      "duration": "X yrs Y mos",\n'
                '      "description": "Job description if available"\n'
                "    }\n"
                "  ]\n"
                "}"
            ),

            'education': base_prompt + (
                "Extract all education entries in this JSON format:\n"
                "{\n"
                '  "education": [\n'
                "    {\n"
                '      "school": "School Name",\n'
                '      "degree": "Degree Type",\n'
                '      "field_of_study": "Field of Study",\n'
                '      "date_range": "Start Date - End Date"\n'
                "    }\n"
                "  ]\n"
                "}"
            ),

            'skills': base_prompt + (
                "Extract all skills in this JSON format:\n"
                "{\n"
                '  "skills": ["skill1", "skill2", "skill3"]\n'
                "}"
            )
        }

        # Fallback prompt for unknown section types
        return prompts.get(
            section_type,
            base_prompt + "Extract any relevant profile information from this section and return it as JSON."
        )

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
                section_type = self.determine_section_type(section_html) #unknown
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
    
    def extract_username_from_url(self, linkedin_url: str) -> str:
        """Extract username from LinkedIn URL for consistent file naming."""
        try:
            # Clean the URL thoroughly
            clean_url = linkedin_url.strip()
            
            # Remove trailing slashes and query parameters
            clean_url = clean_url.rstrip('/').split('?')[0].split('#')[0]
            
            # Extract username part - handle different LinkedIn URL formats
            if '/in/' in clean_url:
                # Standard format: https://www.linkedin.com/in/username
                username = clean_url.split('/in/')[-1]
            elif '/pub/' in clean_url:
                # Old format: https://www.linkedin.com/pub/username
                username = clean_url.split('/pub/')[-1].split('/')[0]
            else:
                # Fallback: take the last part after final slash
                username = clean_url.split('/')[-1]
            
            # Clean username thoroughly - remove any remaining slashes and special chars
            username = username.strip().rstrip('/').strip()
            
            # Replace invalid file system characters
            username = re.sub(r'[^a-zA-Z0-9_-]', '-', username)
            
            # Remove multiple consecutive dashes and clean up
            username = re.sub(r'-+', '-', username).strip('-')
            
            # Ensure we have a valid username
            if not username or username in ['', '-']:
                username = 'unknown'
                
            logger.debug(f"🔗 URL: {linkedin_url} → Username: {username}")
            return username
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to extract username from {linkedin_url}: {e}")
            return 'unknown'
    
    def check_existing_files(self, username: str) -> Dict[str, Any]:
        """
        Comprehensive check if HTML and JSON files already exist for a username.
        Returns detailed information to minimize unnecessary scraping.
        """
        html_file = os.path.join(HTML_DIR, f"{username}.html")
        json_file = os.path.join(JSON_DIR, f"{username}.json")
        
        html_exists = os.path.exists(html_file)
        json_exists = os.path.exists(json_file)
        
        # Get file info if they exist
        html_info = None
        json_info = None
        
        if html_exists:
            try:
                html_stat = os.stat(html_file)
                html_info = {
                    'size': html_stat.st_size,
                    'modified': datetime.fromtimestamp(html_stat.st_mtime).isoformat(),
                    'age_hours': (time.time() - html_stat.st_mtime) / 3600
                }
            except Exception as e:
                logger.warning(f"⚠️ Could not get HTML file info for {username}: {e}")
        
        if json_exists:
            try:
                json_stat = os.stat(json_file)
                json_info = {
                    'size': json_stat.st_size,
                    'modified': datetime.fromtimestamp(json_stat.st_mtime).isoformat(),
                    'age_hours': (time.time() - json_stat.st_mtime) / 3600
                }
            except Exception as e:
                logger.warning(f"⚠️ Could not get JSON file info for {username}: {e}")
        
        # Log file status for better tracking
        if html_exists or json_exists:
            logger.info(f"📁 File check for '{username}':")
            if html_exists:
                logger.info(f"   ✅ HTML exists: {html_file} ({html_info['size']} bytes, {html_info['age_hours']:.1f}h old)")
            else:
                logger.info(f"   ❌ HTML missing: {html_file}")
            if json_exists:
                logger.info(f"   ✅ JSON exists: {json_file} ({json_info['size']} bytes, {json_info['age_hours']:.1f}h old)")
            else:
                logger.info(f"   ❌ JSON missing: {json_file}")
        else:
            logger.info(f"📁 No existing files found for '{username}' - will need to scrape")
        
        return {
            'html_exists': html_exists,
            'json_exists': json_exists,
            'html_path': html_file,
            'json_path': json_file,
            'html_info': html_info,
            'json_info': json_info,
            'username': username
        }

    async def scrape_linkedin_profile_html_only(self, profile_url: str, use_login: bool = True) -> Dict[str, Any]:
        """
        Scrape LinkedIn profile and save only HTML - no processing.
        This is the first phase: pure scraping.
        """
        username = self.extract_username_from_url(profile_url)
        logger.info(f"🚀 Starting HTML scraping for: {profile_url} (username: {username})")
        
        # COMPREHENSIVE CHECK: Minimize scraping as much as possible
        file_status = self.check_existing_files(username)
        if file_status['html_exists']:
            html_info = file_status['html_info']
            logger.info(f"🚫 SCRAPING AVOIDED for '{username}' - HTML already exists!")
            logger.info(f"   💾 File: {file_status['html_path']}")
            logger.info(f"   📊 Size: {html_info['size']} bytes, Age: {html_info['age_hours']:.1f} hours")
            logger.info(f"   ⚡ Saved scraping time and resources!")
            return {
                'success': True,
                'username': username,
                'profile_url': profile_url,
                'html_path': file_status['html_path'],
                'skipped': True,
                'skip_reason': 'html_exists',
                'file_info': html_info
            }
        
        try:
            # Check if we need to login
            if use_login:
                current_url = self.page.url if self.page else ""
                if not current_url or "linkedin.com" not in current_url:
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
            
            # Get page content
            content = await self.page.content()
            
            # Save HTML with username
            html_filename = os.path.join(HTML_DIR, f"{username}.html")
            with open(html_filename, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"💾 Saved HTML to: {html_filename}")
            
           
            
            return {
                'success': True,
                'username': username,
                'profile_url': profile_url,
                'html_path': html_filename,
                'skipped': False,

            }
            
        except Exception as e:
            error_msg = f"HTML scraping failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            
            return {
                'success': False,
                'username': username,
                'profile_url': profile_url,
                'error': error_msg,

            }

    def process_html_to_profile(self, username: str, profile_url: str = None) -> ExtractionResult:
        """
        Process saved HTML file to extract LinkedIn profile data.
        This is the second phase: pure processing (no browser needed).
        """
        logger.info(f"🔄 Processing HTML for username: {username}")
        
        # Check if files exist
        file_status = self.check_existing_files(username)
        
        # If JSON already exists, load and return it - AVOID PROCESSING
        if file_status['json_exists']:
            json_info = file_status['json_info']
            logger.info(f"🚫 PROCESSING AVOIDED for '{username}' - JSON already exists!")
            logger.info(f"   💾 File: {file_status['json_path']}")
            logger.info(f"   📊 Size: {json_info['size']} bytes, Age: {json_info['age_hours']:.1f} hours")
            logger.info(f"   ⚡ Loading existing profile data instead of reprocessing!")
            try:
                with open(file_status['json_path'], 'r', encoding='utf-8') as f:
                    profile_data = json.load(f)
                profile = LinkedInProfile(**profile_data)
                logger.info(f"   ✅ Loaded existing profile: {profile.name}")
                return ExtractionResult(
                    success=True,
                    profile=profile
                )
            except Exception as e:
                logger.warning(f"⚠️ Failed to load existing JSON for {username}: {e}")
                logger.warning(f"   🔄 Will reprocess HTML file instead")
        
        # Check if HTML exists
        if not file_status['html_exists']:
            error_msg = f"No HTML file found for username: {username}"
            logger.error(f"❌ {error_msg}")
            return ExtractionResult(
                success=False,
                error=error_msg
                
            )
        
        try:
            # Load HTML content
            with open(file_status['html_path'], 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            logger.info(f"📄 Loaded HTML file: {file_status['html_path']}")
            
            # Clean HTML for processing (but don't save it)
            cleaned_html = self.clean_html(html_content)
            reduction = round((1 - len(cleaned_html)/len(html_content)) * 100)
            logger.info(f"📏 HTML size reduced from {len(html_content)} to {len(cleaned_html)} characters ({reduction}% reduction)")
            
            # Extract structured profile data from cleaned HTML
            logger.info("📊 Extracting data from cleaned HTML...")
            
            # Use the profile_url from parameter or try to reconstruct from username
            if not profile_url:
                profile_url = f"https://www.linkedin.com/in/{username}/"
            
            # Since this is a sync function calling an async one, we need to handle it
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                profile_data = loop.run_until_complete(
                    self.extract_profile_data_from_html(cleaned_html, profile_url)
                )
            finally:
                loop.close()
            
            # Save JSON with username
            json_filename = os.path.join(JSON_DIR, f"{username}.json")
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(profile_data.dict(), f, indent=2, default=str)
            logger.info(f"💾 Saved JSON to: {json_filename}")
            
            return ExtractionResult(
                success=True,
                profile=profile_data
            )
            
        except Exception as e:
            error_msg = f"HTML processing failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            
            return ExtractionResult(
                success=False,
                error=error_msg
            )

    async def batch_scrape_html_only(self, profile_urls: List[str], use_login: bool = True) -> Dict[str, Any]:
        """Scrape HTML for multiple LinkedIn profiles - first phase only."""
        logger.info(f"🚀 Starting batch HTML scraping of {len(profile_urls)} profiles")
        
        # LOG ALL URLS BEING PROCESSED
        logger.info(f"🔗 URLs to be processed in this batch:")
        for i, url in enumerate(profile_urls, 1):
            logger.info(f"   {i:2d}. {url}")
        
        results = []
        errors = []
        skipped = 0
        
        for i, url in enumerate(profile_urls):
            logger.info(f"\n" + "="*80)
            logger.info(f"📍 PROCESSING URL {i + 1}/{len(profile_urls)}")
            logger.info(f"🔗 URL: {url}")
            username = self.extract_username_from_url(url)
            logger.info(f"👤 Username: {username}")
            logger.info(f"="*80)
            
            try:
                result = await self.scrape_linkedin_profile_html_only(url, use_login)
                if result['success']:
                    results.append(result)
                    if result.get('skipped', False):
                        skipped += 1
                        logger.info(f"⏭️ Skipped (already exists): {result['username']}")
                    else:
                        logger.info(f"✅ Successfully scraped HTML: {result['username']}")
                else:
                    errors.append(f"{url}: {result.get('error', 'Unknown error')}")
                    logger.error(f"❌ Failed to scrape HTML: {result.get('error', 'Unknown error')}")
                
                # Add delay between requests
                if i < len(profile_urls) - 1 and not result.get('skipped', False):
                    logger.info(f"⏳ Waiting {REQUEST_DELAY} seconds before next profile...")
                    await asyncio.sleep(REQUEST_DELAY)
                    
            except Exception as e:
                error_msg = f"{url}: {str(e)}"
                errors.append(error_msg)
                logger.error(f"❌ Failed to scrape HTML for {url}: {e}")
        
        logger.info(f"\n📊 SCRAPING EFFICIENCY REPORT:")
        logger.info(f"   🎯 Total profiles requested: {len(profile_urls)}")
        logger.info(f"   ✅ Successfully scraped (new): {len(results) - skipped}")
        logger.info(f"   🚫 SCRAPING AVOIDED (cached): {skipped}")
        logger.info(f"   ❌ Failed: {len(errors)}")
        logger.info(f"   ⚡ Efficiency: {(skipped / len(profile_urls) * 100):.1f}% scraping avoided!")
        
        if skipped > 0:
            logger.info(f"   💰 Resources saved by avoiding {skipped} unnecessary scrapes!")
        
        return {
            'total_profiles': len(profile_urls),
            'successful_scrapes': len(results),
            'new_scrapes': len(results) - skipped,
            'skipped_scrapes': skipped,
            'failed_scrapes': len(errors),
            'results': results,
            'errors': errors
        }

    def batch_process_html_to_profiles(self, usernames: List[str]) -> BatchExtractionResult:
        """Process multiple HTML files to extract profile data - second phase only."""
        logger.info(f"🔄 Starting batch HTML processing of {len(usernames)} profiles")
        
        results = []
        errors = []
        
        for i, username in enumerate(usernames):
            logger.info(f"\n📍 Processing HTML {i + 1}/{len(usernames)}: {username}")
            
            try:
                result = self.process_html_to_profile(username)
                if result.success:
                    results.append(result.profile)
                    logger.info(f"✅ Successfully processed: {result.profile.name}")
                else:
                    errors.append(f"{username}: {result.error}")
                    logger.error(f"❌ Failed to process HTML: {result.error}")
                    
            except Exception as e:
                error_msg = f"{username}: {str(e)}"
                errors.append(error_msg)
                logger.error(f"❌ Failed to process HTML for {username}: {e}")
        
        # Save batch results
        batch_result = BatchExtractionResult(
            total_profiles=len(usernames),
            successful_extractions=len(results),
            failed_extractions=len(errors),
            profiles=results,
            errors=errors,
            extraction_started_at=datetime.now(),
            extraction_completed_at=datetime.now()
        )
        
        batch_filename = os.path.join(JSON_DIR, f"batch_processed_{int(time.time())}.json")
        with open(batch_filename, 'w', encoding='utf-8') as f:
            json.dump(batch_result.dict(), f, indent=2, default=str)
        
        logger.info(f"\n💾 Batch processing results saved to: {batch_filename}")
        logger.info(f"📊 Successfully processed {len(results)}/{len(usernames)} profiles")
        
        return batch_result


    async def scrape_linkedin_profile(self, profile_url: str, use_login: bool = True) -> ExtractionResult:
        """
        Legacy method: Scrape a single LinkedIn profile (full process).
        For backward compatibility - combines scraping and processing.
        """
        # First scrape HTML
        html_result = await self.scrape_linkedin_profile_html_only(profile_url, use_login)
        
        if not html_result['success']:
            return ExtractionResult(
                success=False,
                error=html_result.get('error', 'Scraping failed')
            )
        
        # Then process HTML if it wasn't skipped
        if html_result.get('skipped', False):
            # Check if JSON exists, if so return it
            username = html_result['username']
            file_status = self.check_existing_files(username)
            if file_status['json_exists']:
                try:
                    with open(file_status['json_path'], 'r', encoding='utf-8') as f:
                        profile_data = json.load(f)
                    profile = LinkedInProfile(**profile_data)
                    return ExtractionResult(
                        success=True,
                        profile=profile
                    )
                except Exception as e:
                    return ExtractionResult(
                        success=False,
                        error=f"Failed to load existing JSON: {str(e)}"
                    )
        
        # Process the HTML
        username = html_result['username']
        return self.process_html_to_profile(username, profile_url)

    async def batch_extract_profiles(self, profile_urls: List[str], use_login: bool = True) -> BatchExtractionResult:
        """
        Legacy method: Extract multiple LinkedIn profiles in batch (full process).
        For backward compatibility - combines scraping and processing.
        """
        # First phase: scrape all HTML
        html_results = await self.batch_scrape_html_only(profile_urls, use_login)
        
        # Extract usernames from successful results
        usernames = [result['username'] for result in html_results['results'] if result['success']]
        
        if not usernames:
            return BatchExtractionResult(
                total_profiles=len(profile_urls),
                successful_extractions=0,
                failed_extractions=len(profile_urls),
                profiles=[],
                errors=html_results['errors'],
                extraction_started_at=datetime.now(),
                extraction_completed_at=datetime.now()
            )
        
        # Second phase: process all HTML files
        return self.batch_process_html_to_profiles(usernames)


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


# New standalone functions for the two-phase approach
async def scrape_html_only(profile_urls: List[str], use_login: bool = True) -> Dict[str, Any]:
    """
    Standalone function to only scrape HTML from LinkedIn profiles.
    Phase 1 of the two-phase approach.
    
    Example usage:
        html_results = await scrape_html_only(["https://www.linkedin.com/in/example1/"])
    """
    async with LinkedInProfileExtractor() as extractor:
        return await extractor.batch_scrape_html_only(profile_urls, use_login)


def process_html_files(usernames: List[str]) -> BatchExtractionResult:
    """
    Standalone function to process HTML files and extract profile data.
    Phase 2 of the two-phase approach - no browser needed.
    
    Example usage:
        usernames = ["johndoe", "janedoe"]
        profiles = process_html_files(usernames)
    """
    extractor = LinkedInProfileExtractor()
    return extractor.batch_process_html_to_profiles(usernames) 