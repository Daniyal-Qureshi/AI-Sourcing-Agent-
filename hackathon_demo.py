#!/usr/bin/env python3
"""
Synapse AI Hackathon Demo Script
Demonstrates the LinkedIn sourcing agent for the Windsurf ML Research Engineer role
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime

# Windsurf job description from the hackathon challenge
WINDSURF_JOB_DESCRIPTION = """
Software Engineer, ML Research at Windsurf (Codeium)

Windsurf is a Forbes AI 50 company building AI-powered developer tools. We're looking for a Software Engineer to join our ML Research team to train LLMs for code generation.

Location: Mountain View, CA
Compensation: $140-300k + equity

About Windsurf:
- Building next-generation AI coding assistants
- Forbes AI 50 company
- Scaling rapidly with world-class engineering team
- Focus on LLM training and optimization for code

Role Responsibilities:
- Train and fine-tune large language models for code generation
- Develop novel architectures for code understanding and generation
- Optimize model performance and inference speed
- Research cutting-edge techniques in AI for software development
- Collaborate with product teams to integrate ML models

Requirements:
- Strong background in machine learning and deep learning
- Experience with PyTorch or TensorFlow
- Knowledge of transformer architectures and LLMs
- Programming skills in Python, with some experience in systems languages
- Understanding of distributed training and model optimization
- PhD in ML/AI or equivalent industry experience preferred
- Experience with code generation, program synthesis, or related areas

Nice to have:
- Previous experience at AI/ML focused companies
- Publications in top-tier ML conferences
- Open source contributions to ML frameworks
- Experience with CUDA and GPU optimization
"""

async def test_hackathon_endpoint():
    """Test the hackathon endpoint with the Windsurf job description"""
    
    print("🚀 Synapse AI Hackathon Demo")
    print("=" * 50)
    print("Testing LinkedIn Sourcing Agent for Windsurf ML Research Engineer role")
    print()
    
    # API endpoint
    url = "http://localhost:8000/api/hackathon/source-candidates"
    
    # Request payload
    payload = {
        "job_description": WINDSURF_JOB_DESCRIPTION,
        "search_method": "rapid_api",  # Use rapid_api for faster demo
        "limit": 10
    }
    
    print(f"📝 Job: Software Engineer, ML Research at Windsurf")
    print(f"🔍 Search Method: {payload['search_method']}")
    print(f"👥 Candidate Limit: {payload['limit']}")
    print()
    
    start_time = time.time()
    
    try:
        async with aiohttp.ClientSession() as session:
            print("🔍 Searching for candidates...")
            
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    # Display results
                    print(f"✅ Search completed in {time.time() - start_time:.1f} seconds")
                    print()
                    print("📊 RESULTS SUMMARY")
                    print("-" * 30)
                    print(f"Candidates found: {result['candidates_found']}")
                    print(f"Average fit score: {result['summary']['average_fit_score']}/10")
                    print(f"Candidates scoring 7+: {result['summary']['candidates_above_7']}")
                    print(f"Processing time: {result['processing_time_seconds']}s")
                    print()
                    
                    print("🎯 TOP CANDIDATES")
                    print("=" * 50)
                    
                    for i, candidate in enumerate(result['top_candidates'], 1):
                        print(f"\n{i}. {candidate['name']} - Score: {candidate['fit_score']}/10")
                        print(f"   LinkedIn: {candidate['linkedin_url']}")
                        print(f"   Key Characteristics:")
                        for char in candidate['key_characteristics']:
                            print(f"   • {char}")
                        
                        print(f"   Score Breakdown:")
                        breakdown = candidate['score_breakdown']
                        print(f"   • Education: {breakdown['education']}/10")
                        print(f"   • Career Trajectory: {breakdown['career_trajectory']}/10") 
                        print(f"   • Company Relevance: {breakdown['company_relevance']}/10")
                        print(f"   • Experience Match: {breakdown['experience_match']}/10")
                        print(f"   • Location Match: {breakdown['location_match']}/10")
                        print(f"   • Tenure: {breakdown['tenure']}/10")
                        
                        print(f"   Outreach Message:")
                        print(f"   \"{candidate['personalized_outreach_message']}\"")
                        print("-" * 50)
                    
                    # Save results to file
                    filename = f"windsurf_candidates_{int(time.time())}.json"
                    with open(filename, 'w') as f:
                        json.dump(result, f, indent=2)
                    print(f"\n💾 Results saved to: {filename}")
                    
                else:
                    error = await response.text()
                    print(f"❌ Error {response.status}: {error}")
                    
    except aiohttp.ClientError as e:
        print(f"❌ Connection error: {e}")
        print("Make sure the FastAPI server is running on localhost:8000")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

async def test_google_crawler_method():
    """Test with Google crawler method as alternative"""
    
    print("\n" + "=" * 50)
    print("🔍 Testing Google Crawler Method (Alternative)")
    print("=" * 50)
    
    url = "http://localhost:8000/api/hackathon/source-candidates"
    
    payload = {
        "job_description": WINDSURF_JOB_DESCRIPTION,
        "search_method": "google_crawler",  # Alternative method
        "limit": 5  # Smaller limit for demo
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            print("🔍 Searching with Google crawler...")
            
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Google crawler found {result['candidates_found']} candidates")
                    print(f"📊 Average score: {result['summary']['average_fit_score']}/10")
                    
                    if result['top_candidates']:
                        best_candidate = result['top_candidates'][0]
                        print(f"🏆 Best candidate: {best_candidate['name']} ({best_candidate['fit_score']}/10)")
                else:
                    print(f"❌ Google crawler error: {response.status}")
                    
    except Exception as e:
        print(f"❌ Google crawler test failed: {e}")

def display_hackathon_info():
    """Display hackathon submission information"""
    
    print("\n" + "🏆" * 50)
    print("SYNAPSE AI HACKATHON SUBMISSION READY!")
    print("🏆" * 50)
    print()
    print("✅ Requirements Implemented:")
    print("  • LinkedIn Profile Finding (RapidAPI + Google Crawler)")
    print("  • AI-Powered Candidate Scoring (6 categories)")  
    print("  • Personalized Outreach Generation")
    print("  • Scalable Architecture (Redis + ARQ workers)")
    print("  • FastAPI Endpoint: /api/hackathon/source-candidates")
    print()
    print("🚀 Bonus Features:")
    print("  • Multi-source enhancement (GitHub integration)")
    print("  • Smart caching (7-day profile freshness)")
    print("  • Batch processing (up to 10 jobs in parallel)")
    print("  • AI keyword extraction from job descriptions")
    print()
    print("📋 Submission Checklist:")
    print("  ✅ Code in GitHub repository")
    print("  ⏳ README with setup instructions")
    print("  ⏳ Demo video (3 minutes max)")
    print("  ⏳ Brief write-up (500 words max)")
    print("  ✅ API endpoint hosted (this script tests it)")
    print()
    print("🎯 API Usage:")
    print(f"  POST http://localhost:8000/api/hackathon/source-candidates")
    print(f"  Body: {{\"job_description\": \"...\", \"limit\": 10}}")
    print()

if __name__ == "__main__":
    print("Starting Synapse AI Hackathon Demo...")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Run the demo
    asyncio.run(test_hackathon_endpoint())
    
    # Test alternative method
    asyncio.run(test_google_crawler_method())
    
    # Display submission info
    display_hackathon_info()
    
    print("\n🎉 Demo completed! Ready for hackathon submission.") 