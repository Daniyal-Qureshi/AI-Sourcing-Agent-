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

# GitHub Configuration
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# Zyte Proxy Configuration
ZYTE_API_KEY = os.getenv("ZYTE_API_KEY", "afacf0f6b8b841f2892a166c3a102741")
ZYTE_PROXY_URL = os.getenv("ZYTE_PROXY_URL", "http://api.zyte.com:8011")
ZYTE_ENABLED = os.getenv("ZYTE_ENABLED", "True").lower() == "true"

# Search Configuration
GOOGLE_SEARCH_BASE_URL = "https://www.google.com/search"
MAX_PROFILES = int(os.getenv("MAX_PROFILES", "20"))
REQUEST_DELAY = int(os.getenv("REQUEST_DELAY", "2"))

TESTING_MAX_PROFILES = 5  # Use 5 profiles for quick testing
PRODUCTION_MAX_PROFILES = 10  # Use 10 profiles for production



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
    "--disable-features=VizDisplayCompositor",
    "--ignore-certificate-errors",
    "--ignore-ssl-errors",
    "--ignore-certificate-errors-spki-list",
    "--ignore-ssl-errors-spki-list",
    "--disable-ssl-verification"
]

# File Paths
OUTPUT_DIR = "./output"
JSON_DIR = f"{OUTPUT_DIR}/json_profiles"
SEARCH_RESULTS_DIR = f"{OUTPUT_DIR}/search_results"

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
        errors.append("OPENAI_API_KEY is required for AI features")
    
    if errors:
        raise ValueError(f"Configuration errors: {', '.join(errors)}")
    
    print("✅ Configuration validated successfully")

def get_browser_config() -> Dict[str, Any]:
    """Get browser configuration for Playwright with optional Zyte proxy."""
    config = {
        "headless": HEADLESS,
        "args": PLAYWRIGHT_ARGS,
        "user_agent": BROWSER_USER_AGENT,
        "viewport": {"width": 1920, "height": 1080}
    }
    
    # Add Zyte proxy configuration if enabled
    if ZYTE_ENABLED and ZYTE_API_KEY:
        config["proxy"] = {
            "server": ZYTE_PROXY_URL,
            "username": ZYTE_API_KEY,
            "password": ""
        }
    
    return config

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