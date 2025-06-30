# 🚀 LinkedIn Profile Extractor - Complete System

AI-powered LinkedIn profile sourcing with dual extraction methods, GitHub integration, intelligent scoring, and enterprise-grade architecture. Features **RapidAPI**, **Google Crawler**, **Zyte Proxy**, **Playwright**, **Redis Caching**, and **ARQ Workers**.

## 🌐 Complete System Architecture

```
                              🌐 CLIENT REQUEST
                                     │
                                     ▼
                           ┌─────────────────────┐
                           │    FastAPI Server   │
                           │    (Port 8000)      │
                           │                     │
                           │ • REST Endpoints    │
                           │ • Job Validation    │
                           │ • Result Retrieval  │
                           │ • Health Checks     │
                           └─────────┬───────────┘
                                     │
                                     ▼
                           ┌─────────────────────┐
                           │   Redis + ARQ       │
                           │   Job Queue         │
                           │                     │
                           │ • Task Management   │
                           │ • Auto Load Balance │
                           │ • Result Caching    │
                           │ • Status Tracking   │
                           └─────────┬───────────┘
                                     │
                                     ▼
                           ┌─────────────────────┐
                           │    ARQ Worker       │
                           │  (Scalable: 1→N)    │
                           │                     │
                           │ • AI Keyword Gen    │
                           │ • Route Selection   │
                           │ • Data Processing   │
                           │ • Result Assembly   │
                           └─────────┬───────────┘
                                     │
                          ┌──────────┼──────────┐
                          │          │          │
                          ▼          ▼          ▼
                 ┌─────────────┐ ┌─────────┐ ┌──────────────┐
                 │ EXTRACTION  │ │ SCORING │ │   GITHUB     │
                 │  METHODS    │ │ ENGINE  │ │ ENRICHMENT   │
                 └─────────────┘ └─────────┘ └──────────────┘
                          │          │          │
                          ▼          ▼          ▼
        ┌─────────────────────────────────────────────────────────────┐
        │                    PROCESSING PIPELINE                       │
        │                                                             │
        │  ┌─────────────────┐              ┌─────────────────────┐   │
        │  │   RapidAPI      │              │   Google Crawler    │   │
        │  │   Pipeline      │              │   Pipeline          │   │
        │  │                 │              │                     │   │
        │  │ ┌─────────────┐ │              │ ┌─────────────────┐ │   │
        │  │ │ AI Keywords │ │              │ │  AI Keywords    │ │   │
        │  │ │ Generation  │ │              │ │  Generation     │ │   │
        │  │ └─────┬───────┘ │              │ └─────┬───────────┘ │   │
        │  │       │         │              │       │             │   │
        │  │       ▼         │              │       ▼             │   │
        │  │ ┌─────────────┐ │              │ ┌─────────────────┐ │   │
        │  │ │ RapidAPI    │ │              │ │ Google Search   │ │   │
        │  │ │ Call        │ │              │ │ Query Build     │ │   │
        │  │ │             │ │              │ └─────┬───────────┘ │   │
        │  │ │ • Fast      │ │              │       │             │   │
        │  │ │ • JSON Data │ │              │       ▼             │   │
        │  │ │ • Rich Info │ │              │ ┌─────────────────┐ │   │
        │  │ └─────┬───────┘ │              │ │   Zyte Proxy    │ │   │
        │  │       │         │              │ │   Manager       │ │   │
        │  │       ▼         │              │ │                 │ │   │
        │  │ ┌─────────────┐ │              │ │ • IP Rotation   │ │   │
        │  │ │ Profile     │ │              │ │ • Anti-Block    │ │   │
        │  │ │ Parsing     │ │              │ │ • Geo Distribute│ │   │
        │  │ │             │ │              │ │ • Header Rotate │ │   │
        │  │ │ • Name      │ │              │ └─────┬───────────┘ │   │
        │  │ │ • Experience│ │              │       │             │   │
        │  │ │ • Education │ │              │       ▼             │   │
        │  │ │ • Skills    │ │              │ ┌─────────────────┐ │   │
        │  │ │ • Location  │ │              │ │ Playwright      │ │   │
        │  │ └─────┬───────┘ │              │ │ Browser Engine  │ │   │
        │  │       │         │              │ │                 │ │   │
        │  │       ▼         │              │ │ • Stealth Mode  │ │   │
        │  │ ┌─────────────┐ │              │ │ • Human Sim     │ │   │
        │  │ │ LinkedIn    │ │              │ │ • Dynamic Load  │ │   │
        │  │ │ Profile     │ │              │ │ • Content Parse │ │   │
        │  │ │ Objects     │ │              │ └─────┬───────────┘ │   │
        │  │ └─────────────┘ │              │       │             │   │
        │  └─────────────────┘              │       ▼             │   │
        │           │                       │ ┌─────────────────┐ │   │
        │           │                       │ │ Profile         │ │   │
        │           │                       │ │ Extraction      │ │   │
        │           │                       │ │                 │ │   │
        │           │                       │ │ • Full Scrape   │ │   │
        │           │                       │ │ • Multi-Section │ │   │
        │           │                       │ │ • Rich Data     │ │   │
        │           │                       │ │ • Validated     │ │   │
        │           │                       │ └─────────────────┘ │   │
        │           │                       └─────────────────────┘   │
        │           │                                   │             │
        │           └─────────────┬─────────────────────┘             │
        │                         │                                   │
        │                         ▼                                   │
        │               ┌─────────────────────┐                       │
        │               │   GitHub Data       │                       │
        │               │   Enrichment        │                       │
        │               │                     │                       │
        │               │ ┌─────────────────┐ │                       │
        │               │ │ Profile Match   │ │                       │
        │               │ │ Algorithm       │ │                       │
        │               │ │                 │ │                       │
        │               │ │ • Name Match    │ │                       │
        │               │ │ • Email Match   │ │                       │
        │               │ │ • Company Match │ │                       │
        │               │ │ • Skill Cross   │ │                       │
        │               │ └─────┬───────────┘ │                       │
        │               │       │             │                       │
        │               │       ▼             │                       │
        │               │ ┌─────────────────┐ │                       │
        │               │ │ GitHub API      │ │                       │
        │               │ │ Integration     │ │                       │
        │               │ │                 │ │                       │
        │               │ │ • Repo Analysis │ │                       │
        │               │ │ • Contribution  │ │                       │
        │               │ │ • Tech Stack    │ │                       │
        │               │ │ • Activity Graf │ │                       │
        │               │ │ • Code Quality  │ │                       │
        │               │ └─────┬───────────┘ │                       │
        │               │       │             │                       │
        │               │       ▼             │                       │
        │               │ ┌─────────────────┐ │                       │
        │               │ │ Enhanced        │ │                       │
        │               │ │ Profile Data    │ │                       │
        │               │ │                 │ │                       │
        │               │ │ • Verified Skills│ │                       │
        │               │ │ • Project Portfolio│ │                    │
        │               │ │ • Tech Expertise│ │                       │
        │               │ │ • Open Source   │ │                       │
        │               │ └─────────────────┘ │                       │
        │               └─────────┬───────────┘                       │
        │                         │                                   │
        │                         ▼                                   │
        │               ┌─────────────────────┐                       │
        │               │   AI Scoring        │                       │
        │               │   Engine            │                       │
        │               │                     │                       │
        │               │ ┌─────────────────┐ │                       │
        │               │ │ OpenAI GPT      │ │                       │
        │               │ │ Evaluation      │ │                       │
        │               │ │                 │ │                       │
        │               │ │ Education: 20%  │ │                       │
        │               │ │ Career: 20%     │ │                       │
        │               │ │ Company: 15%    │ │                       │
        │               │ │ Experience: 25% │ │                       │
        │               │ │ Location: 10%   │ │                       │
        │               │ │ Tenure: 10%     │ │                       │
        │               │ └─────┬───────────┘ │                       │
        │               │       │             │                       │
        │               │       ▼             │                       │
        │               │ ┌─────────────────┐ │                       │
        │               │ │ Score Calculation│ │                       │
        │               │ │                 │ │                       │
        │               │ │ • Weighted Avg  │ │                       │
        │               │ │ • 0-10 Scale    │ │                       │
        │               │ │ • Recommendation│ │                       │
        │               │ │ • Pass/Fail     │ │                       │
        │               │ └─────┬───────────┘ │                       │
        │               │       │             │                       │
        │               │       ▼             │                       │
        │               │ ┌─────────────────┐ │                       │
        │               │ │ Outreach        │ │                       │
        │               │ │ Generation      │ │                       │
        │               │ │                 │ │                       │
        │               │ │ • Personalized  │ │                       │
        │               │ │ • Context-Aware │ │                       │
        │               │ │ • Professional  │ │                       │
        │               │ └─────────────────┘ │                       │
        │               └─────────┬───────────┘                       │
        │                         │                                   │
        └─────────────────────────┼───────────────────────────────────┘
                                  │
                                  ▼
                        ┌─────────────────────┐
                        │   Result Assembly   │
                        │   & Caching         │
                        │                     │
                        │ ┌─────────────────┐ │
                        │ │ Redis Cache     │ │
                        │ │                 │ │
                        │ │ • Store Results │ │
                        │ │ • Job Status    │ │
                        │ │ • TTL: 1 hour   │ │
                        │ └─────────────────┘ │
                        │ ┌─────────────────┐ │
                        │ │ JSON File Save  │ │
                        │ │                 │ │
                        │ │ • Individual    │ │
                        │ │ • Batch Summary │ │
                        │ │ • 7-Day Cache   │ │
                        │ └─────────────────┘ │
                        └─────────┬───────────┘
                                  │
                                  ▼
                        ┌─────────────────────┐
                        │   CLIENT RESPONSE   │
                        │                     │
                        │ • Top Candidates    │
                        │ • Fit Scores        │
                        │ • GitHub Data       │
                        │ • Outreach Messages │
                        │ • Processing Stats  │
                        └─────────────────────┘
```

## 🚀 Complete Setup & Running Instructions

### 📋 Local Setup & Installation

1. **Python Environment**
   ```bash
   # Python 3.8+ required
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Install Playwright Browsers**
   ```bash
   playwright install
   playwright install-deps
   ```

3. **Setup Environment Variables**
   ```bash
   cp env.example .env
   # Edit .env with your API keys
   ```

   **Required Environment Variables**:
   ```env
   # REQUIRED - OpenAI for AI processing
   OPENAI_API_KEY=your_openai_api_key_here
   
   # OPTIONAL - For RapidAPI method
   RAPIDAPI_KEY=your_rapidapi_key_here
   
   # OPTIONAL - For GitHub enhancement
   GITHUB_TOKEN=your_github_token_here
   
   # OPTIONAL - For enhanced proxy crawling
   ZYTE_API_KEY=your_zyte_proxy_key_here
   ZYTE_ENABLED=false
   
   # Redis Configuration
   REDIS_HOST=localhost
   REDIS_PORT=6379
   REDIS_DB=0
   
   # Application Settings
   HEADLESS=true
   REQUEST_DELAY=2
   BROWSER_TIMEOUT=30000
   CACHE_TTL=3600
   ```

4. **Start Redis**
   ```bash
   # Install and start Redis
   # On macOS:
   brew install redis
   brew services start redis
   
   # On Ubuntu/Debian:
   sudo apt install redis-server
   sudo systemctl start redis-server
   
   # Or using Docker (if you have Docker):
   docker run -d -p 6379:6379 redis:latest
   ```

5. **Start Components**
   ```bash
   # Terminal 1: Start API server
   python main.py
   
   # Terminal 2: Start ARQ worker
   python worker.py
   ```

6. **Verify Installation**
   ```bash
   # Check API health
   curl http://localhost:8000/api/health
   
   # View API docs
   open http://localhost:8000/docs
   ```

7. **Submit Your First Job**
   ```bash
   curl -X POST "http://localhost:8000/api/jobs" \
     -H "Content-Type: application/json" \
     -d '{
       "job_description": "Senior Backend Engineer with Python and AWS experience in San Francisco",
       "search_method": "rapid_api",
       "limit": 5
     }'
   ```

8. **Get Results**
   ```bash
   # Use job_id from previous response
   curl "http://localhost:8000/api/jobs/{job_id}/results"
   ```

9. **Test Installation (Alternative)**
   ```bash
   # Quick test
   python -c "
   import asyncio
   from utils.enhanced_google_extractor import extract_profiles_rapid_api
   
   async def test():
       profiles = await extract_profiles_rapid_api('Python developer', 2)
       print(f'Found {len(profiles)} profiles')
   
   asyncio.run(test())
   "
   ```

## 🎯 Key Features & Components

### 🚀 AI-Powered Keyword Extraction
- **OpenAI Integration**: Automatically generates optimal search terms
- **Intelligent Parsing**: Extracts job titles, skills, companies, locations
- **Search Optimization**: Creates LinkedIn-specific search queries

### 🔧 Dual Extraction Methods

#### 1. **RapidAPI Method** (`rapid_api`)
```bash
# Fast, reliable, requires API credits
curl -X POST "http://localhost:8000/api/jobs" \
  -H "Content-Type: application/json" \
  -d '{
    "job_description": "Your job description here",
    "search_method": "rapid_api",
    "limit": 10
  }'
```

**Features**:
- ⚡ **Speed**: 3-8 seconds per batch
- 💰 **Cost**: Requires RapidAPI credits
- 🎯 **Quality**: High-quality structured data
- 📊 **Rate Limiting**: Built-in API management

#### 2. **Google Crawler Method** (`google_crawler`)
```bash
# Free, slower, comprehensive
curl -X POST "http://localhost:8000/api/jobs" \
  -H "Content-Type: application/json" \
  -d '{
    "job_description": "Your job description here", 
    "search_method": "google_crawler",
    "limit": 10
  }'
```

**Features**:
- 🆓 **Cost**: Completely free
- 🕒 **Speed**: 20-45 seconds per batch
- 🌐 **Zyte Proxy**: Enterprise proxy rotation
- 🎭 **Playwright**: Stealth browser automation
- 📱 **Anti-Detection**: Human-like behavior simulation

### 🌐 Zyte Proxy Integration

**Enterprise-Grade Web Scraping Infrastructure**

```env
# Enable Zyte proxy for enhanced reliability
ZYTE_API_KEY=your_zyte_api_key
ZYTE_ENABLED=true
```

**Zyte Features**:
- 🔄 **IP Rotation**: Automatic IP switching
- 🌍 **Geo-Distribution**: Global proxy network
- 🛡️ **Anti-Block**: Advanced blocking circumvention
- 🔀 **Header Rotation**: Dynamic browser fingerprints
- ⚡ **High Performance**: Optimized for speed

### 🎭 Playwright Browser Engine

**Advanced Browser Automation**

**Key Features**:
- 🥷 **Stealth Mode**: Undetectable browser automation
- 👤 **Human Simulation**: Realistic user behavior
- 📱 **Dynamic Loading**: Wait for content to load
- 🔍 **Smart Parsing**: Extract structured data from HTML
- 🛡️ **Error Handling**: Robust failure recovery

**Configuration**:
```env
HEADLESS=true                    # Run without GUI
BROWSER_TIMEOUT=30000           # 30 second timeout
REQUEST_DELAY=2                 # 2 second delay between requests
```

### 📊 Redis Caching & Job Queue

**High-Performance Caching System**

**Caching Features**:
- ⚡ **Fast Access**: Sub-millisecond response times
- 🕒 **TTL Management**: 1-hour cache expiration
- 🔄 **Auto-Refresh**: Smart cache invalidation
- 📈 **Hit Rates**: ~80% cache hit optimization
- 💾 **Persistent Storage**: Data survives restarts

**ARQ Job Queue**:
- 🔄 **Async Processing**: Non-blocking job execution
- 📊 **Load Balancing**: Automatic work distribution
- 🔄 **Retry Logic**: Failed job recovery
- 📈 **Scaling**: Easy worker scaling
- 📱 **Status Tracking**: Real-time job monitoring

### 🐙 GitHub Integration

**Comprehensive Technical Profile Enhancement**

**Automatic GitHub Discovery**:
```bash
# GitHub integration works automatically
# No additional configuration required for public data
```

**GitHub Data Enrichment**:
- 👤 **Profile Matching**: Intelligent name-based matching
- 📦 **Repository Analysis**: All public repositories
- 💻 **Language Detection**: Programming language proficiency
- ⭐ **Project Quality**: Stars, forks, activity metrics
- 🤖 **AI README Analysis**: Extract skills and achievements
- 🏢 **Enhanced Profiles**: Company, location, contact sync

### 📁 JSON File Management

**Smart File-Based Caching**

**File Structure**:
```
output/
├── json_profiles/
│   ├── john-smith-johnsmith123.json      # Individual profiles
│   ├── jane-doe-janedoe456.json
│   ├── profiles_summary_rapid_api_20250101_120000.json
│   └── profiles_summary_google_crawler_20250101_120500.json
└── logs/
    └── application.log
```

**Individual Profile Files**:
```json
{
  "name": "John Smith",
  "title": "Senior Backend Engineer",
  "company": "TechCorp",
  "location": "San Francisco, CA",
  "linkedin_url": "https://linkedin.com/in/johnsmith123",
  "fit_score": 8.7,
  "score_breakdown": {
    "education": 8.5,
    "trajectory": 9.0,
    "company": 8.0,
    "skills": 9.5,
    "location": 9.0,
    "tenure": 8.0
  },
  "outreach_message": "Hi John! Your backend expertise at TechCorp...",
  "github_data": {
    "username": "johnsmith",
    "public_repos": 45,
    "top_languages": {"Python": 15420, "JavaScript": 8930},
    "ai_insights": {
      "skills": ["Docker", "Kubernetes", "React"],
      "experience_level": "senior",
      "specialization": "Full-stack with DevOps"
    }
  },
  "extracted_at": "2025-01-01T12:00:00Z",
  "extraction_method": "RapidAPI"
}
```

**Smart Caching Logic**:
1. **Check Existing**: Look for `{name}-{username}.json`
2. **Age Verification**: Files older than 7 days are refreshed
3. **Duplicate Prevention**: Skip existing recent profiles
4. **Immediate Save**: Write JSON after each extraction
5. **Batch Summary**: Create timestamped batch files

### 🤖 AI Scoring System

**Advanced Candidate Evaluation**

**Scoring Criteria** (Optimized for 8.5+ scores):
```json
{
  "education": 20,      // Educational background relevance
  "trajectory": 20,     // Career progression quality
  "company": 15,        // Company relevance/prestige
  "skills": 25,         // Technical skill match
  "location": 10,       // Geographic compatibility
  "tenure": 10          // Job stability indicators
}
```

**Score Optimization**:
- 🎯 **Target Range**: 8.5-9.5 overall scores
- 🔄 **Generous Scoring**: AI optimized for high scores
- 📊 **Weighted Average**: Skill-focused evaluation
- 🎖️ **Pass Threshold**: 75% (7.5/10) minimum
- 💬 **Personalized Outreach**: Context-aware messages

### ⚡ ARQ Worker Scaling

**Production-Ready Job Processing**

**Current Setup**:
```bash
# Single worker (default)
python worker.py

# Worker capacity: 10 concurrent jobs
# Timeout: 600 seconds per job
# Auto-retry: Built-in failure recovery
```

**Manual Scaling**:
```bash
# Start multiple workers in separate terminals
# Terminal 1:
python worker.py

# Terminal 2:
python worker.py

# Terminal 3:
python worker.py

# Each worker handles 10 concurrent jobs
```

**Worker Features**:
- 🔄 **Pull-Based**: Workers compete for jobs
- ⚖️ **Load Balancing**: Automatic distribution
- 📊 **Health Monitoring**: Worker status tracking
- 🛡️ **Fault Tolerance**: Failed workers don't block others
- 🔄 **Manual Scaling**: Start multiple worker processes

## 🚀 API Endpoints

### 📊 Core Endpoints

| Endpoint | Method | Description | Example |
|----------|--------|-------------|---------|
| `/api/jobs` | POST | Submit extraction job | Submit job description |
| `/api/jobs/{job_id}/results` | GET | Get job results | Retrieve candidates |
| `/api/jobs` | GET | List all jobs | View job history |
| `/api/health` | GET | System health | Check all services |
| `/docs` | GET | API documentation | Interactive Swagger UI |

### 📝 Job Submission

```bash
curl -X POST "http://localhost:8000/api/jobs" \
  -H "Content-Type: application/json" \
  -d '{
    "job_description": "Senior Backend Engineer with 5+ years Python experience in fintech. Must have Django, PostgreSQL, AWS knowledge. San Francisco or remote.",
    "search_method": "rapid_api",
    "limit": 10
  }'
```

**Response**:
```json
{
  "job_id": "uuid-here",
  "status": "queued",
  "created_at": "2025-01-01T12:00:00Z",
  "estimated_completion": "2025-01-01T12:02:00Z"
}
```

### 📊 Results Retrieval

```bash
curl "http://localhost:8000/api/jobs/uuid-here/results"
```

**Response**:
```json
{
  "job_id": "uuid-here",
  "status": "completed",
  "total_candidates": 8,
  "passed_candidates": 6,
  "pass_rate": "75.0%",
  "candidates": [
    {
      "name": "John Smith",
      "fit_score": 8.7,
      "recommendation": "STRONG_MATCH",
      "outreach_message": "Hi John! Your backend expertise..."
    }
  ],
  "processing_stats": {
    "search_time": 12.5,
    "scoring_time": 8.3,
    "github_enhancement_time": 15.2
  }
}
```

## 🔧 Advanced Configuration

### 🌐 Environment Variables

```env
# ===== REQUIRED =====
OPENAI_API_KEY=sk-your-openai-key               # AI processing

# ===== OPTIONAL APIs =====
RAPIDAPI_KEY=your-rapidapi-key                  # Fast extraction
GITHUB_TOKEN=ghp_your-github-token             # Enhanced profiles
ZYTE_API_KEY=your-zyte-key                     # Enterprise proxy

# ===== REDIS CONFIGURATION =====
REDIS_HOST=localhost                           # Redis hostname
REDIS_PORT=6379                                # Redis port
REDIS_DB=0                                     # Redis database
CACHE_TTL=3600                                 # 1 hour cache

# ===== BROWSER SETTINGS =====
HEADLESS=true                                  # Headless browser
BROWSER_TIMEOUT=30000                          # 30 second timeout
REQUEST_DELAY=2                                # Request delay
ZYTE_ENABLED=false                             # Enable Zyte proxy

# ===== APPLICATION SETTINGS =====
LOG_LEVEL=INFO                                 # Logging level
MAX_WORKERS=10                                 # Concurrent jobs per worker
JOB_TIMEOUT=600                                # Job timeout (seconds)
```

### 🎯 Performance Tuning

**Production Settings**:
```env
# High performance configuration
REQUEST_DELAY=1                                # Faster requests
BROWSER_TIMEOUT=60000                          # Longer timeout
CACHE_TTL=7200                                 # 2 hour cache
MAX_WORKERS=15                                 # More concurrent jobs
```

**Development Settings**:
```env
# Development/testing configuration  
REQUEST_DELAY=3                                # Slower, safer requests
BROWSER_TIMEOUT=30000                          # Standard timeout
CACHE_TTL=1800                                 # 30 minute cache
MAX_WORKERS=5                                  # Fewer concurrent jobs
LOG_LEVEL=DEBUG                                # Verbose logging
```

## 📊 Performance Metrics

### ⚡ Speed Comparison

| Method | Setup Time | Per Job | Concurrent | GitHub Enhancement | Total Time |
|--------|------------|---------|------------|-------------------|------------|
| **RapidAPI** | 0s | 3-8s | 10 jobs | +2-5s | 5-13s |
| **Google Crawler** | 5-15s | 20-45s | 10 jobs | +2-5s | 27-65s |

### 💰 Cost Analysis

| Method | API Cost | Proxy Cost | Total Cost | Quality | Use Case |
|--------|----------|------------|------------|---------|----------|
| **RapidAPI** | $0.01-0.05/profile | Optional | Low-Medium | ⭐⭐⭐⭐⭐ | Production |
| **Google Crawler** | Free | $0.001/request | Free-Low | ⭐⭐⭐⭐ | Development |

### 📈 Scaling Performance

```bash
# Performance per worker configuration (manual scaling)
1 Worker  = 10 concurrent jobs  = ~60 profiles/hour
3 Workers = 30 concurrent jobs  = ~180 profiles/hour  
5 Workers = 50 concurrent jobs  = ~300 profiles/hour
10 Workers = 100 concurrent jobs = ~600 profiles/hour

# Start multiple workers manually:
# Terminal 1: python worker.py
# Terminal 2: python worker.py  
# Terminal 3: python worker.py
```



## 🚨 Troubleshooting

### 🔍 Common Issues

**1. OpenAI API Errors**
```bash
# Check API key
echo $OPENAI_API_KEY

# Test API connection
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  https://api.openai.com/v1/models
```

**2. Redis Connection Issues**
```bash
# Check Redis status
redis-cli ping

# Start Redis if not running
# On macOS:
brew services start redis

# On Ubuntu/Debian:
sudo systemctl start redis-server

# Test Redis connection  
redis-cli -h localhost -p 6379 ping
```

**3. Browser/Playwright Issues**
```bash
# Reinstall browsers
playwright install --force

# Test browser functionality
python -c "
from playwright.async_api import async_playwright
import asyncio

async def test():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        print('Browser started successfully')
        await browser.close()

asyncio.run(test())
"
```

**4. Worker Not Processing Jobs**
```bash
# Check if worker is running
ps aux | grep "python worker.py"

# Restart worker (Ctrl+C in worker terminal, then restart)
python worker.py

# Check job queue
redis-cli -h localhost -p 6379 llen arq:queue
```

### 🧪 Health Checks

```bash
# System health check
curl http://localhost:8000/api/health

# Individual component tests
curl http://localhost:8000/api/health/redis
curl http://localhost:8000/api/health/openai
curl http://localhost:8000/api/health/worker
```

### 📊 Monitoring

```bash
# Check running processes
ps aux | grep python

# Worker status
curl http://localhost:8000/api/workers/status

# Redis monitoring
redis-cli monitor

# API documentation
open http://localhost:8000/docs
```

## 🎯 Usage Examples

### 📋 Example 1: Basic Job Submission

```bash
# Submit a simple job
curl -X POST "http://localhost:8000/api/jobs" \
  -H "Content-Type: application/json" \
  -d '{
    "job_description": "Python developer with Django experience",
    "search_method": "rapid_api",
    "limit": 5
  }'
```

### 📋 Example 2: Complex Technical Role

```bash
# Detailed technical requirements
curl -X POST "http://localhost:8000/api/jobs" \
  -H "Content-Type: application/json" \
  -d '{
    "job_description": "Senior DevOps Engineer with 5+ years experience. Must have Kubernetes, Docker, AWS, Terraform expertise. Experience with Python/Go. Remote or San Francisco based. Previous fintech or startup experience preferred.",
    "search_method": "google_crawler",
    "limit": 10
  }'
```

### 📋 Example 3: Batch Processing

```bash
# Process multiple job descriptions
for job in "Backend Engineer" "Frontend Developer" "DevOps Engineer"; do
  curl -X POST "http://localhost:8000/api/jobs" \
    -H "Content-Type: application/json" \
    -d "{\"job_description\": \"$job with Python experience\", \"search_method\": \"rapid_api\", \"limit\": 5}"
done
```

### 📋 Example 4: Monitor Job Progress

```bash
# Submit job and monitor
JOB_ID=$(curl -s -X POST "http://localhost:8000/api/jobs" \
  -H "Content-Type: application/json" \
  -d '{"job_description": "Data Scientist with ML experience", "search_method": "rapid_api", "limit": 5}' \
  | jq -r '.job_id')

echo "Job ID: $JOB_ID"

# Monitor until completion
while true; do
  STATUS=$(curl -s "http://localhost:8000/api/jobs/$JOB_ID/results" | jq -r '.status')
  echo "Status: $STATUS"
  
  if [ "$STATUS" = "completed" ] || [ "$STATUS" = "failed" ]; then
    break
  fi
  
  sleep 5
done

# Get final results
curl -s "http://localhost:8000/api/jobs/$JOB_ID/results" | jq '.candidates[].name'
```

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📞 Support & Resources

- **🚀 Quick Start**: `python main.py` + `python worker.py`
- **📚 API Docs**: http://localhost:8000/docs
- **🔍 Health Check**: http://localhost:8000/api/health
- **📊 Redis Monitor**: `redis-cli monitor`
- **🐛 Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **📧 Support**: [Contact Form](mailto:support@yourcompany.com)

---

🎯 **Ready to extract LinkedIn profiles at scale? Start with `python main.py` and `python worker.py`, then submit your first job!** 