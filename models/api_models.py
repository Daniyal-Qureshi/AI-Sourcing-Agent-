"""
API Models for LinkedIn Profile Sourcing FastAPI Server
"""
from __future__ import annotations
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class JobRequest(BaseModel):
    """Request model for job description processing."""
    job_description: str = Field(..., description="The job description to process")
    search_method: str = Field("rapid_api", description="Search method: 'rapid_api' or 'playwright_crawler'")
    limit: int = Field(5, ge=1, le=50, description="Maximum number of candidates to search for")
    cache_key: Optional[str] = Field(None, description="Optional cache key for this job type")


class JobResponse(BaseModel):
    """Response model for job submission."""
    job_id: str = Field(..., description="Unique job identifier")
    status: str = Field(..., description="Job status")
    message: str = Field(..., description="Status message")
    estimated_completion: Optional[str] = Field(None, description="Estimated completion time")
    data: Optional[Dict[str, Any]] = Field(None, description="Immediate results if available from cache")


class JobStatus(BaseModel):
    """Model for job status information."""
    job_id: str
    status: str  # queued, processing, completed, failed
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    progress: Optional[int] = None  # 0-100
    message: Optional[str] = None
    error: Optional[str] = None
    total_candidates: Optional[int] = None
    passed_candidates: Optional[int] = None
    results: Optional[SearchResults] = None  # Include results if available


class CandidateInfo(BaseModel):
    """Model for candidate information."""
    name: str
    linkedin_url: str
    fit_score: float
    score_breakdown: Dict[str, Any]
    outreach_message: Optional[str] = None
    
    # Optional fields for backward compatibility
    headline: Optional[str] = None
    location: Optional[str] = None
    passed: Optional[bool] = None


class SearchResults(BaseModel):
    """Model for search results."""
    job_id: str
    total_candidates: int
    passed_candidates: int
    failed_candidates: int
    pass_rate: str
    search_method: str
    search_time: float
    scoring_time: float
    candidates: List[CandidateInfo]
    cached: bool = False 