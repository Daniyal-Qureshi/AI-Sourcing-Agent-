"""
Configuration settings for LinkedIn Profile Extractor
"""
import os
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = "gpt-4o-mini"  # Cost-effective model with good performance
OPENAI_MAX_TOKENS = 2000
OPENAI_TEMPERATURE = 0

# LinkedIn Configuration
LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")

# Search Configuration
DEFAULT_SEARCH_QUERY = os.getenv("SEARCH_QUERY", '"backend engineer" "fintech" "San Francisco"')
GOOGLE_SEARCH_BASE_URL = "https://www.google.com/search"
MAX_PROFILES = int(os.getenv("MAX_PROFILES", "20"))
REQUEST_DELAY = int(os.getenv("REQUEST_DELAY", "2"))

# Browser Configuration
HEADLESS = os.getenv("HEADLESS", "False").lower() == "true"
BROWSER_TIMEOUT = int(os.getenv("BROWSER_TIMEOUT", "30")) * 1000  # Convert to milliseconds
BROWSER_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Playwright Configuration
PLAYWRIGHT_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--disable-dev-shm-usage",
    "--no-sandbox",
    "--disable-web-security",
    "--disable-features=VizDisplayCompositor"
]

# File Paths
OUTPUT_DIR = "./output"
HTML_DIR = f"{OUTPUT_DIR}/html_profiles"
JSON_DIR = f"{OUTPUT_DIR}/json_profiles"
SEARCH_RESULTS_DIR = f"{OUTPUT_DIR}/search_results"
SESSIONS_DIR = f"{OUTPUT_DIR}/sessions"

# LinkedIn Profile Data Structure
REQUIRED_PROFILE_FIELDS = [
    "name",
    "headline",
    "linkedin_url",
    "location"
]

OPTIONAL_PROFILE_FIELDS = [
    "summary",
    "experience",
    "education",
    "skills",
    "connections",
    "profileImage"
]

# Google Search Configuration
GOOGLE_SEARCH_PARAMS = {
    "num": 50,  # Number of results per page
    "start": 0,  # Starting index
    "hl": "en",  # Language
    "gl": "us"   # Geolocation
}

# Retry Configuration
MAX_RETRIES = 3
RETRY_DELAY = 5

# Logging Configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

def validate_config() -> None:
    """Validate that all required configuration is present."""
    errors = []
    
    if not OPENAI_API_KEY:
        errors.append("OPENAI_API_KEY is required")
    
    if not LINKEDIN_EMAIL:
        errors.append("LINKEDIN_EMAIL is required")
    
    if not LINKEDIN_PASSWORD:
        errors.append("LINKEDIN_PASSWORD is required")
    
    if errors:
        raise ValueError(f"Configuration errors: {', '.join(errors)}")
    
    print("✅ Configuration validated successfully")

def get_browser_config() -> Dict[str, Any]:
    """Get browser configuration for Playwright."""
    return {
        "headless": HEADLESS,
        "args": PLAYWRIGHT_ARGS,
        "user_agent": BROWSER_USER_AGENT,
        "viewport": {"width": 1920, "height": 1080}
    }

def get_openai_config() -> Dict[str, Any]:
    """Get OpenAI configuration."""
    return {
        "api_key": OPENAI_API_KEY,
        "model": OPENAI_MODEL,
        "max_tokens": OPENAI_MAX_TOKENS,
        "temperature": OPENAI_TEMPERATURE
    }

def get_search_config() -> Dict[str, Any]:
    """Get search configuration."""
    return {
        "base_url": GOOGLE_SEARCH_BASE_URL,
        "params": GOOGLE_SEARCH_PARAMS,
        "max_profiles": MAX_PROFILES,
        "request_delay": REQUEST_DELAY
    } 