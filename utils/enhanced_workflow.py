"""
Enhanced Workflow for LinkedIn Profile Sourcing
Combines search and scoring functionality with proper result structures
Supports both legacy single-phase and new two-phase approaches
"""
import asyncio
import logging
import time
from enum import Enum
from typing import List, Tuple, Dict, Any
from pydantic import BaseModel

from utils.job_description_parser import JobDescriptionParser
from utils.rapid_api_search import RapidAPILinkedInSearcher
from utils.google_search import LinkedInSearcher
from utils.profile_extractor import LinkedInProfileExtractor, scrape_html_only, process_html_files
from utils.candidate_scorer import CandidateScorer, ScoredCandidate
from models.linkedin_profile import LinkedInProfile

logger = logging.getLogger(__name__)


class SearchMethod(Enum):
    """Search method enumeration."""
    RAPID_API = "rapid_api"
    PLAYWRIGHT_CRAWLER = "playwright_crawler"
    PLAYWRIGHT_TWO_PHASE = "playwright_two_phase"


class SearchResult(BaseModel):
    """Search result model."""
    search_method: SearchMethod
    search_time: float
    total_profiles_found: int
    profiles: List[LinkedInProfile]
    html_scraping_summary: Dict[str, Any] = None


class ScoringResult(BaseModel):
    """Scoring result model."""
    total_candidates: int
    passed_candidates: List[ScoredCandidate]
    failed_candidates: List[ScoredCandidate]
    scored_candidates: List[ScoredCandidate]
    scoring_time: float


class EnhancedWorkflowError(Exception):
    """Custom exception for enhanced workflow errors."""
    pass


def search_with_rapid_api_and_score(
    job_description: str, 
    limit: int = 5
) -> Tuple[SearchResult, ScoringResult]:
    """
    Search LinkedIn profiles using Rapid API and score them.
    
    Args:
        job_description: The job description to parse and search against
        limit: Maximum number of profiles to search for
        
    Returns:
        Tuple of (SearchResult, ScoringResult)
    """
    logger.info(f"🚀 Starting Rapid API search and scoring workflow")
    logger.info(f"📋 Job description length: {len(job_description)} chars, Limit: {limit}")
    
   
    
    try:
        # Step 1: Parse job description to extract fields
        logger.info("📝 Parsing job description...")
        parser = JobDescriptionParser()
        job_fields = parser.extract_job_fields(job_description)
        job_fields.limit = limit
        
        # Step 2: Search for profiles using Rapid API
        logger.info("🔍 Searching LinkedIn profiles via Rapid API...")
        search_start = time.time()
        
        searcher = RapidAPILinkedInSearcher()
        profiles = searcher.search_linkedin_profiles(job_fields)
        
        search_time = time.time() - search_start
        logger.info(f"✅ Search completed in {search_time:.2f}s, found {len(profiles)} profiles")
        
        # Create search result
        search_result = SearchResult(
            search_method=SearchMethod.RAPID_API,
            search_time=search_time,
            total_profiles_found=len(profiles),
            profiles=profiles
        )
        
        # Step 3: Score candidates
        logger.info("🎯 Starting candidate scoring...")
        scoring_result = _score_candidates(profiles, job_description)
        
      
        logger.info(f"🎉 Workflow completed")
        logger.info(f"📊 Results: {len(scoring_result.passed_candidates)}/{scoring_result.total_candidates} candidates passed")
        
        return search_result, scoring_result
        
    except Exception as e:
        error_msg = f"Rapid API workflow failed: {str(e)}"
        logger.error(f"❌ {error_msg}")
        raise EnhancedWorkflowError(error_msg)


async def search_with_playwright_and_score(
    job_description: str, 
    limit: int = 5
) -> Tuple[SearchResult, ScoringResult]:
    """
    Search LinkedIn profiles using Playwright crawler and score them (legacy single-phase).
    
    Args:
        job_description: The job description to parse and search against
        limit: Maximum number of profiles to search for
        
    Returns:
        Tuple of (SearchResult, ScoringResult)
    """
    logger.info(f"🚀 Starting Playwright search and scoring workflow (legacy single-phase)")
    logger.info(f"📋 Job description length: {len(job_description)} chars, Limit: {limit}")
    
    
    try:
        
        logger.info("📝 Parsing job description...")
        parser = JobDescriptionParser()
        job_fields = parser.extract_job_fields(job_description)
        
        # Create search terms from job fields
        search_terms = []
        if job_fields.job_title:
            search_terms.append(job_fields.job_title)
        if job_fields.location:
            search_terms.append(job_fields.location)
        
        # If no specific terms, use a default search
        if not search_terms:
            search_terms = ["software engineer", "developer"]
        
        logger.info(f"🔍 Using search terms: {search_terms}")
        
        # Step 2: Search for profile URLs using Google search
        logger.info("🔍 Searching LinkedIn profile URLs via Google...")
        search_start = time.time()
        
        async with LinkedInSearcher() as searcher:
            search_result_obj = await searcher.search_linkedin_profiles(search_terms, limit)
            profile_urls = search_result_obj.profiles
        
       
        logger.info(f"🔗 FOUND {len(profile_urls)} LinkedIn URLs from Google Search:")
        for i, url in enumerate(profile_urls, 1):
            logger.info(f"   {i:2d}. {url}")
        
        if profile_urls:
            logger.info(f"✅ Total URLs ready for processing: {len(profile_urls)}")
        else:
            logger.warning("⚠️ No LinkedIn URLs found!")
        
        # Step 3: Extract profile data from URLs
        logger.info("🤖 Extracting profile data...")
        profiles = []
        
        if profile_urls:
            async with LinkedInProfileExtractor() as extractor:
                for i, url in enumerate(profile_urls[:limit]):
                    try:
                        logger.info(f"📱 Extracting profile {i+1}/{min(len(profile_urls), limit)}: {url}")
                        extraction_result = await extractor.scrape_linkedin_profile(url, use_login=True)
                        
                        if extraction_result.success and extraction_result.profile:
                            profiles.append(extraction_result.profile)
                        else:
                            logger.warning(f"⚠️ Failed to extract profile: {extraction_result.error}")
                            
                    except Exception as e:
                        logger.error(f"❌ Error extracting profile {url}: {e}")
                        continue
        
        search_time = time.time() - search_start
        logger.info(f"✅ Profile extraction completed in {search_time:.2f}s, extracted {len(profiles)} profiles")
        
        # Create search result
        search_result = SearchResult(
            search_method=SearchMethod.PLAYWRIGHT_CRAWLER,
            search_time=search_time,
            total_profiles_found=len(profiles),
            profiles=profiles
        )
        
        # Step 4: Score candidates
        logger.info("🎯 Starting candidate scoring...")
        scoring_result = _score_candidates(profiles, job_description)
        
        logger.info(f"📊 Results: {len(scoring_result.passed_candidates)}/{scoring_result.total_candidates} candidates passed")
        
        return search_result, scoring_result
        
    except Exception as e:
        error_msg = f"Playwright workflow failed: {str(e)}"
        logger.error(f"❌ {error_msg}")
        raise EnhancedWorkflowError(error_msg)


async def search_with_playwright_two_phase_and_score(
    job_description: str, 
    limit: int = 5
) -> Tuple[SearchResult, ScoringResult]:
    """
    Search LinkedIn profiles using new two-phase Playwright approach and score them.
    Phase 1: Get URLs from Google, scrape all HTML, close browser
    Phase 2: Process all HTML files without browser, then score
    
    Args:
        job_description: The job description to parse and search against
        limit: Maximum number of profiles to search for
        
    Returns:
        Tuple of (SearchResult, ScoringResult)
    """
    logger.info(f"🚀 Starting Playwright TWO-PHASE search and scoring workflow")
    logger.info(f"📋 Job description length: {len(job_description)} chars, Limit: {limit}")
    
    
    try:
        logger.info("📝 Parsing job description...")
        parser = JobDescriptionParser()
        job_fields = parser.extract_job_fields(job_description)
        
        # Create search terms from job fields
        search_terms = []
        if job_fields.job_title:
            search_terms.append(job_fields.job_title)
        if job_fields.location:
            search_terms.append(job_fields.location)
        
        # If no specific terms, use a default search
        if not search_terms:
            search_terms = ["software engineer", "developer"]
        
        logger.info(f"🔍 Using search terms: {search_terms}")
        
        # PHASE 1: Search for URLs and scrape HTML
        logger.info("=" * 60)
        logger.info("🔍 PHASE 1: Search URLs and scrape HTML")
        logger.info("=" * 60)
        
        # Step 1: Get LinkedIn profile URLs from Google search
        logger.info("🔍 Searching LinkedIn profile URLs via Google...")
        
        async with LinkedInSearcher() as searcher:
            search_result_obj = await searcher.search_linkedin_profiles(search_terms, limit)
            profile_urls = search_result_obj.profiles
        
        # LOG ALL FOUND URLS
        logger.info(f"🔗 FOUND {len(profile_urls)} LinkedIn URLs from Google Search:")
        for i, url in enumerate(profile_urls, 1):
            logger.info(f"   {i:2d}. {url}")
        
        if profile_urls:
            logger.info(f"✅ Total URLs ready for processing: {len(profile_urls)}")
        else:
            logger.warning("⚠️ No LinkedIn URLs found!")
        
        # Step 2: Scrape HTML from all URLs and close browser
        if not profile_urls:
            logger.warning("⚠️ No profile URLs found, skipping HTML scraping")
            html_scraping_summary = {
                'total_profiles': 0,
                'successful_scrapes': 0,
                'new_scrapes': 0,
                'skipped_scrapes': 0,
                'failed_scrapes': 0,
                'results': [],
                'errors': []
            }
        else:
            # LOG URLS GOING TO SCRAPING
            urls_to_scrape = profile_urls[:limit]
            logger.info(f"🕷️ Scraping HTML from {len(urls_to_scrape)} profiles...")
            logger.info(f"📋 URLs being sent to scraper:")
            for i, url in enumerate(urls_to_scrape, 1):
                logger.info(f"   {i:2d}. {url}")
            html_scraping_summary = await scrape_html_only(urls_to_scrape, use_login=True)
            
        logger.info("🔒 Browser closed after HTML scraping")
        logger.info(f"📊 HTML Scraping Results: {html_scraping_summary['new_scrapes']} new, "
                   f"{html_scraping_summary['skipped_scrapes']} skipped, "
                   f"{html_scraping_summary['failed_scrapes']} failed")
        
        # PHASE 2: Process HTML files (no browser needed)
        logger.info("=" * 60)
        logger.info("🔄 PHASE 2: Process HTML files (browser-free)")
        logger.info("=" * 60)
        
        # Extract usernames from successful HTML scraping results
        usernames = [result['username'] for result in html_scraping_summary['results'] if result['success']]
        
        if not usernames:
            logger.warning("⚠️ No HTML files available for processing")
            profiles = []
        else:
            logger.info(f"📄 Processing {len(usernames)} HTML files...")
            batch_result = process_html_files(usernames)
            profiles = batch_result.profiles
            logger.info(f"✅ Successfully processed {len(profiles)} profiles from HTML files")
        

        
        # Create search result
        search_result = SearchResult(
            search_method=SearchMethod.PLAYWRIGHT_TWO_PHASE,
            
            total_profiles_found=len(profiles),
            profiles=profiles,
            html_scraping_summary=html_scraping_summary
        )
        
        # Step 3: Score candidates
        logger.info("🎯 Starting candidate scoring...")
        scoring_result = _score_candidates(profiles, job_description)
        
    
        logger.info(f"📊 Results: {len(scoring_result.passed_candidates)}/{scoring_result.total_candidates} candidates passed")
        
        return search_result, scoring_result
        
    except Exception as e:
        error_msg = f"Playwright two-phase workflow failed: {str(e)}"
        logger.error(f"❌ {error_msg}")
        raise EnhancedWorkflowError(error_msg)


def _score_candidates(
    profiles: List[LinkedInProfile], 
    job_description: str
) -> ScoringResult:
    """
    Score a list of LinkedIn profiles against a job description.
    
    Args:
        profiles: List of LinkedInProfile objects to score
        job_description: Job description to score against
        
    Returns:
        ScoringResult object with scoring details
    """
    if not profiles:
        logger.warning("⚠️ No profiles to score")
        return ScoringResult(
            total_candidates=0,
            passed_candidates=[],
            failed_candidates=[],
            scored_candidates=[],
            scoring_time=0.0
        )
    
    scoring_start = time.time()
    logger.info(f"🎯 Scoring {len(profiles)} candidates...")
    
    scorer = CandidateScorer()
    scored_candidates = []
    passed_candidates = []
    failed_candidates = []
    
    for i, profile in enumerate(profiles, 1):
        try:
            logger.info(f"🎯 Scoring candidate {i}/{len(profiles)}: {profile.name}")
            scored_candidate = scorer.score_candidate(profile, job_description)
            scored_candidates.append(scored_candidate)
            
            if scored_candidate.passed:
                passed_candidates.append(scored_candidate)
                logger.info(f"✅ {profile.name} PASSED with score {scored_candidate.score:.1f}")
            else:
                failed_candidates.append(scored_candidate)
                logger.info(f"❌ {profile.name} FAILED with score {scored_candidate.score:.1f}")
                
        except Exception as e:
            logger.error(f"❌ Error scoring {profile.name}: {e}")
            # Create a failed score for this candidate
            failed_candidate = ScoredCandidate(
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
                score=0,
                score_breakdown=scorer._get_failed_candidate_score(profile).score_breakdown,
                reasoning=None,
                passed=False
            )
            scored_candidates.append(failed_candidate)
            failed_candidates.append(failed_candidate)
    
    scoring_time = time.time() - scoring_start
    
    logger.info(f"✅ Scoring completed in {scoring_time:.2f}s")
    logger.info(f"📊 Final results: {len(passed_candidates)} passed, {len(failed_candidates)} failed")
    
    return ScoringResult(
        total_candidates=len(profiles),
        passed_candidates=passed_candidates,
        failed_candidates=failed_candidates,
        scored_candidates=scored_candidates,
        scoring_time=scoring_time
    )


# Convenience functions for external use
def process_job_rapid_api(job_description: str, limit: int = 5) -> Tuple[SearchResult, ScoringResult]:
    """
    Convenience function for Rapid API workflow.
    """
    return search_with_rapid_api_and_score(job_description, limit)


async def process_job_playwright(job_description: str, limit: int = 5) -> Tuple[SearchResult, ScoringResult]:
    """
    Convenience function for Playwright workflow (legacy single-phase).
    """
    return await search_with_playwright_and_score(job_description, limit)


async def process_job_playwright_two_phase(job_description: str, limit: int = 5) -> Tuple[SearchResult, ScoringResult]:
    """
    Convenience function for Playwright workflow (new two-phase approach).
    Phase 1: Get URLs from Google, scrape all HTML, close browser
    Phase 2: Process all HTML files without browser, then score
    """
    return await search_with_playwright_two_phase_and_score(job_description, limit) 