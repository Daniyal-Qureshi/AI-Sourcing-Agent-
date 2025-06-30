"""
Streamlined LinkedIn Profile Sourcing Workflow
Two main methods: rapid_api and google_crawler with AI-powered keyword generation
"""
import asyncio
import logging
import time
from enum import Enum
from typing import List, Tuple, Dict, Any
from pydantic import BaseModel

from utils.candidate_scorer import CandidateScorer, ScoredCandidate
from utils.enhanced_google_extractor import extract_profiles_rapid_api, extract_profiles_google_crawler
from models.linkedin_profile import LinkedInProfile

logger = logging.getLogger(__name__)


class SearchMethod(Enum):
    """Streamlined search method enumeration."""
    RAPID_API = "rapid_api"
    GOOGLE_CRAWLER = "google_crawler"


class SearchResult(BaseModel):
    """Search result model."""
    search_method: SearchMethod
    search_time: float
    total_profiles_found: int
    profiles: List[LinkedInProfile]
    ai_keywords_used: bool = False
    search_query: str = ""


class ScoringResult(BaseModel):
    """Scoring result model."""
    total_candidates: int
    passed_candidates: List[ScoredCandidate]
    failed_candidates: List[ScoredCandidate]
    scored_candidates: List[ScoredCandidate]
    scoring_time: float


class StreamlinedWorkflowError(Exception):
    """Custom exception for streamlined workflow errors."""
    pass


async def search_with_rapid_api_and_score(
    job_description: str, 
    limit: int = 5
) -> Tuple[SearchResult, ScoringResult]:
    """
    Search LinkedIn profiles using RapidAPI with AI-powered keyword generation and score them.
    
    Args:
        job_description: The job description to analyze and search against
        limit: Maximum number of profiles to search for
        
    Returns:
        Tuple of (SearchResult, ScoringResult)
    """
    logger.info(f"🚀 Starting RapidAPI search with AI keywords")
    logger.info(f"📋 Job description length: {len(job_description)} chars, Limit: {limit}")
    
    try:
        # Search using integrated RapidAPI extractor with AI keywords
        search_start = time.time()
        
        profiles = await extract_profiles_rapid_api(job_description, limit)
        
        search_time = time.time() - search_start
        logger.info(f"✅ RapidAPI search completed in {search_time:.2f}s, found {len(profiles)} profiles")
        
        # Create search result
        search_result = SearchResult(
            search_method=SearchMethod.RAPID_API,
            search_time=search_time,
            total_profiles_found=len(profiles),
            profiles=profiles,
            ai_keywords_used=True,
            search_query="AI-generated keywords via RapidAPI"
        )
        
        # Score candidates
        logger.info("🎯 Starting candidate scoring...")
        scoring_result = _score_candidates(profiles, job_description)
        
        logger.info(f"🎉 RapidAPI workflow completed")
        logger.info(f"📊 Results: {len(scoring_result.passed_candidates)}/{scoring_result.total_candidates} candidates passed")
        
        return search_result, scoring_result
        
    except Exception as e:
        error_msg = f"RapidAPI workflow failed: {str(e)}"
        logger.error(f"❌ {error_msg}")
        raise StreamlinedWorkflowError(error_msg)


async def search_with_google_crawler_and_score(
    job_description: str, 
    limit: int = 5
) -> Tuple[SearchResult, ScoringResult]:
    """
    Search LinkedIn profiles using Google crawler with AI-powered keyword generation and score them.
    
    Args:
        job_description: The job description to analyze and search against
        limit: Maximum number of profiles to search for
        
    Returns:
        Tuple of (SearchResult, ScoringResult)
    """
    logger.info(f"🚀 Starting Google crawler search with AI keywords")
    logger.info(f"📋 Job description length: {len(job_description)} chars, Limit: {limit}")
    
    try:
        # Search using integrated Google crawler extractor with AI keywords  
        search_start = time.time()
        
        profiles = await extract_profiles_google_crawler(job_description, limit)
        
        search_time = time.time() - search_start
        logger.info(f"✅ Google crawler search completed in {search_time:.2f}s, found {len(profiles)} profiles")
        
        # Create search result
        search_result = SearchResult(
            search_method=SearchMethod.GOOGLE_CRAWLER,
            search_time=search_time,
            total_profiles_found=len(profiles),
            profiles=profiles,
            ai_keywords_used=True,
            search_query="AI-generated optimized Google search"
        )
        
        # Score candidates
        logger.info("🎯 Starting candidate scoring...")
        scoring_result = _score_candidates(profiles, job_description)
        
        logger.info(f"🎉 Google crawler workflow completed")
        logger.info(f"📊 Results: {len(scoring_result.passed_candidates)}/{scoring_result.total_candidates} candidates passed")
        
        return search_result, scoring_result
        
    except Exception as e:
        error_msg = f"Google crawler workflow failed: {str(e)}"
        logger.error(f"❌ {error_msg}")
        raise StreamlinedWorkflowError(error_msg)


def _score_candidates(
    profiles: List[LinkedInProfile], 
    job_description: str
) -> ScoringResult:
    """
    Score candidates against job description using the candidate scorer.
    
    Args:
        profiles: List of LinkedIn profiles to score
        job_description: Job description to score against
        
    Returns:
        ScoringResult with scored candidates
    """
    logger.info(f"🎯 Scoring {len(profiles)} candidates against job description")
    
    scoring_start = time.time()
    
    try:
        scorer = CandidateScorer()
        scored_candidates = []
        
        for profile in profiles:
            try:
                scored_candidate = scorer.score_candidate(profile, job_description)
                scored_candidates.append(scored_candidate)
            except Exception as e:
                logger.warning(f"⚠️ Failed to score candidate {profile.name}: {e}")
                # Create a failed candidate entry
                from utils.candidate_scorer import ScoreBreakdown
                failed_candidate = ScoredCandidate(
                    # Original candidate fields
                    name=profile.name,
                    headline=profile.headline,
                    linkedin_url=profile.linkedin_url,
                    location=profile.location,
                    summary=profile.summary,
                    experience=profile.experience,
                    education=profile.education,
                    skills=profile.skills,
                    connections=profile.connections,
                    profile_image=profile.profile_image,
                    current_company=profile.current_company,
                    current_position=profile.current_position,
                    
                    # Failed scoring fields
                    score=0.0,
                    score_breakdown=ScoreBreakdown(
                        education=0.0,
                        career_trajectory=0.0,
                        company_relevance=0.0,
                        experience_match=0.0,
                        location_match=0.0,
                        tenure=0.0
                    ),
                    reasoning=None,
                    passed=False,
                    recommendation="REJECT"
                )
                scored_candidates.append(failed_candidate)
        
        # Separate passed and failed candidates
        passed_candidates = [c for c in scored_candidates if c.recommendation in ["STRONG_MATCH", "GOOD_MATCH", "CONSIDER"]]
        failed_candidates = [c for c in scored_candidates if c.recommendation in ["REJECT", "NO_MATCH"]]
        
        scoring_time = time.time() - scoring_start
        
        logger.info(f"✅ Scoring completed in {scoring_time:.2f}s")
        logger.info(f"📊 Passed: {len(passed_candidates)}, Failed: {len(failed_candidates)}")
        
        return ScoringResult(
            total_candidates=len(profiles),
            passed_candidates=passed_candidates,
            failed_candidates=failed_candidates,
            scored_candidates=scored_candidates,
            scoring_time=scoring_time
        )
        
    except Exception as e:
        logger.error(f"❌ Scoring failed: {e}")
        # Return empty scoring result on failure
        return ScoringResult(
            total_candidates=len(profiles),
            passed_candidates=[],
            failed_candidates=[],
            scored_candidates=[],
            scoring_time=time.time() - scoring_start
        )


# Main processing functions for ARQ workers
async def process_job_rapid_api(job_description: str, limit: int = 5) -> Tuple[SearchResult, ScoringResult]:
    """
    Process job using RapidAPI method.
    Main entry point for ARQ workers.
    """
    logger.info(f"🔄 Processing job with RapidAPI method")
    return await search_with_rapid_api_and_score(job_description, limit)


async def process_job_google_crawler(job_description: str, limit: int = 5) -> Tuple[SearchResult, ScoringResult]:
    """
    Process job using Google crawler method.
    Main entry point for ARQ workers.
    """
    logger.info(f"🔄 Processing job with Google crawler method")
    return await search_with_google_crawler_and_score(job_description, limit)


 