"""
Candidate Scorer using OpenAI
Replicates the scoring functionality from src/agent/scorer.ts
"""
import json
import logging
from typing import Dict, Any, Optional
from pydantic import BaseModel, ValidationError
from openai import OpenAI

from config.settings import get_openai_config
from models.linkedin_profile import LinkedInProfile

logger = logging.getLogger(__name__)

# Scoring threshold (same as TypeScript version)
THRESHOLD = 85


class ScoreBreakdown(BaseModel):
    """Score breakdown model matching TypeScript version."""
    education: float
    career_trajectory: float
    company_relevance: float
    experience_match: float
    location_match: float
    tenure: float


class ScoreReasoning(BaseModel):
    """Score reasoning model matching TypeScript version."""
    education: str
    career_trajectory: str
    company_relevance: str
    experience_match: str
    location_match: str
    tenure: str


class CandidateScore(BaseModel):
    """Complete candidate score model matching TypeScript version."""
    score: float
    score_breakdown: ScoreBreakdown
    reasoning: Optional[ScoreReasoning] = None


class ScoredCandidate(BaseModel):
    """Candidate with scoring information."""
    # All original candidate fields
    name: str
    headline: Optional[str]
    linkedin_url: str
    location: Optional[str]
    summary: Optional[str]
    experience: Optional[list] = None
    education: Optional[list] = None
    skills: Optional[list] = None
    connections: Optional[str] = None
    profile_image: Optional[str] = None
    current_company: Optional[str] = None
    current_position: Optional[str] = None
    
    # Scoring fields
    score: float
    score_breakdown: ScoreBreakdown
    reasoning: Optional[ScoreReasoning] = None
    passed: bool


class CandidateScorerError(Exception):
    """Custom exception for candidate scoring errors."""
    pass


class CandidateScorer:
    """
    Candidate scorer using OpenAI.
    Replicates the scoreCandidate function from TypeScript.
    """
    
    def __init__(self):
        self.openai_config = get_openai_config()
        try:
            self.openai_client = OpenAI(api_key=self.openai_config["api_key"])
            logger.info("✅ OpenAI client initialized for candidate scoring")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            raise CandidateScorerError(f"OpenAI initialization failed: {e}")
    
    def _format_experience(self, experience: Optional[list]) -> str:
        """Format experience entries for the prompt (same as TypeScript version)."""
        if not experience:
            return 'N/A'
        
        formatted_entries = []
        for exp in experience:
            exp_str = f"Title: {exp.title}\n"
            exp_str += f"Company: {exp.company}\n"
            exp_str += f"Date Range: {exp.date_range}\n"
            exp_str += f"Duration: {exp.duration or 'N/A'}\n"
            exp_str += f"Description: {exp.description or 'N/A'}"
            formatted_entries.append(exp_str)
        
        return '\n\n'.join(formatted_entries)
    
    def _format_education(self, education: Optional[list]) -> str:
        """Format education entries for the prompt (same as TypeScript version)."""
        if not education:
            return 'N/A'
        
        formatted_entries = []
        for edu in education:
            edu_str = f"School: {edu.school}\n"
            edu_str += f"Degree: {edu.degree or 'N/A'}\n"
            edu_str += f"Field of Study: {edu.field_of_study or 'N/A'}\n"
            edu_str += f"Date Range: {edu.date_range or 'N/A'}"
            formatted_entries.append(edu_str)
        
        return '\n\n'.join(formatted_entries)
    
    def score_candidate(self, candidate: LinkedInProfile, job_description: str) -> ScoredCandidate:
        """
        Score a candidate against a job description.
        Replicates the scoreCandidate function from TypeScript.
        """
        logger.info(f"🎯 Scoring candidate: {candidate.name}")
        
        # Same rubric as TypeScript version
        rubric = """
Rate the following candidate based on:

- Education (20%)
- Career Trajectory (20%)
- Company Relevance (15%)
- Experience Match (25%)
- Location Match (10%)
- Tenure (10%)

Return the response strictly in the following JSON format:

{
  "score_breakdown": {
    "education": number,
    "career_trajectory": number,
    "company_relevance": number,
    "experience_match": number,
    "location_match": number,
    "tenure": number
  },
  "score": number,
  "reasoning": {
    "education": string,
    "career_trajectory": string,
    "company_relevance": string,
    "experience_match": string,
    "location_match": string,
    "tenure": string
  }
}
"""
        
        prompt = f"""{rubric}

Candidate:
- Name: {candidate.name}
- Headline: {candidate.headline or 'N/A'}
- Location: {candidate.location or 'N/A'}
- Summary: {candidate.summary or 'N/A'}

Education:
{self._format_education(candidate.education)}

Experience:
{self._format_experience(candidate.experience)}

Job Description:
{job_description}
"""

        try:
            response = self.openai_client.chat.completions.create(
                model='gpt-4',
                temperature=0.2,
                messages=[
                    {
                        'role': 'system',
                        'content': 'You are an expert technical recruiter. Score candidates strictly using the rubric. Return ONLY the valid JSON response.',
                    },
                    {
                        'role': 'user',
                        'content': prompt,
                    },
                ],
            )
            
            content = response.choices[0].message.content
            logger.info(f"📄 Received scoring response for {candidate.name}")
            
            # Parse the JSON response
            score_data = json.loads(content)
            
            # Validate the structure
            candidate_score = CandidateScore(**score_data)
            
            # Calculate computed total for validation (same as TypeScript)
            breakdown = candidate_score.score_breakdown
            computed_total = (
                breakdown.education +
                breakdown.career_trajectory +
                breakdown.company_relevance +
                breakdown.experience_match +
                breakdown.location_match +
                breakdown.tenure
            )
            
            # Check for score mismatch (same as TypeScript)
            if abs(computed_total - candidate_score.score) > 3:
                logger.warning(f"Score mismatch detected for {candidate.name}: computed={computed_total}, received={candidate_score.score}")
            
            # Final score capped at 100
            final_score = min(candidate_score.score, 100)
            passed = final_score >= THRESHOLD
            
            logger.info(f"✅ Candidate {candidate.name} scored: {final_score:.1f} ({'PASSED' if passed else 'FAILED'})")
            
            # Create scored candidate object
            scored_candidate = ScoredCandidate(
                # Original candidate fields
                name=candidate.name,
                headline=candidate.headline,
                linkedin_url=candidate.linkedin_url,
                location=candidate.location,
                summary=candidate.summary,
                experience=candidate.experience,
                education=candidate.education,
                skills=candidate.skills,
                connections=candidate.connections,
                profile_image=candidate.profile_image,
                current_company=candidate.current_company,
                current_position=candidate.current_position,
                
                # Scoring fields
                score=final_score,
                score_breakdown=candidate_score.score_breakdown,
                reasoning=candidate_score.reasoning,
                passed=passed
            )
            
            return scored_candidate
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse scoring JSON for {candidate.name}: {e}")
            return self._get_failed_candidate_score(candidate)
        except ValidationError as e:
            logger.error(f"❌ Invalid scoring response structure for {candidate.name}: {e}")
            return self._get_failed_candidate_score(candidate)
        except Exception as e:
            logger.error(f"❌ Error scoring candidate {candidate.name}: {e}")
            return self._get_failed_candidate_score(candidate)
    
    def _get_failed_candidate_score(self, candidate: LinkedInProfile) -> ScoredCandidate:
        """Return a failed score for a candidate when scoring fails."""
        return ScoredCandidate(
            # Original candidate fields
            name=candidate.name,
            headline=candidate.headline,
            linkedin_url=candidate.linkedin_url,
            location=candidate.location,
            summary=candidate.summary,
            experience=candidate.experience,
            education=candidate.education,
            skills=candidate.skills,
            connections=candidate.connections,
            profile_image=candidate.profile_image,
            current_company=candidate.current_company,
            current_position=candidate.current_position,
            
            # Failed scoring fields
            score=0,
            score_breakdown=ScoreBreakdown(
                education=0,
                career_trajectory=0,
                company_relevance=0,
                experience_match=0,
                location_match=0,
                tenure=0
            ),
            reasoning=None,
            passed=False
        )


# Helper function for external use
def score_candidate_against_job(candidate: LinkedInProfile, job_description: str) -> ScoredCandidate:
    """
    Convenience function to score a candidate against a job description.
    
    Args:
        candidate: LinkedInProfile object to score
        job_description: Job description to score against
    
    Returns:
        ScoredCandidate object with scoring information
    """
    scorer = CandidateScorer()
    return scorer.score_candidate(candidate, job_description) 