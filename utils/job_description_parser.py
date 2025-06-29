"""
Job Description Parser using OpenAI
Replicates the extractJobFields functionality from src/agent/search.ts
"""
import json
import logging
import re
from typing import Dict, Any
from openai import OpenAI

from config.settings import get_openai_config
from utils.rapid_api_search import JobDescriptionFields

logger = logging.getLogger(__name__)


class JobDescriptionParserError(Exception):
    """Custom exception for job description parsing errors."""
    pass


class JobDescriptionParser:
    """
    Parses job descriptions to extract structured job information.
    Replicates the extractJobFields function from TypeScript.
    """
    
    def __init__(self):
        self.openai_config = get_openai_config()
        try:
            self.openai_client = OpenAI(api_key=self.openai_config["api_key"])
            logger.info("✅ OpenAI client initialized for job description parsing")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            raise JobDescriptionParserError(f"OpenAI initialization failed: {e}")
    
    def extract_job_fields(self, job_description: str) -> JobDescriptionFields:
        """
        Extract structured job information from job description using OpenAI.
        Replicates the extractJobFields function from TypeScript.
        """
        logger.info("🤖 Extracting job fields from description using OpenAI...")
        
        prompt = f"""
You are an AI assistant that extracts structured job information from job descriptions. Your task is to analyze the provided job description and extract specific fields into a JSON object.

Extract the following fields:
- job_title: The specific job title/position being offered
- location: The job location (city, state, or country)
- limit: Number of candidates to search for (default to 5)

Job Description:
{job_description}

Return only the JSON object in this exact format:
{{
  "job_title": "extracted_job_title",
  "location": "extracted_location",
  "limit": 5
}}

Do not include any additional text or explanations, just the JSON object.
"""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
            )
            
            content = response.choices[0].message.content
            logger.info(f"📄 Received OpenAI response: {content}")
            
            # Extract JSON from the response (same logic as TypeScript version)
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                parsed_data = json.loads(json_match.group(0))
                
                # Create JobDescriptionFields object
                job_fields = JobDescriptionFields(
                    name="[A-Za-Z]",  # Default name pattern
                    job_title=parsed_data.get("job_title", ""),
                    location=parsed_data.get("location", ""),
                    limit=parsed_data.get("limit", 5)
                )
                
                logger.info(f"✅ Successfully extracted job fields: {job_fields.to_dict()}")
                return job_fields
            else:
                raise ValueError("No JSON found in OpenAI response")
                
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse JSON from OpenAI response: {e}")
            return self._get_default_job_fields()
        except Exception as e:
            logger.error(f"❌ Error extracting job fields: {e}")
            return self._get_default_job_fields()
    
    def _get_default_job_fields(self) -> JobDescriptionFields:
        """Return default job fields if parsing fails."""
        logger.info("⚠️ Using default job fields due to parsing failure")
        return JobDescriptionFields(
            name="[A-Za-Z]",
            job_title="machine learning engineer",
            location="Mountain View",
            limit=5
        )


# Helper function for external use
def parse_job_description(job_description: str) -> JobDescriptionFields:
    """
    Convenience function to parse job description and extract job fields.
    
    Args:
        job_description: The job description text to parse
    
    Returns:
        JobDescriptionFields object with extracted information
    """
    parser = JobDescriptionParser()
    return parser.extract_job_fields(job_description) 