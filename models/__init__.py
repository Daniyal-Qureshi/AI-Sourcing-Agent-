"""
Models package for LinkedIn Profile Extractor
"""
from .linkedin_profile import (
    LinkedInProfile,
    ExperienceEntry,
    EducationEntry,
    SearchResult,
    ExtractionResult,
    BatchExtractionResult,
    SessionData,
    validate_linkedin_url,
    clean_linkedin_url,
    create_profile_from_url
)

__all__ = [
    'LinkedInProfile',
    'ExperienceEntry', 
    'EducationEntry',
    'SearchResult',
    'ExtractionResult',
    'BatchExtractionResult',
    'SessionData',
    'validate_linkedin_url',
    'clean_linkedin_url',
    'create_profile_from_url'
] 