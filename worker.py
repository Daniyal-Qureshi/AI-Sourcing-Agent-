"""
ARQ Worker for Streamlined LinkedIn Profile Processing
Handles AI-powered keyword extraction and profile sourcing with two optimized methods
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
    ARQ job function: Process complete LinkedIn sourcing pipeline with AI keywords
    
    Args:
        ctx: ARQ context
        job_id: Unique job identifier
        job_description: Job description to analyze and extract keywords from
        search_method: Search method to use ('rapid_api' or 'google_crawler')
        limit: Number of profiles to find
        cache_key: Cache key for results
        
    Returns:
        Dict with job results
    """
    # Context info for better error tracking
    logger.info(f"🚀 ARQ Processing job {job_id} with AI keywords (attempt {ctx.get('job_try', 1)})")
    logger.info(f"🎯 Method: {search_method}, Job description length: {len(job_description)} chars, Limit: {limit}")
    
    try:
        # Update status at start
        RedisCache.update_job_status(job_id, {
            "status": "processing",
            "started_at": datetime.now().isoformat(),
            "message": f"Processing with {search_method} and AI keyword extraction"
        })
        
        # Use streamlined workflow with AI keyword generation
        logger.info(f"🔍 Processing job with streamlined workflow using {search_method}")
        
        if search_method == "rapid_api":
            from utils.enhanced_workflow import search_with_rapid_api_and_score
            search_result, scoring_result = await search_with_rapid_api_and_score(job_description, limit)
        elif search_method == "google_crawler":
            from utils.enhanced_workflow import search_with_google_crawler_and_score
            search_result, scoring_result = await search_with_google_crawler_and_score(job_description, limit)
        else:
            raise ValueError(f"Unknown search method: {search_method}. Use 'rapid_api' or 'google_crawler'")
        
        # Generate outreach messages concurrently
        logger.info(f"💬 Generating outreach for {len(scoring_result.scored_candidates)} candidates")
        outreach_messages = await generate_outreach_async(scoring_result.scored_candidates, job_description)
        
        # Format final results
        candidates = []
        for candidate in scoring_result.scored_candidates:
            # Extract LinkedIn profile from ScoredCandidate
            profile = candidate.candidate
            
            candidates.append(CandidateInfo(
                name=profile.name,
                linkedin_url=profile.linkedin_url,
                fit_score=candidate.overall_score,
                score_breakdown=candidate.score_breakdown,
                outreach_message=outreach_messages.get(profile.linkedin_url, "Hi, I'd like to connect with you."),
                headline=profile.headline,
                location=profile.location,
                passed=candidate.recommendation in ["STRONG_MATCH", "GOOD_MATCH", "CONSIDER"]
            ))
        
        results_data = {
            "total_candidates": scoring_result.total_candidates,
            "passed_candidates": len(scoring_result.passed_candidates),
            "failed_candidates": len(scoring_result.failed_candidates),
            "pass_rate": f"{(len(scoring_result.passed_candidates) / scoring_result.total_candidates * 100):.1f}%" if scoring_result.total_candidates else "0%",
            "search_method": search_method,
            "search_time": search_result.search_time,
            "scoring_time": scoring_result.scoring_time,
            "ai_keywords_used": search_result.ai_keywords_used,
            "search_query": search_result.search_query,
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
            "message": f"Job completed successfully with {search_method} and AI keywords",
            "total_candidates": scoring_result.total_candidates,
            "passed_candidates": len(scoring_result.passed_candidates),
            "ai_keywords_used": True,
            "search_query": search_result.search_query
        })
        
        logger.info(f"✅ ARQ job {job_id} completed: {len(scoring_result.passed_candidates)}/{scoring_result.total_candidates} candidates")
        logger.info(f"🎯 AI Search query used: {search_result.search_query}")
        
        return {
            "status": "completed",
            "total_candidates": scoring_result.total_candidates,
            "passed_candidates": len(scoring_result.passed_candidates),
            "ai_keywords_used": True,
            "search_query": search_result.search_query
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
    """Generate outreach messages concurrently for scored candidates"""
    
    async def generate_single(candidate):
        try:
            # Extract LinkedIn profile from ScoredCandidate
            profile = candidate.candidate
            linkedin_url = profile.linkedin_url
            
            # Simple outreach message generation
            outreach_message = f"Hi {profile.name}! I came across your profile and was impressed by your background"
            if profile.headline:
                outreach_message += f" as a {profile.headline}"
            if profile.location:
                outreach_message += f" in {profile.location}"
            outreach_message += ". I have an exciting opportunity that matches your expertise. Would you be open to a brief conversation?"
            
            return linkedin_url, outreach_message
            
        except Exception as e:
            logger.error(f"Failed outreach generation: {e}")
            return getattr(candidate.candidate, 'linkedin_url', ''), "Hi, I'd like to connect with you regarding an opportunity that matches your background."
    
    # Generate all outreach concurrently
    tasks = [generate_single(candidate) for candidate in candidates]
    results = await asyncio.gather(*tasks)
    
    return dict(results)


# ARQ Configuration
class WorkerSettings:
    """ARQ worker settings for streamlined processing"""
    redis_settings = RedisSettings(host='localhost', port=6379, database=0)
    functions = [process_job]
    max_jobs = 10  
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
        logger.info("🚀 Starting Streamlined ARQ Worker with AI Keywords")
        logger.info("📋 Worker Configuration:")
        logger.info(f"   • Max concurrent jobs: {WorkerSettings.max_jobs}")
        logger.info(f"   • Job timeout: {WorkerSettings.job_timeout} seconds")
        logger.info(f"   • Redis: {WorkerSettings.redis_settings.host}:{WorkerSettings.redis_settings.port}")
        logger.info(f"   • Supported methods: rapid_api, google_crawler")
        logger.info(f"   • Features: AI keyword extraction, targeted searches, comprehensive profiles")
        logger.info("🔄 Worker is ready to process jobs... (Press Ctrl+C to stop)")
        
        from arq.worker import create_worker
        worker = create_worker(WorkerSettings)
        
        try:
            await worker.main()
        except asyncio.CancelledError:
            logger.info("💤 Worker shutdown completed")
        except KeyboardInterrupt:
            logger.info("🛑 Worker interrupted, shutting down gracefully...")
        finally:
            logger.info("👋 ARQ Worker stopped")
    
    # Run the worker
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 ARQ Worker stopped by user")
    except Exception as e:
        logger.error(f"❌ ARQ Worker error: {e}")
        sys.exit(1)
