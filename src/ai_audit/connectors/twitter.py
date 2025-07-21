"""Twitter/X profile connector."""

import asyncio
from typing import Dict, Any, Optional, List
import tweepy
from datetime import datetime, timedelta

from . import BaseConnector
from ..models import ProfileData, Platform
from ..config import settings


class TwitterConnector(BaseConnector):
    """Connector for Twitter/X profiles."""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key or settings.twitter_bearer_token)
        self.client = None
        if self.api_key:
            self.client = tweepy.Client(bearer_token=self.api_key)
    
    def get_platform(self) -> Platform:
        return Platform.TWITTER
    
    def is_configured(self) -> bool:
        return self.api_key is not None
    
    async def get_profile_data(self, username: str) -> ProfileData:
        """Fetch Twitter profile data."""
        if not self.is_configured():
            raise ValueError("Twitter Bearer Token not configured")
        
        try:
            # Get user info
            user = self.client.get_user(
                username=username,
                user_fields=[
                    'created_at', 'description', 'location', 'name', 
                    'public_metrics', 'url', 'verified', 'profile_image_url'
                ]
            )
            
            if not user.data:
                raise ValueError(f"User {username} not found")
            
            user_data = user.data
            
            # Get recent tweets for analysis
            tweets_data = await self._get_recent_tweets(user_data.id)
            
            # Build profile text
            profile_text = self._build_profile_text(user_data, tweets_data)
            
            # Build metadata
            metrics = user_data.public_metrics or {}
            metadata = {
                "followers_count": metrics.get("followers_count", 0),
                "following_count": metrics.get("following_count", 0),
                "tweet_count": metrics.get("tweet_count", 0),
                "listed_count": metrics.get("listed_count", 0),
                "account_created": user_data.created_at.isoformat() if user_data.created_at else None,
                "verified": getattr(user_data, 'verified', False),
                "location": user_data.location,
                "website": user_data.url,
                "recent_tweets_count": len(tweets_data) if tweets_data else 0
            }
            
            raw_data = {
                "user_info": {
                    "id": user_data.id,
                    "username": user_data.username,
                    "name": user_data.name,
                    "description": user_data.description,
                    "location": user_data.location,
                    "url": user_data.url,
                    "verified": getattr(user_data, 'verified', False),
                    "created_at": user_data.created_at.isoformat() if user_data.created_at else None,
                    "public_metrics": metrics,
                },
                "recent_tweets": tweets_data if tweets_data else []
            } if settings.retain_raw_data else None
            
            if settings.anonymize_data and raw_data:
                raw_data = self.anonymize_data(raw_data)
            
            return ProfileData(
                platform=self.platform,
                username=username,
                user_id=str(user_data.id),
                profile_text=profile_text,
                metadata=metadata,
                raw_data=raw_data
            )
            
        except Exception as e:
            raise ValueError(f"Failed to fetch Twitter profile for {username}: {e}")
    
    def _build_profile_text(self, user_data, tweets_data: Optional[List[Dict]]) -> str:
        """Build a comprehensive text representation of the profile."""
        parts = []
        
        if user_data.name:
            parts.append(f"Name: {user_data.name}")
        
        if user_data.description:
            parts.append(f"Bio: {user_data.description}")
        
        if user_data.location:
            parts.append(f"Location: {user_data.location}")
        
        if user_data.url:
            parts.append(f"Website: {user_data.url}")
        
        metrics = user_data.public_metrics or {}
        parts.append(f"Followers: {metrics.get('followers_count', 0)}")
        parts.append(f"Following: {metrics.get('following_count', 0)}")
        parts.append(f"Tweets: {metrics.get('tweet_count', 0)}")
        
        if user_data.created_at:
            parts.append(f"Member since: {user_data.created_at.strftime('%B %Y')}")
        
        if tweets_data:
            parts.append(f"\nRecent tweet content (for analysis):")
            for i, tweet in enumerate(tweets_data[:5]):  # Limit to 5 tweets
                parts.append(f"Tweet {i+1}: {tweet['text'][:100]}...")
        
        return "\n".join(parts)
    
    async def _get_recent_tweets(self, user_id: str, max_tweets: int = 20) -> Optional[List[Dict[str, Any]]]:
        """Get recent tweets for content analysis."""
        try:
            tweets = self.client.get_users_tweets(
                id=user_id,
                max_results=min(max_tweets, 100),  # API limit
                tweet_fields=['created_at', 'public_metrics', 'context_annotations'],
                exclude=['retweets', 'replies']  # Focus on original content
            )
            
            if not tweets.data:
                return None
            
            tweets_data = []
            for tweet in tweets.data:
                tweet_info = {
                    "id": tweet.id,
                    "text": tweet.text,
                    "created_at": tweet.created_at.isoformat() if tweet.created_at else None,
                    "public_metrics": tweet.public_metrics if hasattr(tweet, 'public_metrics') else {},
                }
                
                # Add context annotations if available (topics, entities)
                if hasattr(tweet, 'context_annotations') and tweet.context_annotations:
                    contexts = []
                    for annotation in tweet.context_annotations:
                        if hasattr(annotation, 'entity'):
                            contexts.append({
                                "domain": annotation.domain.name if hasattr(annotation, 'domain') else None,
                                "entity": annotation.entity.name if hasattr(annotation, 'entity') else None
                            })
                    tweet_info["context_annotations"] = contexts
                
                tweets_data.append(tweet_info)
            
            return tweets_data
            
        except Exception as e:
            print(f"Warning: Could not fetch recent tweets: {e}")
            return None
