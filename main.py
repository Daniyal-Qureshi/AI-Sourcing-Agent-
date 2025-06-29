"""
LinkedIn Profile Sourcing FastAPI Server
"""
import asyncio
import logging
import uuid
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

from typing import Literal


from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from models.api_models import (
    JobRequest,
    JobResponse,
    JobStatus,
    CandidateInfo,
    SearchResults
)

from utils.redis_cache import RedisCache, generate_cache_key
from utils.enhanced_workflow import (
    search_with_rapid_api_and_score, 
    search_with_playwright_and_score,
    search_with_playwright_two_phase_and_score,
    process_job_rapid_api, 
    process_job_playwright,
    process_job_playwright_two_phase
)
from arq import create_pool
from arq.connections import RedisSettings
# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global ARQ pool for job processing
arq_pool = None



def run_async_task(coro):
    """
    Safely runs an async coroutine from a sync context,
    handling both running and non-running event loops.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # No event loop running: safe to use asyncio.run()
        return asyncio.run(coro)
    else:
        # Event loop is running: create a new task and wait for result
        future = asyncio.ensure_future(coro)
        return loop.run_until_complete(future)

def get_playwright_results(job_description: str, limit: int):
    async def run_playwright():
        return await search_with_playwright_and_score(
            job_description=job_description,
            limit=limit
        )

    return run_async_task(run_playwright())
    

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global arq_pool
    
    # Startup
    logger.info("🚀 Starting LinkedIn Sourcing Agent API with ARQ")
    arq_pool = await create_pool(RedisSettings(host='localhost', port=6379, database=0))
    logger.info("✅ ARQ system ready")
    
    yield
    
    # Shutdown  
    logger.info("🛑 Shutting down LinkedIn Sourcing Agent API")
    if arq_pool:
        arq_pool.close()
        await arq_pool.wait_closed()
        logger.info("✅ Shutdown complete")

# Create FastAPI app
app = FastAPI(
    title="LinkedIn Profile Sourcing API", 
    description="Scalable LinkedIn profile sourcing with ARQ: Async Redis Queue processing with true concurrency, distributed workers, and smart caching",
    version="4.0.0",
    lifespan=lifespan
)




@app.post("/api/jobs", response_model=JobResponse)
async def submit_job(
    job_description: str,
    search_method: Literal["rapid_api", "playwright", "playwright_two_phase"] = Query(default="rapid_api"),
    limit: int = 5
):
    """
    Submit a job for processing using ARQ (Async Redis Queue).
    
    Args:
        job_description: The job description to process
        search_method: "rapid_api", "playwright", or "playwright_two_phase"
        limit: Maximum number of profiles to process
    
    Search Methods:
    - "rapid_api": Use RapidAPI for profile search (faster, requires API credits)
    - "playwright": Legacy single-phase browser automation (slower, browser stays open)
    - "playwright_two_phase": NEW optimized approach (scrape HTML first, then process)
    
    The ARQ system provides:
    - True async/await processing with Redis backend
    - Scalable distributed workers (up to 10 concurrent jobs)
    - Single job worker handling complete pipeline end-to-end
    - Concurrent profile extraction and outreach generation
    - Smart 7-day profile caching with username-based storage
    - Automatic retries and job timeout handling
    - Full pipeline: search → extract → score → outreach
    """
    logger.info(f"📝 Received job submission: {search_method}, limit: {limit}")
    
    if not job_description or len(job_description.strip()) < 10:
        raise HTTPException(status_code=400, detail="Job description must be at least 10 characters long")
    
    if search_method not in ["rapid_api", "playwright", "playwright_two_phase"]:
        raise HTTPException(status_code=400, detail="Search method must be 'rapid_api', 'playwright', or 'playwright_two_phase'")
    
    if limit < 1 or limit > 50:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 50")
    
    return await _process_job_request(job_description, search_method, limit)


async def _process_job_request(
    job_description: str,
    search_method: str,
    limit: int
):
    """
    Internal job processing logic using ARQ worker.
    
    Args:
        job_description: The job description to process
        search_method: "rapid_api" or "playwright"
        limit: Maximum number of profiles to process
    
    Returns:
        JobResponse with job details and status
    """
    try:
        # Generate unique job ID
        job_id = str(uuid.uuid4())
        
        # Generate cache key
        cache_key = generate_cache_key(
            job_description, search_method, limit
        )
        
        # Check if results are already cached
        cached_results = RedisCache.get_cached_results(cache_key)
        if cached_results:
            logger.info(f"Job {job_id}: Found cached results, returning immediately")
            
            # Create job status as completed
            RedisCache.update_job_status(job_id, {
                "job_id": job_id,
                "status": "completed",
                "created_at": datetime.now().isoformat(),
                "started_at": datetime.now().isoformat(),
                "completed_at": datetime.now().isoformat(),
                "progress": 100,
                "message": "Job completed (cached results)",
                "total_candidates": cached_results.get("total_candidates", 0),
                "passed_candidates": cached_results.get("passed_candidates", 0)
            })
            
            # Create search results object
            search_results = SearchResults(
                job_id=job_id,
                cached=True,
                **cached_results
            )
            RedisCache.cache_job_results(job_id, search_results.dict())
            
            return JobResponse(
                job_id=job_id,
                status="completed",
                message="Job completed immediately (cached results)",
                estimated_completion_time=datetime.now().isoformat(),
                data=cached_results
            )
        
        # Initialize job status
        RedisCache.update_job_status(job_id, {
            "job_id": job_id,
            "status": "queued",
            "created_at": datetime.now().isoformat(),
            "progress": 0,
            "message": "Job queued for processing with worker system",
            "processing_mode": "workers"
        })
        
        # Submit job to ARQ
        logger.info("Submitting job to ARQ worker")
        arq_job = await arq_pool.enqueue_job(
            'process_job',
            job_id=job_id,
            job_description=job_description,
            search_method=search_method,
            limit=limit,
            cache_key=cache_key
        )
        
        logger.info(f"Job {job_id} submitted to ARQ (ARQ job ID: {arq_job.job_id})")
        
        return JobResponse(
            job_id=job_id,
            status="queued", 
            message="Job queued successfully with ARQ (scalable async processing)",
            estimated_completion_time=(datetime.now() + timedelta(minutes=5)).isoformat()
        )
            
    except Exception as e:
        logger.error(f"Error submitting job: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to submit job: {str(e)}")




@app.get("/api/jobs/{job_id}/results", response_model=SearchResults)
async def get_job_results(job_id: str):
    """Get the results of a completed job."""
    try:
        # Check job status first
        status_data = RedisCache.get_job_status(job_id)
        if not status_data:
            raise HTTPException(status_code=404, detail="Job not found")
        
        if status_data.get("status") != "completed":
            raise HTTPException(
                status_code=400, 
                detail=f"Job is not completed yet. Current status: {status_data.get('status')}"
            )
        
        # Get results
        results = RedisCache.get_job_results(job_id)
        if not results:
            raise HTTPException(status_code=404, detail="Job results not found")
        
        return SearchResults(**results)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job results: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get job results: {str(e)}")




@app.get("/api/jobs")
async def list_jobs(status: Optional[str] = None):
    """List all jobs with optional status filtering. Returns candidates with URL and score only."""
    try:
        jobs = RedisCache.get_all_jobs(status)
        
        result = []
        for job in jobs:
            job_id = job.get("job_id")
            job_status = job.get("status")
            
            job_data = {
                "job_id": job_id,
                "status": job_status,
                "created_at": job.get("created_at"),
                "completed_at": job.get("completed_at"),
                "total_candidates": job.get("total_candidates", 0),
                "passed_candidates": job.get("passed_candidates", 0),
                "candidates": []
            }
            
            # If job is completed, get candidate data
            if job_status == "completed" and job_id:
                results_data = RedisCache.get_job_results(job_id)
                if results_data and "candidates" in results_data:
                    for candidate in results_data["candidates"]:
                        job_data["candidates"].append({
                            "name": candidate.get("name", ""),
                            "linkedin_url": candidate.get("linkedin_url", ""),
                            "fit_score": candidate.get("fit_score", 0.0),
                            "outreach_message": candidate.get("outreach_message", ""),
                            "score_breakdown": candidate.get("score_breakdown", {}),
                            "passed": candidate.get("passed", False)
                        })
            
            result.append(job_data)
        
        return {
            "total_jobs": len(result),
            "status_filter": status,
            "jobs": result
        }
        
    except Exception as e:
        logger.error(f"Error listing jobs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list jobs: {str(e)}")


@app.delete("/api/jobs/{job_id}/cache")
async def delete_job_cache(job_id: str):
    """Delete cache entries for a specific job."""
    try:
        deleted = RedisCache.delete_job_cache(job_id)
        if deleted:
            return {
                "message": f"Cache deleted for job {job_id}",
                "job_id": job_id,
                "deleted": True
            }
        else:
            return {
                "message": f"No cache found for job {job_id}",
                "job_id": job_id,
                "deleted": False
            }
    except Exception as e:
        logger.error(f"Error deleting job cache: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete job cache: {str(e)}")

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    try:
        redis_status = "connected" if RedisCache.is_available() else "unavailable"
        
        # Check ARQ pool
        arq_status = "healthy"
        try:
            if arq_pool:
                await arq_pool.ping()
            else:
                arq_status = "pool not initialized"
        except Exception as e:
            arq_status = f"unhealthy: {str(e)}"
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "redis": redis_status,
            "arq_system": {
                "status": arq_status,
                "features": ["async_processing", "scalability", "distributed_workers"]
            },
            "features": {
                "async_processing": "True async with ARQ",
                "concurrent_jobs": "Up to 10 jobs concurrently",
                "search_methods": ["rapid_api", "playwright"],
                "pipeline_features": ["search", "extraction", "scoring", "outreach"]
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }



@app.get("/")
async def root():
    """Root endpoint redirect to API info."""
    return {
        "message": "LinkedIn Profile Sourcing API",
        "docs": "/docs",
        "api": "/api"
    }



if __name__ == "__main__":
    print("🌐 Starting LinkedIn Sourcing API...")
    print("   API will be available at: http://localhost:8000")
    print("   API docs at: http://localhost:8000/docs")
    print("   Health check: http://localhost:8000/api/health")
    print("   Press Ctrl+C to stop")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True) 