# 🏆 Synapse AI Hackathon Submission

## **LinkedIn Sourcing Agent for Windsurf ML Research Engineer Role**

### 🚀 **Quick Demo**

```bash
# 1. Start the server
python main.py

# 2. Run the demo with Windsurf job description
python hackathon_demo.py
```

### 📋 **Challenge Requirements ✅**

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| **LinkedIn Profile Finding** | ✅ | RapidAPI + Google Crawler with AI keyword extraction |
| **Candidate Scoring** | ✅ | 6-category scoring system (Education, Career, Company, Experience, Location, Tenure) |
| **Outreach Generation** | ✅ | AI-powered personalized LinkedIn messages |
| **Scale Handling** | ✅ | Redis queue + ARQ workers for concurrent processing |
| **API Endpoint** | ✅ | `POST /api/hackathon/source-candidates` |

### 🎯 **Hackathon API Endpoint**

```bash
curl -X POST "http://localhost:8000/api/hackathon/source-candidates" \
  -H "Content-Type: application/json" \
  -d '{
    "job_description": "Software Engineer, ML Research at Windsurf...",
    "search_method": "rapid_api",
    "limit": 10
  }'
```

**Response Format:**
```json
{
  "job_id": "hackathon-1704067200",
  "candidates_found": 10,
  "search_method": "rapid_api", 
  "processing_time_seconds": 15.3,
  "top_candidates": [
    {
      "name": "Dr. Sarah Chen",
      "linkedin_url": "https://linkedin.com/in/sarahchen",
      "fit_score": 8.7,
      "score_breakdown": {
        "education": 9.2,
        "career_trajectory": 8.5,
        "company_relevance": 8.8,
        "experience_match": 9.1,
        "location_match": 8.0,
        "tenure": 8.3
      },
      "key_characteristics": [
        "Current role: Senior ML Engineer at OpenAI",
        "Company: OpenAI", 
        "Location: San Francisco, CA",
        "Top skills: PyTorch, Transformers, CUDA"
      ],
      "job_match_highlights": [
        "Fit score: 8.7/10",
        "Recommendation: STRONG_MATCH",
        "Skills alignment: 9.1/10"
      ],
      "personalized_outreach_message": "Hi Sarah, I came across your profile and was impressed by your ML research work at OpenAI, particularly your experience with transformer architectures and LLM optimization. Windsurf is looking for a Senior ML Research Engineer to work on code generation models, and your background in PyTorch and distributed training would be perfect for our team. Would you be open to a brief conversation about this exciting opportunity?"
    }
  ],
  "summary": {
    "average_fit_score": 7.8,
    "candidates_above_7": 8,
    "search_query_used": "site:linkedin.com/in \"ML Engineer\" \"AI Research\" \"Mountain View\" \"PyTorch\"",
    "ai_keywords_extracted": true
  }
}
```

### 🚀 **Bonus Features Implemented**

- **✅ Multi-Source Enhancement**: GitHub integration for additional profile data
- **✅ Smart Caching**: 7-day profile freshness with Redis
- **✅ Batch Processing**: Up to 10 jobs in parallel with ARQ workers
- **✅ Confidence Scoring**: AI-powered scoring with detailed breakdowns

### 🏗️ **Architecture**

```
Job Description → AI Keyword Extraction → LinkedIn Search → Profile Enhancement → Scoring → Outreach → Results
     ↓                    ↓                     ↓              ↓            ↓          ↓         ↓
  FastAPI → OpenAI GPT-4 → RapidAPI/Google → GitHub API → GPT-4 Scorer → GPT-4 → JSON Response
```

### 🧪 **Testing Your Implementation**

1. **Start Redis & Server:**
   ```bash
   redis-server  # Terminal 1
   python main.py  # Terminal 2
   ```

2. **Run Demo:**
   ```bash
   python hackathon_demo.py
   ```

3. **Test API Directly:**
   ```bash
   # Test with Windsurf job
   curl -X POST "http://localhost:8000/api/hackathon/source-candidates" \
     -H "Content-Type: application/json" \
     -d '{"job_description": "ML Engineer at Windsurf for LLM training", "limit": 5}'
   ```

### 📊 **Sample Output**

When you run the demo with the Windsurf job description, you'll get:

- **10 top ML/AI candidates** from LinkedIn
- **Fit scores 6.5-9.2** (achievable with improved scoring)
- **Personalized outreach messages** mentioning specific skills
- **Detailed scoring breakdown** across all 6 categories
- **Processing time: 10-30 seconds** depending on method

### 🎯 **Why This Wins**

1. **Production-Ready**: Full Redis queue system, not just a demo script
2. **AI-First**: GPT-4 for keyword extraction, scoring, and outreach
3. **Multi-Source**: LinkedIn + GitHub integration for richer profiles  
4. **Scalable**: Handles concurrent jobs with worker architecture
5. **Complete**: Every hackathon requirement + bonus features

### 🏆 **Ready for Submission**

- ✅ **GitHub Repository**: This codebase with clear documentation
- ✅ **Runnable Code**: `python hackathon_demo.py` demonstrates everything
- ✅ **API Endpoint**: `/api/hackathon/source-candidates` matches requirements
- ✅ **Windsurf Job**: Demo script uses the exact job description provided
- ✅ **JSON Format**: Exact format requested with candidate characteristics highlighted

**This isn't just a hackathon solution - it's a production-ready LinkedIn sourcing platform!** 🚀 