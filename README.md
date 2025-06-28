# LinkedIn Profile Extractor

A comprehensive Python tool that combines Google search functionality with LinkedIn profile extraction using OpenAI. This project merges the best features from the deepseek-ai-web-crawler and the TypeScript Playwright script to create a scalable, AI-powered LinkedIn sourcing solution.

## 🚀 Features

### 🔍 Google Search Integration
- **Smart LinkedIn Search**: Automatically searches Google for LinkedIn profiles using advanced queries
- **Site-Restricted Search**: Uses `site:linkedin.com/in` to find only profile pages
- **Pagination Support**: Automatically handles multiple pages of search results
- **URL Validation**: Filters and cleans LinkedIn URLs to ensure quality results

### 📊 AI-Powered Profile Extraction
- **OpenAI Integration**: Uses GPT-4o-mini for intelligent data extraction
- **Section-by-Section Processing**: Identifies and processes different LinkedIn sections (experience, education, skills, etc.)
- **HTML Cleaning**: Optimizes HTML content for AI processing while preserving essential data
- **Structured Data Output**: Returns clean, validated JSON data following consistent schemas

### 🔐 LinkedIn Authentication
- **Session Management**: Automatically handles LinkedIn login and session persistence
- **Cookie Storage**: Saves authentication cookies for 24-hour reuse
- **Safe Mode**: Option to search without LinkedIn login (Google search only)

### 🛠️ Multiple Operation Modes
1. **Search Only**: Find LinkedIn profile URLs without accessing LinkedIn directly
2. **Extract Only**: Process provided LinkedIn URLs to extract detailed profile data
3. **Full Workflow**: Complete end-to-end search and extraction pipeline

## 📋 Requirements

- Python 3.8+
- OpenAI API key
- LinkedIn account (for profile extraction)
- Playwright browser automation

## 🔧 Installation

1. **Clone or download the project**:
```bash
cd linkedin-profile-extractor
```

2. **Create a virtual environment**:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Install Playwright browsers**:
```bash
playwright install chromium
```

5. **Setup environment variables**:
```bash
cp env.example .env
# Edit .env file with your actual values
```

## ⚙️ Configuration

Create a `.env` file with the following variables:

```bash
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# LinkedIn Credentials (required for authenticated access)
LINKEDIN_EMAIL=your_email@example.com
LINKEDIN_PASSWORD=your_password_here

# Search Configuration
SEARCH_QUERY="backend engineer" "fintech" "San Francisco"
MAX_PROFILES=20
REQUEST_DELAY=2

# Browser Configuration
HEADLESS=False
BROWSER_TIMEOUT=30
```

## 🚀 Usage

### Interactive Mode

Run the main script for an interactive experience:

```bash
python main.py
```

Choose from the following options:
1. **Search Only** - Find LinkedIn profile URLs (safe, no LinkedIn login required)
2. **Extract Only** - Extract data from provided LinkedIn URLs
3. **Full Workflow** - Complete search and extraction pipeline

### Command Line Mode

#### Search for profiles:
```bash
python main.py search "backend engineer" "fintech" "San Francisco"
```

#### Extract specific profiles:
```bash
python main.py extract https://linkedin.com/in/profile1 https://linkedin.com/in/profile2
```

#### Full workflow:
```bash
python main.py workflow "backend engineer" "fintech" "San Francisco"
```

### Programmatic Usage

```python
import asyncio
from utils.google_search import search_linkedin_profiles
from utils.profile_extractor import extract_multiple_profiles

async def main():
    # Search for profiles
    search_result = await search_linkedin_profiles(
        ["backend engineer", "fintech", "San Francisco"], 
        max_results=20
    )
    
    # Extract profile data
    extraction_result = await extract_multiple_profiles(
        search_result.profiles[:5],  # Extract first 5 profiles
        use_login=True
    )
    
    print(f"Found {search_result.total_results} profiles")
    print(f"Extracted {extraction_result.successful_extractions} profiles")

asyncio.run(main())
```

## 📊 Output Format

### Search Results
```json
{
  "search_query": "site:linkedin.com/in \"backend engineer\" \"fintech\" \"San Francisco\"",
  "search_terms": ["backend engineer", "fintech", "San Francisco"],
  "total_results": 25,
  "profiles": ["https://linkedin.com/in/profile1", "..."],
  "searched_at": "2024-01-15T10:30:00"
}
```

### Profile Data
```json
{
  "name": "John Doe",
  "headline": "Senior Backend Engineer at FinTech Startup",
  "linkedin_url": "https://linkedin.com/in/johndoe",
  "location": "San Francisco, California, United States",
  "summary": "Experienced backend engineer with 8+ years...",
  "experience": [
    {
      "title": "Senior Backend Engineer",
      "company": "FinTech Startup",
      "date_range": "Jan 2022 - Present",
      "duration": "2 yrs 3 mos",
      "description": "Led development of microservices..."
    }
  ],
  "education": [
    {
      "school": "Stanford University",
      "degree": "Master of Science",
      "field_of_study": "Computer Science",
      "date_range": "2018 - 2020"
    }
  ],
  "skills": ["Python", "AWS", "Microservices", "Docker"],
  "connections": "500+ connections",
  "extracted_at": "2024-01-15T10:45:00"
}
```

## 📁 Project Structure

```
linkedin-profile-extractor/
├── main.py                 # Main application entry point
├── config/
│   └── settings.py         # Configuration management
├── models/
│   └── linkedin_profile.py # Data models and schemas
├── utils/
│   ├── google_search.py    # Google search functionality
│   └── profile_extractor.py # LinkedIn profile extraction
├── output/                 # Generated output files
│   ├── html_profiles/      # Saved HTML files
│   ├── json_profiles/      # Extracted JSON data
│   ├── search_results/     # Search result files
│   └── sessions/           # LinkedIn session data
├── requirements.txt        # Python dependencies
├── env_template.txt        # Environment variables template
└── README.md              # This file
```

## 🔍 How It Works

### 1. Google Search Phase
- Constructs targeted Google search queries using `site:linkedin.com/in` restriction
- Uses Playwright to automate browser interaction and handle Google's anti-bot measures
- Extracts and validates LinkedIn profile URLs from search results
- Supports pagination to gather comprehensive results

### 2. Profile Extraction Phase
- Uses Playwright to navigate to LinkedIn profiles with proper stealth settings
- Handles LinkedIn authentication and session management
- Applies intelligent HTML cleaning to extract only relevant content sections
- Uses OpenAI's GPT model to parse HTML and extract structured data
- Processes different sections (experience, education, skills) with specialized prompts

### 3. Data Processing
- Validates and cleans extracted data using Pydantic models
- Saves both raw HTML and cleaned/structured JSON outputs
- Provides comprehensive error handling and retry mechanisms
- Generates detailed reports and summaries

## 🛡️ Safety Features

- **Stealth Mode**: Advanced browser fingerprinting protection
- **Rate Limiting**: Configurable delays between requests
- **Session Persistence**: Reduces login frequency to avoid account flagging
- **Safe Mode**: Option to only search without accessing LinkedIn directly
- **Error Recovery**: Robust error handling and retry mechanisms

## ⚡ Performance Optimizations

- **Async Processing**: Non-blocking operations for better performance
- **HTML Optimization**: Intelligent content filtering for faster AI processing
- **Session Reuse**: Persistent authentication to reduce overhead
- **Batch Processing**: Efficient handling of multiple profiles
- **Configurable Limits**: Customizable rate limits and timeouts

## 🔧 Customization

### Modify Search Strategy
Edit `utils/google_search.py` to customize:
- Search query construction
- URL filtering logic
- Pagination behavior
- Error handling

### Customize Data Extraction
Edit `utils/profile_extractor.py` to:
- Add new profile sections
- Modify OpenAI prompts
- Change data validation rules
- Adjust HTML cleaning logic

### Add New Output Formats
Extend `models/linkedin_profile.py` to:
- Add new data fields
- Create custom export formats
- Implement additional validation

## 🚨 Important Notes

### LinkedIn Terms of Service
- Always respect LinkedIn's Terms of Service and robots.txt
- Use reasonable rate limits and delays between requests
- Consider using LinkedIn's official API for commercial applications
- This tool is intended for personal research and recruitment purposes

### Account Safety
- Use a dedicated LinkedIn account for automation
- Enable two-factor authentication on your LinkedIn account
- Monitor your account for any unusual activity
- Consider using LinkedIn Premium for better access limits

### API Usage
- Monitor your OpenAI API usage and costs
- GPT-4o-mini is cost-effective but consider usage limits
- Implement additional error handling for API rate limits
- Cache results to minimize API calls

## 🐛 Troubleshooting

### Common Issues

1. **LinkedIn Login Failed**
   - Check credentials in `.env` file
   - Verify two-factor authentication is disabled
   - Clear browser data in `output/sessions/`

2. **Google Search Blocked**
   - Add longer delays between requests
   - Use different user agents
   - Consider using proxy services

3. **OpenAI API Errors**
   - Verify API key is correct
   - Check API usage limits
   - Monitor rate limits

4. **Browser Automation Issues**
   - Ensure Playwright browsers are installed
   - Try running in non-headless mode
   - Check for browser updates

## 📈 Future Enhancements

- [ ] Support for additional search engines
- [ ] Integration with LinkedIn Sales Navigator
- [ ] Advanced profile scoring and filtering
- [ ] Export to CRM systems
- [ ] Parallel processing for large-scale extraction
- [ ] Machine learning for improved data extraction
- [ ] Real-time profile monitoring
- [ ] Integration with recruitment platforms

## 📄 License

This project is for educational and research purposes. Please ensure compliance with LinkedIn's Terms of Service and applicable laws in your jurisdiction.

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 💬 Support

For questions, issues, or suggestions:
- Create an issue in the repository
- Review existing documentation
- Check the troubleshooting section

---

**⚠️ Disclaimer**: This tool is provided as-is for educational purposes. Users are responsible for ensuring compliance with all applicable terms of service and laws. The authors are not responsible for any misuse or consequences resulting from the use of this tool. 