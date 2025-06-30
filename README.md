# Streamlined LinkedIn Profile Extractor

AI-powered LinkedIn profile sourcing with two optimized methods: **RapidAPI** and **Google Crawler**. Features intelligent keyword extraction, targeted searches, and comprehensive profile data extraction.

## 🚀 Key Features

- **AI-Powered Keyword Extraction**: Automatically generates optimal search terms from job descriptions
- **Optimized Search Queries**: Uses format `site:linkedin.com/in "job_title" "industry" "location" "skills"`
- **Two Extraction Methods**: Fast API-based (RapidAPI) and free browser automation (Google Crawler)
- **Comprehensive Data**: Education, experience, skills, and about sections
- **Intelligent Scoring**: AI-powered candidate ranking and recommendations
- **Scalable Processing**: Async Redis Queue (ARQ) with distributed workers

## 🎯 Example Search Query

Input job description:
```
Senior Backend Engineer at fintech startup in San Francisco. 
Requires Python, Django, AWS experience. 
```

AI-generated search:
```
site:linkedin.com/in "backend engineer" "fintech" "San Francisco" "Python"
```

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-repo/linkedin-profile-extractor
   cd linkedin-profile-extractor
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Playwright browsers**
   ```bash
   playwright install
   ```

5. **Setup environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your API keys
   ```

## ⚙️ Configuration

Create `.env` file with required settings:

```env
# Required for AI keyword generation
OPENAI_API_KEY=your_openai_api_key

# Optional: For RapidAPI method
RAPIDAPI_KEY=your_rapidapi_key

# Optional: For enhanced proxy support
ZYTE_API_KEY=your_zyte_proxy_key
ZYTE_ENABLED=false

# Search settings

REQUEST_DELAY=2
HEADLESS=true
```

## 🔥 Quick Start

### Method 1: API Server (Recommended)

Start the FastAPI server:
```bash
python main.py
```

Submit a job via API:
```bash
curl -X POST "http://localhost:8000/api/jobs" \
  -H "Content-Type: application/json" \
  -d '{
    "job_description": "Senior Backend Engineer at fintech startup in San Francisco. Requires Python, Django, AWS experience.",
    "search_method": "rapid_api",
    "limit": 5
  }'
```

Check job results:
```bash
curl "http://localhost:8000/api/jobs/{job_id}/results"
```

### Method 2: Direct Script Usage

```python
import asyncio
from utils.enhanced_google_extractor import extract_profiles_rapid_api, extract_profiles_google_crawler

async def main():
    job_description = """
    Senior Backend Engineer at fintech startup in San Francisco.
    Requires Python, Django, AWS experience.
    """
    
    # Method 1: RapidAPI (fast, requires credits)
    profiles = await extract_profiles_rapid_api(job_description, max_results=5)
    
    # Method 2: Google Crawler (free, slower)
    profiles = await extract_profiles_google_crawler(job_description, max_results=5)
    
    for profile in profiles:
        print(f"{profile.name} - {profile.headline}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Method 3: Test the Integration

```bash
# Complete integration test with caching verification
python test_streamlined_integration.py

# Quick verification of caching and JSON output
python verify_caching.py

# Test GitHub integration and enhancement features
python test_github_integration.py
```

## 📊 Two Main Methods

### 1. RapidAPI Method (`rapid_api`)

**Best for**: Production use with budget for API calls

**Features**:
- Fast API-based search (2-5 seconds)
- High-quality, structured data
- Requires RapidAPI credits
- Built-in rate limiting

**Usage**:
```python
profiles = await extract_profiles_rapid_api(job_description, max_results=10)
```

### 2. Google Crawler Method (`google_crawler`)

**Best for**: Development, testing, or budget-conscious usage

**Features**:
- Free browser automation (15-30 seconds)
- Comprehensive data extraction
- Targeted searches for education, experience, skills
- No API costs

**Usage**:
```python
profiles = await extract_profiles_google_crawler(job_description, max_results=10)
```

## 🧠 AI Keyword Generation

The system uses OpenAI to automatically extract the best search keywords from job descriptions:

**Input**:
```
We are looking for a Senior Backend Engineer to join our fintech startup in San Francisco.
Requirements: Python, Django, PostgreSQL, AWS, microservices architecture.
```

**AI Output**:
```json
{
  "job_title": "Senior Backend Engineer",
  "industry": "fintech",
  "location": "San Francisco",
  "skills": ["Python", "Django", "AWS"],
  "companies": ["fintech startups", "financial technology"],
  "search_query": "site:linkedin.com/in \"Senior Backend Engineer\" \"fintech\" \"San Francisco\" \"Python\""
}
```

## 🔗 GitHub Integration (NEW!)

The system automatically enhances LinkedIn profiles with comprehensive GitHub data using intelligent name matching and AI-powered README analysis.

### 🎯 Features

**Automatic Discovery**:
- Searches GitHub using LinkedIn profile names
- Intelligent username matching with multiple formats
- Handles common name variations and titles

**Repository Analysis**:
- Fetches all public repositories (up to 100)
- Extracts programming languages and usage statistics  
- Identifies top technologies and frameworks
- Calculates language proficiency by code volume

**AI-Powered README Analysis**:
- Downloads and analyzes GitHub profile READMEs
- Extracts professional skills and achievements
- Identifies experience level and specializations
- Discovers additional contact information

### 📊 GitHub Data Structure

Each profile is enhanced with comprehensive GitHub information:

```json
{
  "name": "John Smith",
  "title": "Senior Backend Engineer",
  "skills": ["Python", "Django", "JavaScript", "Go", "TypeScript"],  // Enhanced with GitHub languages
  "location": "San Francisco, CA",  // Updated from GitHub if missing
  "github_data": {
    "username": "johnsmith",
    "profile_url": "https://github.com/johnsmith",
    "bio": "🚀 Building Scalable Systems and Delivering High-Performance Applications",
    "company": "TechCorp",
    "blog": "https://johnsmith.dev",
    "public_repos": 46,
    "followers": 230,
    "following": 155,
    "top_languages": {
      "Python": 15420,
      "JavaScript": 8930,
      "Go": 5210,
      "TypeScript": 3140,
      "Dockerfile": 890
    },
    "notable_repositories": [
      {
        "name": "awesome-api-framework",
        "description": "High-performance API framework for microservices",
        "language": "Python",
        "stars": 127,
        "url": "https://github.com/johnsmith/awesome-api-framework"
      }
    ],
    "ai_insights": {
      "skills": ["Docker", "Kubernetes", "React", "Node.js"],
      "experience_level": "senior",
      "specialization": "Full-stack Development with DevOps",
      "achievements": ["Open source contributor", "Tech conference speaker"],
      "certifications": ["AWS Certified Solutions Architect"]
    }
  }
}
```

### 🔍 GitHub Search Process

1. **Name Processing**: Extracts first + last name from LinkedIn profile
2. **Username Generation**: Creates search queries like:
   - `Daniyal+Qureshi`
   - `Daniyal-Qureshi` 
   - `DaniyalQureshi`
   - `Daniyal_Qureshi`
3. **Profile Matching**: Uses GitHub search API to find matching users
4. **Data Extraction**: Fetches profile, repositories, and languages
5. **README Analysis**: Downloads and analyzes profile README with AI
6. **Skills Enhancement**: Merges programming languages with existing skills

### 🤖 AI README Analysis

When a GitHub profile README is found, AI extracts:

- **Technical Skills**: Programming languages, frameworks, tools
- **Projects**: Notable projects and their descriptions
- **Experience Level**: Estimated seniority (junior/mid/senior)
- **Specialization**: Primary areas of expertise
- **Achievements**: Open source contributions, certifications
- **Contact Info**: Additional ways to reach the candidate

### 📈 Enhanced Profile Benefits

**For Recruiters**:
- Complete technical skill assessment
- Real coding activity and contributions
- Project portfolio and code quality insights
- Open source involvement and community presence

**For Candidates**:
- Comprehensive technical profile
- Showcase of real work and projects
- Evidence of continuous learning
- Community contributions and reputation

### ⚙️ GitHub API Configuration

No additional setup required! GitHub integration works automatically with:
- **Public GitHub API**: No authentication needed for public data
- **Rate Limiting**: Built-in respectful API usage
- **Error Handling**: Graceful fallback when GitHub data unavailable
- **Performance**: Async processing with minimal impact on extraction speed

## 🔄 Scalable Processing with ARQ

The system uses **Async Redis Queue (ARQ)** for scalable distributed processing:

**Features**:
- Process up to 10 jobs concurrently
- Automatic retries and error handling
- 7-day result caching
- Real-time job status tracking

**Start ARQ Worker**:
```bash
python arq_worker.py
```

**Worker Configuration**:
- **Max Jobs**: 10 concurrent
- **Timeout**: 10 minutes per job
- **Retry**: Automatic with exponential backoff
- **Caching**: 7-day Redis cache

## 📁 Smart Caching & JSON Output

### 🧠 Intelligent Caching System

The system automatically saves individual JSON files for each candidate and implements smart caching:

**Key Features:**
- **Individual JSON Files**: Each candidate gets their own file (e.g., `john-smith-123.json`)
- **Smart Filename Generation**: Uses LinkedIn username or sanitized name
- **7-Day Freshness Check**: Automatically refreshes data older than 7 days
- **Duplicate Prevention**: Skips re-crawling existing recent profiles
- **Summary Files**: Additional timestamped summary files for batch processing

**File Structure:**
```
output/json_profiles/
├── john-smith-123.json              # Individual profile (from LinkedIn username)
├── jane-doe-456.json                # Individual profile  
├── profiles_summary_google_crawler_20240115_143022.json  # Batch summary
└── profiles_summary_rapid_api_20240115_143155.json       # Batch summary
```

### 📄 Individual Profile JSON Structure

Each candidate file contains complete profile data:

```json
{
  "name": "John Smith",
  "title": "Senior Backend Engineer", 
  "company": "TechCorp",
  "location": "San Francisco, CA",
  "linkedin_url": "https://linkedin.com/in/johnsmith",
  "followers": "500+ followers",
  "education": [
    {
      "school": "Stanford University",
      "degree": "BS Computer Science", 
      "field": "Computer Science",
      "dates": "2018-2022"
    }
  ],
  "experience": [
    {
      "title": "Senior Backend Engineer",
      "company": "TechCorp", 
      "duration": "2022-Present",
      "location": "San Francisco, CA"
    }
  ],
  "skills": ["Python", "Django", "AWS", "PostgreSQL"],
  "about": "Experienced backend engineer passionate about fintech...",
  "extracted_at": "2024-01-15T10:30:00Z",
  "extraction_method": "Google Crawler"
}
```

### 📋 Summary File Structure

Batch processing creates additional summary files:

```json
{
  "extraction_method": "google_crawler",
  "extracted_at": "2024-01-15T14:30:22Z",
  "total_profiles": 5,
  "profiles": [
    {
      "name": "John Smith",
      "title": "Senior Backend Engineer",
      // ... complete profile data
    }
    // ... more profiles
  ]
}
```

### 🔄 Caching Workflow

1. **Check Existing**: Look for `{username}.json` or `{name}.json`
2. **Age Verification**: Check if file is < 7 days old
3. **Cache Decision**: 
   - ✅ **Use Cache**: If recent data exists
   - 🔄 **Refresh**: If data is stale or missing
4. **Save Immediately**: Write JSON after each profile extraction
5. **Summary Creation**: Generate batch summary at completion

## 🎯 Candidate Scoring

Automatically scores candidates against job requirements:

```json
{
  "overall_score": 8.5,
  "recommendation": "STRONG_MATCH",
  "score_breakdown": {
    "experience_match": 9.0,
    "skills_match": 8.0,
    "location_match": 9.0,
    "education_match": 8.0
  },
  "reasoning": "Strong match with 5+ years Python experience, fintech background, and San Francisco location."
}
```

## 🚀 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/jobs` | POST | Submit new extraction job |
| `/api/jobs/{job_id}/results` | GET | Get job results |
| `/api/jobs` | GET | List all jobs |
| `/api/health` | GET | System health check |
| `/docs` | GET | Interactive API documentation |

## ⚡ Performance

| Method | Speed | Cost | Quality | GitHub Enhancement | Use Case |
|--------|-------|------|---------|-------------------|----------|
| RapidAPI | 3-8s* | $$ | High | ✅ Automatic | Production |
| Google Crawler | 20-45s* | Free | Good | ✅ Automatic | Development/Testing |

*_Times include GitHub data enhancement. Add 2-5s per profile for GitHub integration._

## 🛠️ Advanced Configuration

### Proxy Support (Optional)

For enhanced reliability, configure Zyte proxy:

```env
ZYTE_API_KEY=your_zyte_key
ZYTE_ENABLED=true
```

### Browser Settings

```env
HEADLESS=true                    # Run browser in headless mode
BROWSER_TIMEOUT=30000           # Browser timeout in milliseconds
REQUEST_DELAY=2                 # Delay between requests in seconds
```

### Testing vs Production

```env
TESTING_MODE=true               # Uses 3 profiles for quick testing
# TESTING_MODE=false            # Uses 10 profiles for production
```

## 🐞 Troubleshooting

### Common Issues

1. **OpenAI API Error**: Ensure `OPENAI_API_KEY` is set correctly
2. **Browser Timeout**: Increase `BROWSER_TIMEOUT` or check internet connection
3. **RapidAPI Limit**: Check your RapidAPI quota and upgrade if needed
4. **Redis Connection**: Ensure Redis is running on localhost:6379

### Debug Mode

Enable verbose logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Test Individual Components

```bash
# Test AI keyword generation only
python -c "
import asyncio
from utils.enhanced_google_extractor import IntegratedLinkedInExtractor

async def test():
    async with IntegratedLinkedInExtractor() as extractor:
        keywords = extractor.generate_search_keywords('Backend engineer in fintech')
        print(keywords.search_query)

asyncio.run(test())
"
```

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/your-repo/linkedin-profile-extractor/issues)
- **Documentation**: [API Docs](http://localhost:8000/docs)
- **Health Check**: [System Status](http://localhost:8000/api/health) 