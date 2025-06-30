"""
ARQ Worker for Streamlined LinkedIn Profile Processing
Handles AI-powered keyword extraction and profile sourcing with two optimized methods
"""
import asyncio
import logging
import signal
import sys
import os
from datetime import datetime
from typing import Dict, Any

from arq.connections import RedisSettings
from utils.redis_cache import RedisCache
from models.api_models import SearchResults, CandidateInfo

logger = logging.getLogger(__name__)


async def process_job(ctx: Dict[str, Any], job_id: str, job_description: str, search_method: str, limit: int, cache_key: str) -> Dict[str, Any]:
    logger.info(f"🚀 Processing job {job_id} | Method: {search_method} | Limit: {limit}")

    try:
        RedisCache.update_job_status(job_id, {
            "status": "processing",
            "started_at": datetime.now().isoformat(),
            "message": f"Processing with {search_method}"
        })

        if search_method == "rapid_api":
            from utils.enhanced_workflow import search_with_rapid_api_and_score
            search_result, scoring_result = await search_with_rapid_api_and_score(job_description, limit)
        elif search_method == "google_crawler":
            from utils.enhanced_workflow import search_with_google_crawler_and_score
            search_result, scoring_result = await search_with_google_crawler_and_score(job_description, limit)
        else:
            raise ValueError(f"Unknown search method: {search_method}")

        outreach_messages = await generate_outreach_async(scoring_result.scored_candidates, job_description)

        candidates = [
            CandidateInfo(
                name=c.name,
                linkedin_url=c.linkedin_url,
                fit_score=c.score,
                score_breakdown=c.score_breakdown.dict(),  # Convert Pydantic model to dict
                outreach_message=outreach_messages.get(c.linkedin_url, "Hi, I'd like to connect with you."),
                headline=c.headline,
                location=c.location,
                passed=c.recommendation in ["STRONG_MATCH", "GOOD_MATCH", "CONSIDER"]
            )
            for c in scoring_result.scored_candidates
        ]

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

        RedisCache.cache_results(cache_key, results_data)
        RedisCache.cache_job_results(job_id, SearchResults(job_id=job_id, **results_data).dict())

        RedisCache.update_job_status(job_id, {
            "status": "completed",
            "completed_at": datetime.now().isoformat(),
            **results_data
        })

        logger.info(f"✅ Job {job_id} completed: {len(scoring_result.passed_candidates)}/{scoring_result.total_candidates}")
        return {
            "status": "completed",
            "total_candidates": scoring_result.total_candidates,
            "passed_candidates": len(scoring_result.passed_candidates),
            "ai_keywords_used": True,
            "search_query": search_result.search_query
        }

    except Exception as e:
        logger.error(f"❌ Job {job_id} failed: {e}")
        RedisCache.update_job_status(job_id, {
            "status": "failed",
            "completed_at": datetime.now().isoformat(),
            "error": str(e)
        })
        raise


async def generate_outreach_async(candidates: list, job_description: str) -> Dict[str, str]:
    async def generate_single(c):
        try:
            msg = f"Hi {c.name}! I came across your profile"
            if c.headline:
                msg += f" as a {c.headline}"
            if c.location:
                msg += f" in {c.location}"
            msg += ". I have an exciting opportunity that matches your expertise. Would you be open to a brief chat?"
            return c.linkedin_url, msg
        except Exception as e:
            logger.error(f"Outreach error: {e}")
            return getattr(c, 'linkedin_url', ''), "Hi, I'd like to connect with you."

    return dict(await asyncio.gather(*(generate_single(c) for c in candidates)))


class WorkerSettings:
    redis_settings = RedisSettings(host='localhost', port=6379, database=0)
    functions = [process_job]
    max_jobs = 10
    job_timeout = 600
    keep_result = 3600


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )


def setup_aggressive_shutdown():
    def kill_now(signum, frame):
        logger.warning("🛑 Ctrl+C detected — exiting immediately.")
        os._exit(1)

    signal.signal(signal.SIGINT, kill_now)
    signal.signal(signal.SIGTERM, kill_now)


async def main():
    from arq.worker import create_worker
    worker = create_worker(WorkerSettings)
    await worker.main()


if __name__ == '__main__':
    setup_logging()
    setup_aggressive_shutdown()

    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)
