"""
ARQ Worker for Scalable LinkedIn Profile Processing
Handles complete job workflows with true async scalability
"""
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

from arq import cron
from arq.connections import RedisSettings
from utils.redis_cache import RedisCache
from models.api_models import SearchResults, CandidateInfo

logger = logging.getLogger(__name__)


async def process_job(ctx: Dict[str, Any], job_id: str, job_description: str, search_method: str, limit: int, cache_key: str) -> Dict[str, Any]:
    """
    ARQ job function: Process complete LinkedIn sourcing pipeline
    
    Args:
        ctx: ARQ context
        job_id: Unique job identifier
        job_description: Job description to process
        search_method: Search method to use
        limit: Number of profiles to find
        cache_key: Cache key for results
        
    Returns:
        Dict with job results
    """
    # Context info for better error tracking
    logger.info(f"🚀 ARQ Processing job {job_id} (attempt {ctx.get('job_try', 1)})")
    logger.info(f"🚀 ARQ Processing job {job_id}")
    
    try:
        # Update status at start
        RedisCache.update_job_status(job_id, {
            "status": "processing",
            "started_at": datetime.now().isoformat(),
            "message": "Processing with ARQ worker"
        })
        
        # Use enhanced workflow (already does search + extraction + scoring)
        logger.info(f"🔍 Processing job with enhanced workflow using {search_method}")
        
        if search_method == "rapid_api":
            from utils.enhanced_workflow import search_with_rapid_api_and_score
            loop = asyncio.get_event_loop()
            search_result, scoring_result = await loop.run_in_executor(
                None, search_with_rapid_api_and_score, job_description, limit
            )
        elif search_method == "playwright":
            from utils.enhanced_workflow import search_with_playwright_and_score
            search_result, scoring_result = await search_with_playwright_and_score(job_description, limit)
        elif search_method == "playwright_two_phase":
            from utils.enhanced_workflow import search_with_playwright_two_phase_and_score
            search_result, scoring_result = await search_with_playwright_two_phase_and_score(job_description, limit)
        else:
            raise ValueError(f"Unknown search method: {search_method}. Use 'rapid_api', 'playwright', or 'playwright_two_phase'")
        
        # Step 2: Generate outreach messages concurrently
        logger.info(f"💬 Generating outreach for {len(scoring_result.scored_candidates)} candidates")
        outreach_messages = await generate_outreach_async(scoring_result.scored_candidates, job_description)
        
        # Format final results
        candidates = []
        for candidate in scoring_result.scored_candidates:
            candidates.append(CandidateInfo(
                name=candidate.name,
                linkedin_url=candidate.linkedin_url,
                fit_score=candidate.score,
                score_breakdown=candidate.score_breakdown,
                outreach_message=outreach_messages.get(candidate.linkedin_url, "Hi, I'd like to connect with you."),
                headline=candidate.headline,
                location=candidate.location,
                passed=candidate.passed
            ))
        
        results_data = {
            "total_candidates": scoring_result.total_candidates,
            "passed_candidates": len(scoring_result.passed_candidates),
            "failed_candidates": len(scoring_result.failed_candidates),
            "pass_rate": f"{(len(scoring_result.passed_candidates) / scoring_result.total_candidates * 100):.1f}%" if scoring_result.total_candidates else "0%",
            "search_method": search_method,
            "search_time": search_result.search_time,
            "scoring_time": scoring_result.scoring_time,
            "candidates": [c.dict() for c in candidates]
        }
        
        search_results = SearchResults(job_id=job_id, **results_data)
        
        # Cache results
        RedisCache.cache_results(cache_key, results_data)
        RedisCache.cache_job_results(job_id, search_results.dict())
        
        # Update final status
        RedisCache.update_job_status(job_id, {
            "status": "completed",
            "completed_at": datetime.now().isoformat(),
            "message": "Job completed successfully",
            "total_candidates": scoring_result.total_candidates,
            "passed_candidates": len(scoring_result.passed_candidates)
        })
        
        logger.info(f"✅ ARQ job {job_id} completed: {len(scoring_result.passed_candidates)}/{scoring_result.total_candidates} candidates")
        
        return {
            "status": "completed",
            "total_candidates": scoring_result.total_candidates,
            "passed_candidates": len(scoring_result.passed_candidates)
        }
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ ARQ job {job_id} failed: {error_msg}")
        
        RedisCache.update_job_status(job_id, {
            "status": "failed",
            "completed_at": datetime.now().isoformat(),
            "error": error_msg,
            "message": f"Job failed: {error_msg}"
        })
        
        raise


async def generate_outreach_async(candidates: list, job_description: str) -> Dict[str, str]:
    """Generate outreach messages concurrently"""
    from utils.profile_extractor import generate_outreach_message
    
    async def generate_single(candidate):
        try:
            loop = asyncio.get_event_loop()
            message = await loop.run_in_executor(
                None,
                generate_outreach_message,
                candidate.linkedin_url,
                job_description,
                "connection_request"
            )
            return candidate.linkedin_url, message
        except Exception as e:
            logger.error(f"Failed outreach for {candidate.linkedin_url}: {e}")
            return candidate.linkedin_url, "Hi, I'd like to connect with you regarding an opportunity that matches your background."
    
    # Generate all outreach concurrently
    tasks = [generate_single(candidate) for candidate in candidates]
    results = await asyncio.gather(*tasks)
    
    return dict(results)


# ARQ Configuration
class WorkerSettings:
    """ARQ worker settings"""
    redis_settings = RedisSettings(host='localhost', port=6379, database=0)
    functions = [process_job]
    max_jobs = 10  # Process up to 10 jobs concurrently
    job_timeout = 600  # 10 minutes timeout per job
    keep_result = 3600  # Keep results for 1 hour
    
    # Shutdown settings for proper Ctrl+C handling
    max_burst_jobs = 1  # Process one job at a time during shutdown
    health_check_interval = 1  # Check for shutdown signals every 1 second
    graceful_shutdown_timeout = 5  # Force shutdown after 5 seconds


if __name__ == '__main__':
    # Run ARQ worker with proper Ctrl+C handling
    import sys
    
    # Setup logging for worker
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    async def main():
        """Run the ARQ worker"""
        logger.info("🚀 Starting ARQ Worker for LinkedIn Profile Processing")
        logger.info("📋 Worker Configuration:")
        logger.info(f"   • Max concurrent jobs: {WorkerSettings.max_jobs}")
        logger.info(f"   • Job timeout: {WorkerSettings.job_timeout} seconds")
        logger.info(f"   • Redis: {WorkerSettings.redis_settings.host}:{WorkerSettings.redis_settings.port}")
        logger.info("🔄 Worker is ready to process jobs... (Press Ctrl+C to stop)")
        
        from arq.worker import create_worker
        worker = create_worker(WorkerSettings)
        
        try:
            await worker.main()
        except asyncio.CancelledError:
            logger.info("✅ ARQ Worker task cancelled")
        except Exception as e:
            logger.error(f"❌ Worker error: {e}")
            raise

from arq import run_worker

from arq_worker import WorkerSettings  # adjust if your file/module is named differently

if __name__ == "__main__":
    import asyncio
    asyncio.run(run_worker(WorkerSettings))
