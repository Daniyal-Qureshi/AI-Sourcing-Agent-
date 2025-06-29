# LinkedIn Profile Sourcing Agent

An AI-powered system for finding, extracting, scoring, and generating outreach for LinkedIn profiles based on job descriptions. **Now with fully integrated scalable worker system!**

## 🚀 What's New - Worker Integration

### ✅ **Complete API Integration**
The worker system is now **fully integrated** into the main API flow:

- **Default Processing**: All jobs now use the worker system by default
- **Backward Compatibility**: Legacy processing available as fallback
- **Smart Caching**: Username-based file naming with 7-day freshness validation
- **Outreach Generation**: Automatic personalized message creation
- **Real-time Monitoring**: Track job progress through multiple pipeline stages

### 🔄 **Processing Flow**
```
Job Submission → Worker Pipeline → Results
     ↓              ↓                ↓
   API Call    1. Search Workers    Cached Data
                2. Extract Workers   + Outreach
                3. Outreach Workers  + Scoring
```

## 🆕 New Two-Phase Approach

### **Revolutionary Optimization for Large-Scale Processing**

The system now supports a **NEW two-phase approach** that dramatically improves efficiency for large-scale LinkedIn profile processing:

#### **Phase 1: HTML Scraping** 🕷️
- Gets LinkedIn URLs from Google search
- Scrapes **all** profile HTML pages in batch
- **Closes browser immediately** after scraping
- Smart duplicate detection (skips existing files)

#### **Phase 2: Data Processing** 🔄
- Processes HTML files **without opening browser**
- Extracts structured profile data
- No network requests needed
- Can be run multiple times safely

### **Key Benefits:**

✅ **Efficiency**: Browser only open during scraping phase  
✅ **Smart Caching**: Checks for existing HTML/JSON files by username  
✅ **No Duplicates**: Skips already-processed profiles automatically  
✅ **File Organization**: Clean username-based naming (`username.html`, `username.json`)  
✅ **Separation of Concerns**: Scraping vs. processing completely separated  
✅ **Recovery**: Can reprocess HTML files without re-scraping  

### **Usage:**

```python
# Option 1: Use the integrated two-phase workflow
from utils.enhanced_workflow import search_with_playwright_two_phase_and_score

search_result, scoring_result = await search_with_playwright_two_phase_and_score(
    job_description="Senior Python Developer in San Francisco",
    limit=10
)

# Option 2: Manual phase separation for maximum control
from utils.profile_extractor import scrape_html_only, process_html_files

# Phase 1: Scrape HTML (browser opens and closes)
html_results = await scrape_html_only(profile_urls, use_login=True)

# Phase 2: Process HTML files (no browser needed)
usernames = [r['username'] for r in html_results['results'] if r['success']]
profiles = process_html_files(usernames)
```

### **API Support:**

The two-phase approach is available via the API:

```bash
# Use the new two-phase method
POST /api/jobs
{
  "job_description": "Senior Python Developer...",
  "search_method": "playwright_two_phase",  # <- NEW METHOD
  "limit": 10
}
```

**Search Method Options:**
- `"rapid_api"` - Uses RapidAPI (fast, requires credits)
- `"playwright"` - Legacy single-phase browser automation  
- `"playwright_two_phase"` - **NEW** optimized two-phase approach

---

## 🛠 Core Components

### 1. **Enhanced API Endpoints**

**Main Job Processing (Worker-Integrated):**
```bash
# Submit job with worker system (recommended)
POST /api/jobs
{
  "job_description": "Senior Python Developer...",
  "search_method": "rapid_api",
  "limit": 10,
  "use_workers": true  # Default: true
}

# Advanced worker pipeline with outreach
POST /api/jobs/worker-pipeline  
{
  "job_description": "Senior Python Developer...",
  "search_method": "rapid_api",
  "limit": 10,
  "generate_outreach": true
}

# Legacy processing (fallback)
POST /api/jobs/legacy
{
  "job_description": "Senior Python Developer...",
  "search_method": "rapid_api",
  "limit": 5
}
```

**Worker System Monitoring:**
```bash
# Check worker system status
GET /api/workers/status

# Monitor specific worker task
GET /api/workers/tasks/{task_id}

# Direct worker control
POST /api/workers/direct/search
POST /api/workers/direct/extract  
POST /api/workers/direct/outreach
POST /api/workers/direct/pipeline
```

### 2. **Smart Processing Pipeline**

**Stage 1: Profile Search** (15% progress)
- Uses Rapid API or Google search via workers
- Finds LinkedIn profile URLs
- Caches search results

**Stage 2: Profile Extraction** (40-75% progress)  
- Smart caching check (username-based files)
- Validates data freshness (< 7 days)
- Extracts only if needed
- Saves as `{username}.html` and `{username}.json`

**Stage 3: Candidate Scoring** (80% progress)
- Evaluates profiles against job requirements
- Assigns scores and pass/fail status
- Generates scoring breakdown

**Stage 4: Outreach Generation** (85-95% progress)
- Creates personalized LinkedIn messages
- Connection requests and direct messages
- Saves outreach data in profile JSON

### 3. **File Organization**
```
output/
├── html_profiles/          # Cleaned HTML files (username-based)
│   ├── john-doe-123.html
│   ├── jane-smith-456.html
│   └── alex-johnson-789.html
└── json_profiles/          # Complete profile data + outreach
    ├── john-doe-123.json   # Profile + outreach messages
    ├── jane-smith-456.json
    └── alex-johnson-789.json
```

**Sample JSON Structure:**
```json
{
  "name": "John Doe",
  "headline": "Senior Python Developer at TechCorp",
  "linkedin_url": "https://linkedin.com/in/john-doe-123",
  "location": "San Francisco, CA",
  "experience": [...],
  "skills": [...],
  "extracted_at": "2024-01-15T10:30:00",
  "username": "john-doe-123",
  "outreach": [
    {
      "message": "Hi John! I came across your profile...",
      "outreach_type": "connection_request",
      "generated_at": "2024-01-15T10:35:00",
      "job_context": "Senior Python Developer position..."
    }
  ]
}
```

### 4. **Intelligent Caching System**

**Cache Flow:**
1. **URL to Username**: Extract username from LinkedIn URL
2. **File Check**: Look for `{username}.json` in cache
3. **Freshness Validation**: Check if data is < 7 days old
4. **Smart Decision**: Use cache or extract fresh data
5. **Storage**: Save with username-based naming

**Benefits:**
- ⚡ **Faster Processing**: Avoid re-extracting recent profiles
- 💰 **Cost Savings**: Reduce API calls and browser automation
- 🎯 **Data Quality**: Fresh data when needed, cached when appropriate
- 📊 **Easy Management**: Clear file naming and organization

## 📊 API Usage Examples

### Basic Job Submission (Worker-Based)
```python
import requests

# Submit job with integrated worker system
response = requests.post("http://localhost:8000/api/jobs", json={
    "job_description": """
    Senior Python Developer
    - 5+ years Python experience  
    - FastAPI/Django expertise
    - San Francisco, CA
    """,
    "search_method": "rapid_api",
    "limit": 10,
    "use_workers": True  # Uses worker pipeline
})

job = response.json()
job_id = job['job_id']

# Monitor progress
while True:
    status_response = requests.get(f"http://localhost:8000/api/jobs/{job_id}/status")
    status = status_response.json()
    
    print(f"Progress: {status['progress']}% - {status['message']}")
    
    if status['status'] == 'completed':
        break
    time.sleep(5)

# Get results
results = requests.get(f"http://localhost:8000/api/jobs/{job_id}/results").json()
print(f"Found {results['total_candidates']} candidates")
```

### Advanced Worker Pipeline
```python
# Submit job with full worker pipeline
response = requests.post("http://localhost:8000/api/jobs/worker-pipeline", json={
    "job_description": "Machine Learning Engineer with 3+ years experience",
    "search_method": "rapid_api", 
    "limit": 15,
    "generate_outreach": True
})

# This automatically:
# 1. Searches for profiles using workers
# 2. Extracts profile data with smart caching  
# 3. Generates personalized outreach messages
# 4. Saves everything with username-based naming
```

### Direct Worker Control
```python
# Direct search using workers
search_response = requests.post("http://localhost:8000/api/workers/direct/search", json={
    "job_description": "Backend developer",
    "search_method": "rapid_api",
    "limit": 5
})

task_id = search_response.json()['task_id']

# Monitor worker task
task_status = requests.get(f"http://localhost:8000/api/workers/tasks/{task_id}").json()
print(f"Task status: {task_status['status']}")
```

## 🔧 Setup & Installation

### 1. Install Dependencies
```bash
cd linkedin-profile-extractor
pip install -r requirements.txt
```

### 2. Environment Setup
```bash
cp env.example .env
# Edit .env with your API keys
```

### 3. Run the API Server
```bash
python main.py
```

The API server now starts with:
- ✅ **Worker System**: 8 concurrent workers for scalable processing
- ✅ **Smart Caching**: Username-based file management
- ✅ **Outreach Generation**: Automatic personalized messaging
- ✅ **Real-time Monitoring**: Progress tracking and task status

### 4. Test Integration
```bash
python test_worker_integration.py
```

## 🎯 Key Benefits

### **Scalability**
- **8 Concurrent Workers**: Process multiple profiles simultaneously
- **Priority Queue**: Important jobs processed first
- **Automatic Retry**: Failed tasks automatically retried
- **Load Balancing**: Intelligent task distribution

### **Intelligence**
- **Smart Caching**: Avoid unnecessary re-extraction (saves time & money)
- **Freshness Validation**: Ensures data quality with 7-day freshness checks
- **Username-based Naming**: Clear, consistent file organization
- **Context-aware Outreach**: Personalized messages using profile + job data

### **Reliability**
- **Error Handling**: Comprehensive error catching and logging
- **Task Monitoring**: Real-time status tracking for all operations
- **Graceful Shutdown**: Clean worker system shutdown
- **Data Persistence**: All data saved in structured JSON format

### **User Experience**
- **Progress Tracking**: Real-time updates during processing
- **Multiple Processing Options**: Worker, legacy, and direct control
- **Backward Compatibility**: Existing code continues to work
- **Enhanced Results**: Profiles include outreach messages automatically

## 🔄 Migration Guide

### For Existing Users
The API is **backward compatible**. Existing code will automatically use the worker system:

**Before (still works):**
```python
response = requests.post("/api/jobs", json={
    "job_description": "Python developer",
    "search_method": "rapid_api",
    "limit": 5
})
```

**Now Enhanced:**
The same call now automatically:
- ✅ Uses worker system for scalability
- ✅ Implements smart caching
- ✅ Generates outreach messages  
- ✅ Saves with username-based naming

**For Maximum Features:**
```python
response = requests.post("/api/jobs/worker-pipeline", json={
    "job_description": "Python developer", 
    "search_method": "rapid_api",
    "limit": 5,
    "generate_outreach": True
})
```

## 🔮 What's Next

- **AI-Powered Outreach**: GPT integration for smarter messaging
- **A/B Testing**: Message effectiveness tracking
- **CRM Integration**: Export to popular CRM systems
- **Analytics Dashboard**: Visual progress and performance tracking
- **Webhook Notifications**: Real-time updates via webhooks
- **Rate Limiting**: LinkedIn compliance features

---

## 🎉 Summary

The LinkedIn Sourcing Agent now features a **fully integrated worker system** that provides:

✅ **Scalable Processing**: 8 concurrent workers handle multiple profiles  
✅ **Smart Caching**: Username-based files with freshness validation  
✅ **Automatic Outreach**: Personalized LinkedIn messages  
✅ **Real-time Monitoring**: Track progress through pipeline stages  
✅ **Easy Integration**: Works with existing code, enhanced features available  

**Ready to use!** Start the server with `python main.py` and submit jobs to experience intelligent, scalable LinkedIn sourcing.

For detailed testing, run: `python test_worker_integration.py` 