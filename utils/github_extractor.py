import asyncio
import aiohttp
import json
import base64
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
import logging
from openai import AsyncOpenAI
from config.settings import OPENAI_API_KEY, GITHUB_TOKEN

logger = logging.getLogger(__name__)

@dataclass
class GitHubRepository:
    """GitHub repository information"""
    name: str
    full_name: str
    description: Optional[str] = None
    language: Optional[str] = None
    languages: Dict[str, int] = field(default_factory=dict)
    stars: int = 0
    forks: int = 0
    url: str = ""
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)

@dataclass
class GitHubProfile:
    """Complete GitHub profile information"""
    username: str
    name: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    company: Optional[str] = None
    blog: Optional[str] = None
    email: Optional[str] = None
    public_repos: int = 0
    followers: int = 0
    following: int = 0
    created_at: Optional[str] = None
    repositories: List[GitHubRepository] = field(default_factory=list)
    top_languages: Dict[str, int] = field(default_factory=dict)
    readme_content: Optional[str] = None
    ai_extracted_info: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        # Convert repository objects to dictionaries
        data['repositories'] = [repo.to_dict() if hasattr(repo, 'to_dict') else asdict(repo) for repo in self.repositories]
        return data

class GitHubExtractor:
    """Extract comprehensive GitHub profile data"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
        self.base_url = "https://api.github.com"
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def _format_github_username(self, full_name: str) -> str:
        """Format full name for GitHub username search"""
        # Remove common titles and clean the name
        name = re.sub(r'\b(Mr\.?|Ms\.?|Mrs\.?|Dr\.?|Prof\.?)\s+', '', full_name, flags=re.IGNORECASE)
        
        # Split into parts and join with +
        name_parts = name.strip().split()
        if len(name_parts) >= 2:
            return f"{name_parts[0]}+{name_parts[1]}"
        else:
            return name_parts[0] if name_parts else full_name

    async def _make_github_request(self, url: str) -> Optional[Dict[str, Any]]:
        """Make GitHub API request with error handling"""
        try:
            headers = {
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'LinkedIn-Profile-Extractor'
            }
            
            # Add GitHub token authentication if available
            if GITHUB_TOKEN:
                headers['Authorization'] = f'token {GITHUB_TOKEN}'
                logger.debug(f"🔑 Using GitHub token authentication for request: {url}")
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 404:
                    logger.debug(f"GitHub resource not found: {url}")
                    return None
                else:
                    logger.warning(f"GitHub API error {response.status}: {url}")
                    return None
                    
        except Exception as e:
            logger.error(f"GitHub API request failed: {e}")
            return None

    async def search_github_user(self, full_name: str) -> Optional[str]:
        """Search for GitHub username based on full name"""
        try:
            # Try different username formats
            search_queries = [
                self._format_github_username(full_name),
                full_name.replace(' ', '-'),
                full_name.replace(' ', ''),
                full_name.replace(' ', '_'),
                full_name.split()[0] if ' ' in full_name else full_name
            ]
            
            for query in search_queries:
                # Search users API
                search_url = f"{self.base_url}/search/users?q={query}&type=Users&per_page=5"
                search_result = await self._make_github_request(search_url)
                
                if search_result and 'items' in search_result:
                    for user in search_result['items']:
                        # Check if name matches closely
                        user_name = user.get('login', '').lower()
                        if any(part.lower() in user_name for part in full_name.split() if len(part) > 2):
                            logger.info(f"🎯 Found GitHub user: {user['login']} for {full_name}")
                            return user['login']
            
            logger.debug(f"No GitHub user found for: {full_name}")
            return None
            
        except Exception as e:
            logger.error(f"GitHub user search failed: {e}")
            return None

    async def get_user_repositories(self, username: str) -> List[GitHubRepository]:
        """Get all repositories for a user"""
        try:
            repos_url = f"{self.base_url}/users/{username}/repos?per_page=100&sort=updated"
            repos_data = await self._make_github_request(repos_url)
            
            if not repos_data:
                return []
            
            repositories = []
            
            # Process repositories in batches for languages
            for repo_data in repos_data:
                try:
                    # Get repository languages
                    languages_url = f"{self.base_url}/repos/{repo_data['full_name']}/languages"
                    languages_data = await self._make_github_request(languages_url)
                    
                    repo = GitHubRepository(
                        name=repo_data.get('name', ''),
                        full_name=repo_data.get('full_name', ''),
                        description=repo_data.get('description'),
                        language=repo_data.get('language'),
                        languages=languages_data or {},
                        stars=repo_data.get('stargazers_count', 0),
                        forks=repo_data.get('forks_count', 0),
                        url=repo_data.get('html_url', ''),
                        created_at=repo_data.get('created_at'),
                        updated_at=repo_data.get('updated_at')
                    )
                    
                    repositories.append(repo)
                    
                    # Add small delay to respect rate limits
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.debug(f"Error processing repo {repo_data.get('name')}: {e}")
                    continue
            
            logger.info(f"📦 Found {len(repositories)} repositories for {username}")
            return repositories
            
        except Exception as e:
            logger.error(f"Failed to get repositories for {username}: {e}")
            return []

    async def get_user_profile(self, username: str) -> Optional[Dict[str, Any]]:
        """Get GitHub user profile information"""
        try:
            logger.info(f"👤 Fetching GitHub profile for: {username}")
            
            profile_url = f"{self.base_url}/users/{username}"
            profile_data = await self._make_github_request(profile_url)
            
            if profile_data:
                logger.info(f"✅ Retrieved GitHub profile for {username}")
                logger.info(f"📋 Profile summary:")
                logger.info(f"   👤 Name: {profile_data.get('name', 'N/A')}")
                logger.info(f"   📧 Email: {profile_data.get('email', 'N/A')}")
                logger.info(f"   📍 Location: {profile_data.get('location', 'N/A')}")
                logger.info(f"   🏢 Company: {profile_data.get('company', 'N/A')}")
                logger.info(f"   🌐 Blog: {profile_data.get('blog', 'N/A')}")
                logger.info(f"   📝 Bio: {profile_data.get('bio', 'N/A')}")
                logger.info(f"   📦 Public repos: {profile_data.get('public_repos', 0)}")
                logger.info(f"   👥 Followers: {profile_data.get('followers', 0)}")
                logger.info(f"   👥 Following: {profile_data.get('following', 0)}")
                logger.info(f"   📅 Created: {profile_data.get('created_at', 'N/A')}")
            else:
                logger.warning(f"❌ No profile data found for {username}")
                
            return profile_data
            
        except Exception as e:
            logger.error(f"💥 Failed to get profile for {username}: {e}")
            return None

    async def get_user_readme(self, username: str) -> Optional[str]:
        """Get user's README content from their profile repository"""
        try:
            # Try to get README from username/username repository
            readme_url = f"{self.base_url}/repos/{username}/{username}/readme"
            readme_data = await self._make_github_request(readme_url)
            
            if readme_data and 'content' in readme_data:
                # Decode base64 content
                content = base64.b64decode(readme_data['content']).decode('utf-8')
                logger.info(f"📄 Retrieved README for {username}")
                return content
            
            return None
            
        except Exception as e:
            logger.debug(f"No README found for {username}: {e}")
            return None

    def _calculate_top_languages(self, repositories: List[GitHubRepository]) -> Dict[str, int]:
        """Calculate top programming languages from repositories"""
        logger.info(f"💻 Calculating top languages from {len(repositories)} repositories")
        
        language_stats = {}
        
        for repo in repositories:
            for language, bytes_count in repo.languages.items():
                if language in language_stats:
                    language_stats[language] += bytes_count
                else:
                    language_stats[language] = bytes_count
        
        # Sort by usage and return top languages
        sorted_languages = sorted(language_stats.items(), key=lambda x: x[1], reverse=True)
        top_languages = dict(sorted_languages[:10])  # Top 10 languages
        
        logger.info(f"📊 Top languages calculated: {list(top_languages.keys())}")
        
        return top_languages

    async def _analyze_readme_with_ai(self, readme_content: str, username: str) -> Dict[str, Any]:
        """Analyze README content with AI to extract profile information"""
        if not self.openai_client or not readme_content:
            return {}
        
        try:
            prompt = f"""
            Analyze this GitHub README profile for {username} and extract relevant professional information:

            README Content:
            {readme_content[:3000]}  # Limit content length

            Extract and return JSON with:
            1. skills: List of technical skills mentioned
            2. projects: List of notable projects with descriptions
            3. achievements: Notable achievements or contributions
            4. technologies: Technologies/frameworks mentioned
            5. experience_level: Estimated experience level (junior/mid/senior)
            6. specialization: Main area of expertise
            7. contact_info: Any contact information found
            8. certifications: Any certifications mentioned
            9. education: Educational background if mentioned
            10. summary: Brief professional summary

            Return only valid JSON:
            """
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional profile analyzer. Extract structured information from GitHub README profiles. Return only valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0,
                max_tokens=1000
            )
            
            result = response.choices[0].message.content.strip()
            clean_json = result.replace('```json\n', '').replace('```\n', '').replace('```', '').strip()
            
            ai_data = json.loads(clean_json)
            logger.info(f"🤖 AI analysis completed for {username}")
            return ai_data
            
        except Exception as e:
            logger.warning(f"AI README analysis failed for {username}: {e}")
            return {}

    async def extract_github_profile(self, full_name: str) -> Optional[GitHubProfile]:
        """Extract complete GitHub profile data"""
        try:
            logger.info(f"🔍 Starting comprehensive GitHub extraction for: {full_name}")
            logger.info("=" * 60)
            
            # Search for GitHub username
            username = await self.search_github_user(full_name)
            if not username:
                logger.warning(f"🚫 GitHub extraction aborted - no username found for: {full_name}")
                return None
            
            logger.info(f"✅ GitHub username found: {username}")
            
            # Get user profile information
            profile_data = await self.get_user_profile(username)
            if not profile_data:
                logger.error(f"❌ GitHub extraction failed - no profile data for: {username}")
                return None
            
            # Get repositories with languages
            repositories = await self.get_user_repositories(username)
            
            # Calculate top languages
            top_languages = self._calculate_top_languages(repositories)
            
            # Get README content
            readme_content = await self.get_user_readme(username)
            
            # Analyze README with AI
            ai_extracted_info = {}
            if readme_content:
                ai_extracted_info = await self._analyze_readme_with_ai(readme_content, username)
            
            # Build complete GitHub profile
            github_profile = GitHubProfile(
                username=username,
                name=profile_data.get('name'),
                bio=profile_data.get('bio'),
                location=profile_data.get('location'),
                company=profile_data.get('company'),
                blog=profile_data.get('blog'),
                email=profile_data.get('email'),
                public_repos=profile_data.get('public_repos', 0),
                followers=profile_data.get('followers', 0),
                following=profile_data.get('following', 0),
                created_at=profile_data.get('created_at'),
                repositories=repositories,
                top_languages=top_languages,
                readme_content=readme_content,
                ai_extracted_info=ai_extracted_info
            )
            
            logger.info("🎉 GitHub extraction completed successfully!")
            logger.info(f"📊 Final extraction summary for {username}:")
            logger.info(f"   👤 Profile: {github_profile.name or 'N/A'}")
            logger.info(f"   📍 Location: {github_profile.location or 'N/A'}")
            logger.info(f"   🏢 Company: {github_profile.company or 'N/A'}")
            logger.info(f"   📦 Repositories: {len(github_profile.repositories)}")
            logger.info(f"   💻 Top languages: {list(github_profile.top_languages.keys())}")
            logger.info(f"   📄 README: {'Yes' if github_profile.readme_content else 'No'}")
            logger.info(f"   🤖 AI insights: {'Yes' if github_profile.ai_extracted_info else 'No'}")
            logger.info("=" * 60)
            
            return github_profile
            
        except Exception as e:
            logger.error(f"💥 GitHub extraction failed for {full_name}: {e}")
            return None

    def merge_with_linkedin_profile(self, linkedin_profile: Dict[str, Any], github_profile: GitHubProfile) -> Dict[str, Any]:
        """Merge GitHub data with LinkedIn profile"""
        try:
            logger.info(f"🔗 Starting merge of GitHub data with LinkedIn profile")
            logger.info(f"👤 LinkedIn profile: {linkedin_profile.get('name', 'N/A')}")
            logger.info(f"🐙 GitHub profile: {github_profile.username}")
            
            # Add GitHub languages to skills
            github_languages = list(github_profile.top_languages.keys())
            existing_skills = linkedin_profile.get('skills', [])
            combined_skills = list(set(existing_skills + github_languages))
            
            logger.info(f"🎯 Skills enhancement:")
            logger.info(f"   📋 Original skills: {existing_skills}")
            logger.info(f"   💻 GitHub languages: {github_languages}")
            logger.info(f"   ✨ Combined skills: {combined_skills}")
            
            # Enhanced location syncing logic
            linkedin_location = linkedin_profile.get('location')
            github_location = github_profile.location
            
            logger.info(f"📍 Location synchronization:")
            logger.info(f"   📋 LinkedIn location: {linkedin_location or 'Not provided'}")
            logger.info(f"   🐙 GitHub location: {github_location or 'Not provided'}")
            
            # Sync location from GitHub if missing or empty in LinkedIn
            if github_location and (not linkedin_location or linkedin_location.strip() == ""):
                linkedin_profile['location'] = github_location
                logger.info(f"✅ Location updated from GitHub: {github_location}")
            elif linkedin_location and github_location and linkedin_location != github_location:
                logger.info(f"ℹ️ Different locations found - kept LinkedIn: '{linkedin_location}' vs GitHub: '{github_location}'")
            elif not github_location and not linkedin_location:
                logger.info(f"⚠️ No location information available in either profile")
            else:
                logger.info(f"✅ Location already available in LinkedIn: {linkedin_location}")
            
            # Sync other profile fields if missing in LinkedIn
            synced_fields = []
            
            # Sync company if missing
            if github_profile.company and not linkedin_profile.get('company'):
                linkedin_profile['company'] = github_profile.company
                synced_fields.append(f"company: {github_profile.company}")
            
            # Sync bio/summary if missing
            if github_profile.bio and not linkedin_profile.get('summary') and not linkedin_profile.get('about'):
                linkedin_profile['summary'] = github_profile.bio
                synced_fields.append(f"summary: {github_profile.bio[:50]}...")
            
            # Sync blog/website if missing
            if github_profile.blog and not linkedin_profile.get('website'):
                linkedin_profile['website'] = github_profile.blog
                synced_fields.append(f"website: {github_profile.blog}")
            
            if synced_fields:
                logger.info(f"🔄 Additional fields synced from GitHub: {', '.join(synced_fields)}")
            
            # Prepare notable repositories
            notable_repositories = [
                {
                    'name': repo.name,
                    'description': repo.description,
                    'language': repo.language,
                    'stars': repo.stars,
                    'url': repo.url
                }
                for repo in sorted(github_profile.repositories, key=lambda r: r.stars, reverse=True)[:5]
            ]
            
            logger.info(f"⭐ Top 5 repositories by stars:")
            for i, repo in enumerate(notable_repositories, 1):
                logger.info(f"   {i}. {repo['name']} ({repo['stars']} ⭐) - {repo['description'] or 'No description'}")
            
            # Add GitHub-specific information
            github_data = {
                'username': github_profile.username,
                'profile_url': f"https://github.com/{github_profile.username}",
                'bio': github_profile.bio,
                'company': github_profile.company,
                'blog': github_profile.blog,
                'location': github_profile.location,  # Store original GitHub location
                'public_repos': github_profile.public_repos,
                'followers': github_profile.followers,
                'following': github_profile.following,
                'top_languages': github_profile.top_languages,
                'notable_repositories': notable_repositories,
                'ai_insights': github_profile.ai_extracted_info,
                'created_at': github_profile.created_at
            }
            
            linkedin_profile['github_data'] = github_data
            
            # Update skills with combined data
            linkedin_profile['skills'] = combined_skills
            
            logger.info(f"✅ GitHub data successfully merged with LinkedIn profile")
            logger.info(f"📊 Merge summary:")
            logger.info(f"   👤 Profile enhanced: {linkedin_profile.get('name')}")
            logger.info(f"   🎯 Total skills: {len(combined_skills)}")
            logger.info(f"   📍 Final location: {linkedin_profile.get('location', 'Not provided')}")
            logger.info(f"   📦 GitHub repos: {github_profile.public_repos}")
            logger.info(f"   👥 GitHub followers: {github_profile.followers}")
            logger.info(f"   💻 Top language: {list(github_profile.top_languages.keys())[0] if github_profile.top_languages else 'N/A'}")
            
            return linkedin_profile
            
        except Exception as e:
            logger.error(f"💥 Failed to merge GitHub data: {e}")
            return linkedin_profile


# Standalone function for easy integration
async def enhance_profile_with_github(linkedin_profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enhance LinkedIn profile with GitHub data
    
    Args:
        linkedin_profile: LinkedIn profile dictionary
    
    Returns:
        Enhanced profile with GitHub information
    """
    try:
        full_name = linkedin_profile.get('name')
        if not full_name:
            logger.warning("⚠️ No name found in LinkedIn profile - cannot enhance with GitHub")
            return linkedin_profile
        
        logger.info(f"🚀 Starting GitHub enhancement for LinkedIn profile: {full_name}")
        
        async with GitHubExtractor() as extractor:
            github_profile = await extractor.extract_github_profile(full_name)
            
            if github_profile:
                enhanced_profile = extractor.merge_with_linkedin_profile(linkedin_profile, github_profile)
                logger.info(f"🎉 GitHub enhancement completed successfully for {full_name}")
                return enhanced_profile
            else:
                logger.info(f"ℹ️ No GitHub profile found for {full_name} - returning original profile")
                return linkedin_profile
                
    except Exception as e:
        logger.error(f"💥 GitHub enhancement failed: {e}")
        return linkedin_profile 