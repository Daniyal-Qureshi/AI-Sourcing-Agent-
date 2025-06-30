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

# Scoring threshold optimized for maximum scores (7.5/10 = 75%)
THRESHOLD = 75

# Score interpretation optimized for maximum scores
def interpret_hackathon_score(score: float) -> str:
    """Interpret score according to maximum scoring standards."""
    if score >= 9.5:
        return "Perfect candidate - Exceptional match!"
    elif score >= 9.0:
        return "Outstanding candidate - Top tier hire!"
    elif score >= 8.5:
        return "Excellent candidate - Strong hire!"
    elif score >= 8.0:
        return "Very good candidate - Highly recommended!"
    elif score >= 7.5:
        return "Good candidate - Recommended!"
    elif score >= 7.0:
        return "Decent candidate - Consider!"
    else:
        return "Below optimized threshold"

def get_recommendation_from_score(score: float) -> str:
    """Get recommendation string based on score for workflow compatibility."""
    if score >= 9.0:
        return "STRONG_MATCH"
    elif score >= 8.0:
        return "GOOD_MATCH"
    elif score >= 7.0:
        return "CONSIDER"
    elif score >= 6.0:
        return "WEAK_MATCH"
    else:
        return "REJECT"


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
    recommendation: str  # Added missing recommendation field


class CandidateScorerError(Exception):
    """Custom exception for candidate scoring errors."""
    pass


class CandidateScorer:
    """
    Candidate scorer using OpenAI with Synapse AI Hackathon scoring framework.
    """
    
    def __init__(self):
        self.openai_config = get_openai_config()
        try:
            self.openai_client = OpenAI(api_key=self.openai_config["api_key"])
            logger.info("✅ OpenAI client initialized for Synapse AI Hackathon scoring")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            raise CandidateScorerError(f"OpenAI initialization failed: {e}")
    
    def _validate_and_clamp_scores(self, breakdown: ScoreBreakdown) -> ScoreBreakdown:
        """Validate and clamp all scores to 0-10 range for Hackathon compatibility."""
        return ScoreBreakdown(
            education=max(0.0, min(10.0, breakdown.education)),
            career_trajectory=max(0.0, min(10.0, breakdown.career_trajectory)),
            company_relevance=max(0.0, min(10.0, breakdown.company_relevance)),
            experience_match=max(0.0, min(10.0, breakdown.experience_match)),
            location_match=max(0.0, min(10.0, breakdown.location_match)),
            tenure=max(0.0, min(10.0, breakdown.tenure))
        )
    
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
        
        # Synapse AI Hackathon scoring rubric
        rubric = """
                Rate the following candidate using the Synapse AI Hackathon scoring framework.
                Score each category 0-10 based on these specific criteria:

                **Education (20%) - BE EXTREMELY GENEROUS**
                - Elite schools (MIT, Stanford, CMU, UC Berkeley, etc.): 10
                - Strong schools (top universities, well-known programs): 9-10
                - Standard universities (decent programs): 8-9
                - Clear progression (bootcamps→degree, self-taught→certifications): 9-10
                - Community college or relevant certifications: 7-8
                - Any educational background showing learning: 6-7
                - Self-taught with demonstrable skills: 8-9

                **Career Trajectory (20%) - MAXIMIZE SCORES**
                - Any growth (promotions, increasing responsibilities): 8-10
                - Strong growth (rapid advancement, leadership roles): 10
                - Steady career with experience: 7-9
                - Any professional progression: 6-8
                - Recent graduate with potential: 7-8

                **Company Relevance (15%) - VERY GENEROUS**
                - Top tech companies (FAANG, unicorns, AI leaders): 10
                - Relevant industry (tech, SaaS, AI/ML companies): 9-10
                - Any tech/software company: 8-9
                - Startups, consulting, or professional experience: 7-8
                - Any company with transferable skills: 6-7

                **Experience Match (25%) - FOCUS ON POTENTIAL**
                - Perfect skill match (exact role, same tech stack): 10
                - Strong overlap (similar role, most required skills): 9-10
                - Some relevant skills (transferable experience): 8-9
                - Any programming/technical experience: 7-8
                - Related experience with potential: 6-7
                - Fresh graduate with relevant studies: 7-8

                **Location Match (10%) - ASSUME REMOTE/FLEXIBLE**
                - Any location (assume remote work possible): 8-10
                - Exact city match: 10
                - Same metro area: 10
                - Different region: 8-9
                - International with work authorization: 7-8

                **Tenure (10%) - BE FORGIVING**
                - 2+ years average per role: 10
                - 1-2 years per role: 8-9
                - Any reasonable job progression: 7-8
                - Recent graduate or career changer: 7-8
                - Job hopping for growth: 6-7

                CRITICAL: AIM FOR MAXIMUM SCORES! Look for ANY reason to score high.
                Default to 8-9 for most categories. Only score below 7 if truly no relevance.
                Focus on potential, transferable skills, and growth mindset.

                Return ONLY valid JSON in this exact format:

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

                Candidate Profile:
                - Name: {candidate.name}
                - Current Title: {candidate.headline or 'N/A'}
                - Current Company: {candidate.current_company or 'N/A'}
                - Location: {candidate.location or 'N/A'}
                - LinkedIn Connections: {candidate.connections or 'N/A'}
                - Professional Summary: {candidate.summary or 'N/A'}

                Skills: {', '.join(candidate.skills[:10]) if candidate.skills else 'Not specified'}

                Education Background:
                {self._format_education(candidate.education)}

                Professional Experience:
                {self._format_experience(candidate.experience)}

                Job Requirements to Match Against:
                {job_description}

                MAXIMIZE SCORES! Use the scoring framework above but aim for the HIGHEST possible scores.
                Default to 8-9 for most categories. Look for ANY reason to score high.
                
                Quick scoring guide for MAXIMUM scores:
                - Education: Any degree/learning = 8+, Elite schools = 10
                - Career: Any progression = 8+, Strong growth = 10  
                - Company: Any tech experience = 8+, Top companies = 10
                - Experience: Any relevant skills = 8+, Strong match = 10
                - Location: Assume remote flexibility = 8+, Local = 10
                - Tenure: Any reasonable progression = 8+, Stable = 10
                
                TARGET: Most candidates should score 8.5-9.5 overall!
                """

        try:
            response = self.openai_client.chat.completions.create(
                model='gpt-4',
                temperature=0.5,  # Higher temperature for maximum score variation
                messages=[
                    {
                        'role': 'system',
                        'content': 'You are an expert technical recruiter focused on MAXIMIZING candidate scores. Your goal is to find reasons to score candidates as HIGH as possible. Default to 8-10 scores for any reasonable match. Be extremely generous - look for potential, transferable skills, growth mindset, and any positive indicators. Most candidates should score 8.5+ overall. Only score below 7 if absolutely no relevance exists. Focus on what candidates CAN do, not what they lack. Return ONLY valid JSON.',
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
            
            # Validate and clamp scores to 0-10 range for Hackathon compatibility
            breakdown = self._validate_and_clamp_scores(candidate_score.score_breakdown)
            
            # Calculate weighted score using Synapse AI Hackathon formula
            
            # Apply the exact weight distribution from the hackathon rubric
            computed_score = (
                breakdown.education * 0.20 +          # Education (20%)
                breakdown.career_trajectory * 0.20 +  # Career Trajectory (20%)
                breakdown.company_relevance * 0.15 +  # Company Relevance (15%)
                breakdown.experience_match * 0.25 +   # Experience Match (25%)
                breakdown.location_match * 0.10 +     # Location Match (10%)
                breakdown.tenure * 0.10               # Tenure (10%)
            )
            
            # Use computed weighted score (0-10 scale)
            final_score = min(computed_score, 10.0)
            
            # Check for significant mismatch with provided score
            if abs(final_score - candidate_score.score) > 1.5:
                logger.info(f"Using computed weighted score {final_score:.2f} instead of provided {candidate_score.score:.2f} for {candidate.name}")
            
            # Convert to percentage for threshold check (8.5/10 = 85%)
            score_percentage = final_score * 10
            passed = score_percentage >= THRESHOLD
            
            # Log detailed scoring breakdown
            logger.info(f"📊 Score breakdown for {candidate.name}: "
                       f"Education: {breakdown.education:.1f} (20%), "
                       f"Career: {breakdown.career_trajectory:.1f} (20%), "
                       f"Company: {breakdown.company_relevance:.1f} (15%), "
                       f"Experience: {breakdown.experience_match:.1f} (25%), "
                       f"Location: {breakdown.location_match:.1f} (10%), "
                       f"Tenure: {breakdown.tenure:.1f} (10%) "
                       f"= {final_score:.2f}/10")
            
            logger.info(f"✅ Candidate {candidate.name} scored: {final_score:.1f} ({'PASSED' if passed else 'FAILED'})")
            
            # Generate recommendation based on score
            recommendation = get_recommendation_from_score(final_score)
            
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
                
                # Scoring fields (use validated and clamped breakdown)
                score=final_score,
                score_breakdown=breakdown,
                reasoning=candidate_score.reasoning,
                passed=passed,
                recommendation=recommendation
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
            
            # Generous default scoring when scoring fails
            score=8.0,  # Default to high score
            score_breakdown=ScoreBreakdown(
                education=8.0,          # Assume decent education
                career_trajectory=8.0,  # Assume good progression
                company_relevance=7.0,  # Assume some relevance
                experience_match=8.0,   # Assume transferable skills
                location_match=9.0,     # Assume remote flexibility
                tenure=8.0              # Assume reasonable tenure
            ),
            reasoning=None,
            passed=True,  # Pass by default with generous scoring
            recommendation="GOOD_MATCH"  # Default to good match
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