"""
LinkedIn Profile Data Models
"""
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict, Any
from datetime import datetime


class ExperienceEntry(BaseModel):
    """Represents a single work experience entry."""
    title: str = Field(..., description="Job title")
    company: str = Field(..., description="Company name")
    date_range: Optional[str] = Field(None, description="Date range (e.g., 'Jan 2020 - Present')")
    duration: Optional[str] = Field(None, description="Duration (e.g., '2 yrs 3 mos')")
    location: Optional[str] = Field(None, description="Job location")
    description: Optional[str] = Field(None, description="Job description")


class EducationEntry(BaseModel):
    """Represents a single education entry."""
    school: str = Field(..., description="School/University name")
    degree: Optional[str] = Field(None, description="Degree type (e.g., 'Bachelor's', 'Master's')")
    field_of_study: Optional[str] = Field(None, description="Field of study")
    date_range: Optional[str] = Field(None, description="Date range")


class LinkedInProfile(BaseModel):
    """
    Represents the complete LinkedIn profile data structure.
    Combines data from both deepseek crawler and playwright approaches.
    """
    
    # Core profile information
    name: str = Field(..., description="Full name")
    headline: Optional[str] = Field(None, description="Professional headline")
    linkedin_url: str = Field(..., description="LinkedIn profile URL")
    location: Optional[str] = Field(None, description="Location (City, State, Country)")
    summary: Optional[str] = Field(None, description="About/Summary section")
    
    # Professional experience
    experience: Optional[List[ExperienceEntry]] = Field(None, description="Work experience entries")
    
    # Education
    education: Optional[List[EducationEntry]] = Field(None, description="Education entries")
    
    # Skills and connections
    skills: Optional[List[str]] = Field(None, description="List of skills")
    connections: Optional[str] = Field(None, description="Number of connections")
    
    # Additional profile data
    profile_image: Optional[str] = Field(None, description="Profile image URL")
    current_company: Optional[str] = Field(None, description="Current company")
    current_position: Optional[str] = Field(None, description="Current job title")
    
    # Metadata
    extracted_at: Optional[datetime] = Field(None, description="When the profile was extracted")
    extraction_method: Optional[str] = Field(None, description="Method used for extraction")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SearchResult(BaseModel):
    """Represents a Google search result for LinkedIn profiles."""
    search_query: str = Field(..., description="The search query used")
    search_terms: List[str] = Field(..., description="Individual search terms")
    total_results: int = Field(..., description="Total number of results found")
    profiles: List[str] = Field(..., description="List of LinkedIn profile URLs")
    searched_at: datetime = Field(..., description="When the search was performed")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ExtractionResult(BaseModel):
    """Represents the result of a profile extraction operation."""
    success: bool = Field(..., description="Whether extraction was successful")
    profile: Optional[LinkedInProfile] = Field(None, description="Extracted profile data")
    error: Optional[str] = Field(None, description="Error message if extraction failed")
    
    
class BatchExtractionResult(BaseModel):
    """Represents the result of a batch profile extraction operation."""
    total_profiles: int = Field(..., description="Total number of profiles to extract")
    successful_extractions: int = Field(..., description="Number of successful extractions")
    failed_extractions: int = Field(..., description="Number of failed extractions")
    profiles: List[LinkedInProfile] = Field(..., description="Successfully extracted profiles")
    errors: List[str] = Field(..., description="List of error messages")
    extraction_started_at: datetime = Field(..., description="When batch extraction started")
    extraction_completed_at: datetime = Field(..., description="When batch extraction completed")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SessionData(BaseModel):
    """Represents LinkedIn session data for authentication."""
    cookies: List[Dict[str, Any]] = Field(..., description="Browser cookies")
    timestamp: int = Field(..., description="Session creation timestamp")
    user_agent: str = Field(..., description="User agent string")
    is_valid: bool = Field(True, description="Whether session is still valid")
    
    
# Utility functions for data validation
def validate_linkedin_url(url: str) -> bool:
    """Validate that a URL is a valid LinkedIn profile URL."""
    return (
        url.startswith("https://www.linkedin.com/in/") or 
        url.startswith("https://linkedin.com/in/")
    ) and not any(excluded in url for excluded in ["dir/", "title/", "#", "?"])


def clean_linkedin_url(url: str) -> str:
    """Clean and normalize a LinkedIn profile URL."""
    # Remove tracking parameters
    clean_url = url.split('?')[0].split('#')[0]
    
    # Ensure it ends without trailing slash
    if clean_url.endswith('/'):
        clean_url = clean_url[:-1]
    
    # Ensure it starts with https://
    if not clean_url.startswith('https://'):
        if clean_url.startswith('linkedin.com'):
            clean_url = 'https://www.' + clean_url
        elif clean_url.startswith('www.linkedin.com'):
            clean_url = 'https://' + clean_url
    
    return clean_url


def create_profile_from_url(url: str, name: str = None) -> LinkedInProfile:
    """Create a basic LinkedIn profile from a URL."""
    clean_url = clean_linkedin_url(url)
    
    # Extract name from URL if not provided
    if not name:
        url_parts = clean_url.split('/')
        linkedin_id = url_parts[-1] if url_parts else "unknown"
        name = linkedin_id.replace('-', ' ').title()
    
    return LinkedInProfile(
        name=name,
        linkedin_url=clean_url,
        extraction_method="URL extraction",
        extracted_at=datetime.now()
    ) 