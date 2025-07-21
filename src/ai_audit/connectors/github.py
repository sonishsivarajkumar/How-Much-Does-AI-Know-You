"""GitHub profile connector."""

import asyncio
from typing import Dict, Any, Optional, List
from github import Github, GithubException
from datetime import datetime, timedelta

from . import BaseConnector
from ..models import ProfileData, Platform
from ..config import settings


class GitHubConnector(BaseConnector):
    """Connector for GitHub profiles."""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key or settings.github_token)
        self.client = Github(self.api_key) if self.api_key else None
    
    def get_platform(self) -> Platform:
        return Platform.GITHUB
    
    def is_configured(self) -> bool:
        return self.api_key is not None
    
    async def get_profile_data(self, username: str) -> ProfileData:
        """Fetch GitHub profile data."""
        if not self.is_configured():
            raise ValueError("GitHub token not configured")
        
        try:
            user = self.client.get_user(username)
            
            # Collect basic profile info
            profile_text = self._build_profile_text(user)
            
            # Collect repositories for analysis
            repos_data = await self._get_repositories_data(user)
            
            # Build metadata
            metadata = {
                "followers": user.followers,
                "following": user.following,
                "public_repos": user.public_repos,
                "account_created": user.created_at.isoformat() if user.created_at else None,
                "last_updated": user.updated_at.isoformat() if user.updated_at else None,
                "location": user.location,
                "company": user.company,
                "blog": user.blog,
                "repositories": repos_data
            }
            
            raw_data = {
                "user_info": {
                    "login": user.login,
                    "name": user.name,
                    "bio": user.bio,
                    "location": user.location,
                    "company": user.company,
                    "blog": user.blog,
                    "email": user.email,
                    "hireable": user.hireable,
                    "public_repos": user.public_repos,
                    "followers": user.followers,
                    "following": user.following,
                    "created_at": user.created_at.isoformat() if user.created_at else None,
                    "updated_at": user.updated_at.isoformat() if user.updated_at else None,
                }
            } if settings.retain_raw_data else None
            
            if settings.anonymize_data and raw_data:
                raw_data = self.anonymize_data(raw_data)
            
            return ProfileData(
                platform=self.platform,
                username=username,
                user_id=str(user.id),
                profile_text=profile_text,
                metadata=metadata,
                raw_data=raw_data
            )
            
        except GithubException as e:
            raise ValueError(f"Failed to fetch GitHub profile for {username}: {e}")
    
    def _build_profile_text(self, user) -> str:
        """Build a comprehensive text representation of the profile."""
        parts = []
        
        if user.name:
            parts.append(f"Name: {user.name}")
        
        if user.bio:
            parts.append(f"Bio: {user.bio}")
        
        if user.location:
            parts.append(f"Location: {user.location}")
        
        if user.company:
            parts.append(f"Company: {user.company}")
        
        if user.blog:
            parts.append(f"Website: {user.blog}")
        
        parts.append(f"Public repositories: {user.public_repos}")
        parts.append(f"Followers: {user.followers}")
        parts.append(f"Following: {user.following}")
        
        if user.created_at:
            parts.append(f"Member since: {user.created_at.strftime('%B %Y')}")
        
        return "\n".join(parts)
    
    async def _get_repositories_data(self, user, max_repos: int = 10) -> List[Dict[str, Any]]:
        """Get data from user's repositories."""
        repos_data = []
        
        try:
            repos = user.get_repos(sort="updated", direction="desc")
            
            count = 0
            for repo in repos:
                if count >= max_repos:
                    break
                
                # Skip forks for privacy
                if repo.fork:
                    continue
                
                repo_info = {
                    "name": repo.name,
                    "description": repo.description,
                    "language": repo.language,
                    "stars": repo.stargazers_count,
                    "forks": repo.forks_count,
                    "created_at": repo.created_at.isoformat() if repo.created_at else None,
                    "updated_at": repo.updated_at.isoformat() if repo.updated_at else None,
                    "topics": repo.get_topics() if hasattr(repo, 'get_topics') else [],
                }
                
                # Get commit patterns (privacy-conscious)
                commit_patterns = await self._get_commit_patterns(repo)
                if commit_patterns:
                    repo_info["commit_patterns"] = commit_patterns
                
                repos_data.append(repo_info)
                count += 1
                
        except Exception as e:
            print(f"Warning: Could not fetch repository data: {e}")
        
        return repos_data
    
    async def _get_commit_patterns(self, repo) -> Optional[Dict[str, Any]]:
        """Analyze commit patterns for schedule inference."""
        try:
            # Get commits from last 3 months
            since = datetime.now() - timedelta(days=90)
            commits = repo.get_commits(since=since)
            
            hour_counts = [0] * 24
            day_counts = [0] * 7
            commit_count = 0
            
            for commit in commits:
                if commit_count >= 100:  # Limit to prevent rate limiting
                    break
                
                commit_date = commit.commit.author.date
                if commit_date:
                    hour_counts[commit_date.hour] += 1
                    day_counts[commit_date.weekday()] += 1
                    commit_count += 1
            
            if commit_count > 0:
                return {
                    "total_commits": commit_count,
                    "peak_hour": hour_counts.index(max(hour_counts)),
                    "peak_day": day_counts.index(max(day_counts)),
                    "hour_distribution": hour_counts,
                    "day_distribution": day_counts
                }
                
        except Exception as e:
            print(f"Warning: Could not analyze commit patterns: {e}")
        
        return None
