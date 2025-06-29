"""
LinkedIn Profile Search using Rapid API
Replicates the functionality from src/agent/search.ts
"""
import asyncio
import json
import logging
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime

from models.linkedin_profile import LinkedInProfile, ExperienceEntry, EducationEntry

logger = logging.getLogger(__name__)


class RapidAPISearchError(Exception):
    """Custom exception for Rapid API search errors."""
    pass


class JobDescriptionFields:
    """Data class for job description fields."""
    
    def __init__(self, name: str = "[A-Za-Z]", job_title: str = "", location: str = "", limit: int = 5):
        self.name = name
        self.job_title = job_title
        self.location = location
        self.limit = limit
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "job_title": self.job_title,
            "location": self.location,
            "limit": self.limit
        }


class RapidAPILinkedInSearcher:
    """
    LinkedIn profile searcher using Rapid API.
    Replicates the getSearchLinkedIn function from TypeScript.
    """
    
    def __init__(self, api_key: str = None):
        # Use the same API key as in the TypeScript version for consistency
        self.api_key = api_key or '3868e60168msh0aab25223667a61p10f7c4jsn9b49a82037d9'
        self.base_url = 'https://fresh-linkedin-profile-data.p.rapidapi.com/google-full-profiles'
        
    def search_linkedin_profiles(self, job_fields: JobDescriptionFields) -> List[LinkedInProfile]:
        """
        Search LinkedIn profiles using Rapid API.
        Replicates the getSearchLinkedIn function from TypeScript.
        """
        logger.info(f"🔍 Starting Rapid API LinkedIn search...")
        logger.info(f"Job fields: {job_fields.to_dict()}")
        
        try:
            headers = {
                'Content-Type': 'application/json',
                'X-RapidAPI-Key': self.api_key,
                'X-RapidAPI-Host': 'fresh-linkedin-profile-data.p.rapidapi.com'
            }
            
            payload = job_fields.to_dict()
            
            logger.info(f"📡 Making API request to: {self.base_url}")
            response = requests.post(
                self.base_url,
                json=payload,
                headers=headers,
                timeout=30
            )
            
            response.raise_for_status()
            
            response_data = response.json()
            profiles_data = response_data.get('data', [])
            
            logger.info(f"✅ Received {len(profiles_data)} profiles from Rapid API")
            
            # Convert to LinkedInProfile objects
            profiles = []
            for profile_data in profiles_data:
                try:
                    profile = self._convert_to_linkedin_profile(profile_data)
                    profiles.append(profile)
                except Exception as e:
                    logger.warning(f"⚠️ Failed to convert profile: {e}")
                    continue
            
            logger.info(f"📊 Successfully converted {len(profiles)} profiles")
            return profiles
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ API request failed: {e}")
            raise RapidAPISearchError(f"API request failed: {e}")
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            raise RapidAPISearchError(f"Unexpected error: {e}")
    
    def _convert_to_linkedin_profile(self, profile_data: Dict[str, Any]) -> LinkedInProfile:
        """Convert Rapid API response data to LinkedInProfile object."""
        
        # Extract experience data
        experience_entries = []
        if profile_data.get('experiences'):
            for exp_data in profile_data['experiences']:
                try:
                    experience = ExperienceEntry(
                        title=exp_data.get('title', ''),
                        company=exp_data.get('company', ''),
                        date_range=exp_data.get('date_range'),
                        duration=exp_data.get('duration'),
                        location=exp_data.get('location'),
                        description=exp_data.get('description')
                    )
                    experience_entries.append(experience)
                except Exception as e:
                    logger.warning(f"⚠️ Failed to parse experience entry: {e}")
                    continue
        
        # Extract education data
        education_entries = []
        if profile_data.get('educations'):
            for edu_data in profile_data['educations']:
                try:
                    education = EducationEntry(
                        school=edu_data.get('school', ''),
                        degree=edu_data.get('degree'),
                        field_of_study=edu_data.get('field_of_study'),
                        date_range=edu_data.get('date_range')
                    )
                    education_entries.append(education)
                except Exception as e:
                    logger.warning(f"⚠️ Failed to parse education entry: {e}")
                    continue
        
        # Create LinkedInProfile object
        profile = LinkedInProfile(
            name=profile_data.get('full_name', 'Unknown'),
            headline=profile_data.get('headline'),
            linkedin_url=profile_data.get('linkedin_url', ''),
            location=profile_data.get('location'),
            summary=profile_data.get('about'),
            experience=experience_entries if experience_entries else None,
            education=education_entries if education_entries else None,
            skills=profile_data.get('skills'),
            connections=profile_data.get('connections'),
            profile_image=profile_data.get('profile_image'),
            current_company=profile_data.get('current_company'),
            current_position=profile_data.get('current_position'),
            extracted_at=datetime.now(),
            extraction_method="Rapid API"
        )
        
        return profile


# Helper function for external use
def search_profiles_via_rapid_api(
    job_title: str = "",
    location: str = "",
    limit: int = 5,
    api_key: str = None
) -> List[LinkedInProfile]:
    """
    Convenience function to search LinkedIn profiles via Rapid API.
    
    Args:
        job_title: Job title to search for
        location: Location to search in
        limit: Maximum number of profiles to return
        api_key: Rapid API key (optional)
    
    Returns:
        List of LinkedInProfile objects
    """
    job_fields = JobDescriptionFields(
        name="[A-Za-Z]",
        job_title=job_title,
        location=location,
        limit=limit
    )
    
    searcher = RapidAPILinkedInSearcher(api_key)
    return searcher.search_linkedin_profiles(job_fields) 