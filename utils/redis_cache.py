"""
Redis Cache Management for LinkedIn Sourcing
"""
import json
import logging
import os
from typing import Dict, Any, Optional
from datetime import datetime

import redis

logger = logging.getLogger(__name__)

# Redis configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")

# Cache settings
CACHE_TTL = int(os.getenv("CACHE_TTL", 3600))  # 1 hour default
JOB_STATUS_TTL = int(os.getenv("JOB_STATUS_TTL", 86400))  # 24 hours default

# Redis client for caching only
try:
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        password=REDIS_PASSWORD,
        decode_responses=True
    )
    # Test connection
    redis_client.ping()
    logger.info("✅ Redis connection successful")
except Exception as e:
    logger.warning(f"⚠️ Redis connection failed: {e}. Caching will be disabled.")
    redis_client = None


def generate_cache_key(job_description: str, search_method: str, limit: int) -> str:
    """Generate a cache key based on job parameters."""
    import hashlib
    content = f"{job_description}:{search_method}:{limit}"
    return f"linkedin_search:{hashlib.md5(content.encode()).hexdigest()}"


def generate_job_status_key(job_id: str) -> str:
    """Generate a Redis key for job status."""
    return f"job_status:{job_id}"


def generate_results_key(job_id: str) -> str:
    """Generate a Redis key for job results."""
    return f"job_results:{job_id}"


class RedisCache:
    """Redis cache operations for LinkedIn sourcing."""
    
    @staticmethod
    def is_available() -> bool:
        """Check if Redis is available."""
        return redis_client is not None
    
    @staticmethod
    def get_cached_results(cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached search results."""
        if not redis_client:
            return None
            
        try:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
            return None
        except Exception as e:
            logger.error(f"Error getting cached results: {e}")
            return None
    
    @staticmethod
    def cache_results(cache_key: str, results: Dict[str, Any], ttl: int = CACHE_TTL):
        """Cache search results."""
        if not redis_client:
            return
            
        try:
            redis_client.setex(cache_key, ttl, json.dumps(results, default=str))
            logger.info(f"Cached results with key: {cache_key}")
        except Exception as e:
            logger.error(f"Error caching results: {e}")
    
    @staticmethod
    def get_job_status(job_id: str) -> Optional[Dict[str, Any]]:
        """Get job status from Redis."""
        if not redis_client:
            return None
            
        try:
            status_data = redis_client.get(generate_job_status_key(job_id))
            if status_data:
                return json.loads(status_data)
            return None
        except Exception as e:
            logger.error(f"Error getting job status: {e}")
            return None
    
    @staticmethod
    def update_job_status(job_id: str, status_update: Dict[str, Any]):
        """Update job status in Redis."""
        if not redis_client:
            return
            
        try:
            key = generate_job_status_key(job_id)
            existing_data = redis_client.get(key)
            
            if existing_data:
                data = json.loads(existing_data)
                data.update(status_update)
            else:
                data = status_update
            
            redis_client.setex(key, JOB_STATUS_TTL, json.dumps(data, default=str))
            logger.info(f"Updated job status for {job_id}: {status_update}")
        except Exception as e:
            logger.error(f"Error updating job status: {e}")
    
    @staticmethod
    def get_job_results(job_id: str) -> Optional[Dict[str, Any]]:
        """Get job results from Redis."""
        if not redis_client:
            return None
            
        try:
            results_data = redis_client.get(generate_results_key(job_id))
            if results_data:
                return json.loads(results_data)
            return None
        except Exception as e:
            logger.error(f"Error getting job results: {e}")
            return None
    
    @staticmethod
    def cache_job_results(job_id: str, results: Dict[str, Any]):
        """Cache job results."""
        if not redis_client:
            return
            
        try:
            key = generate_results_key(job_id)
            redis_client.setex(key, JOB_STATUS_TTL, json.dumps(results, default=str))
            logger.info(f"Cached job results for {job_id}")
        except Exception as e:
            logger.error(f"Error caching job results: {e}")
    
    @staticmethod
    def delete_job_cache(job_id: str) -> bool:
        """Delete all cache entries for a job (status + results)."""
        if not redis_client:
            return False
            
        try:
            status_key = generate_job_status_key(job_id)
            results_key = generate_results_key(job_id)
            
            deleted_count = redis_client.delete(status_key, results_key)
            logger.info(f"Deleted {deleted_count} cache entries for job {job_id}")
            return deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting job cache: {e}")
            return False
    
    @staticmethod
    def delete_cache_by_key(cache_key: str) -> bool:
        """Delete cache entry by cache key."""
        if not redis_client:
            return False
            
        try:
            deleted = redis_client.delete(cache_key)
            if deleted:
                logger.info(f"Deleted cache entry: {cache_key}")
            return deleted > 0
        except Exception as e:
            logger.error(f"Error deleting cache by key: {e}")
            return False
    
    @staticmethod
    def get_all_jobs(status_filter: Optional[str] = None) -> list[Dict[str, Any]]:
        """Get all jobs with optional status filtering."""
        if not redis_client:
            return []
            
        try:
            # Get all job status keys
            job_keys = redis_client.keys("job_status:*")
            jobs = []
            
            for key in job_keys:
                try:
                    job_data = redis_client.get(key)
                    if job_data:
                        job_info = json.loads(job_data)
                        
                        # Apply status filter if provided
                        if status_filter:
                            job_status = job_info.get("status", "")
                            if status_filter == "in_progress" and job_status not in ["queued", "processing"]:
                                continue
                            elif status_filter == "completed" and job_status != "completed":
                                continue
                            elif status_filter == "failed" and job_status != "failed":
                                continue
                        
                        jobs.append(job_info)
                except Exception as e:
                    logger.error(f"Error processing job key {key}: {e}")
                    continue
            
            return jobs
        except Exception as e:
            logger.error(f"Error getting all jobs: {e}")
            return [] 