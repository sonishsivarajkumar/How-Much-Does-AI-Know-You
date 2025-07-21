"""Reddit profile connector."""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from . import BaseConnector
from ..models import ProfileData, Platform
from ..config import settings


class RedditConnector(BaseConnector):
    """Connector for Reddit profiles."""
    
    def __init__(self, client_id: Optional[str] = None, client_secret: Optional[str] = None):
        super().__init__(client_id or settings.reddit_client_id)
        self.client_secret = client_secret or settings.reddit_client_secret
        self.reddit = None
        
        if self.is_configured():
            try:
                import praw
                self.reddit = praw.Reddit(
                    client_id=self.api_key,
                    client_secret=self.client_secret,
                    user_agent="AI-Audit/0.1.0 (Privacy Analysis Tool)"
                )
            except ImportError:
                print("Warning: praw library not installed. Run: pip install praw")
    
    def get_platform(self) -> Platform:
        return Platform.REDDIT
    
    def is_configured(self) -> bool:
        return self.api_key is not None and self.client_secret is not None
    
    async def get_profile_data(self, username: str) -> ProfileData:
        """Fetch Reddit profile data."""
        if not self.is_configured():
            raise ValueError("Reddit API credentials not configured")
        
        if not self.reddit:
            raise ValueError("Reddit client not initialized")
        
        try:
            user = self.reddit.redditor(username)
            
            # Get user info
            try:
                # This will trigger an API call and raise exception if user doesn't exist
                created_utc = user.created_utc
            except Exception:
                raise ValueError(f"Reddit user {username} not found or suspended")
            
            # Collect recent comments and submissions
            comments_data = await self._get_recent_comments(user)
            submissions_data = await self._get_recent_submissions(user)
            
            # Build profile text
            profile_text = self._build_profile_text(user, comments_data, submissions_data)
            
            # Build metadata
            metadata = {
                "account_created": datetime.fromtimestamp(created_utc).isoformat(),
                "comment_karma": getattr(user, 'comment_karma', 0),
                "link_karma": getattr(user, 'link_karma', 0),
                "is_gold": getattr(user, 'is_gold', False),
                "is_mod": getattr(user, 'is_mod', False),
                "has_verified_email": getattr(user, 'has_verified_email', False),
                "recent_comments_count": len(comments_data) if comments_data else 0,
                "recent_submissions_count": len(submissions_data) if submissions_data else 0,
            }
            
            # Activity patterns
            activity_patterns = self._analyze_activity_patterns(comments_data, submissions_data)
            if activity_patterns:
                metadata["activity_patterns"] = activity_patterns
            
            raw_data = {
                "user_info": {
                    "name": username,
                    "id": getattr(user, 'id', None),
                    "created_utc": created_utc,
                    "comment_karma": metadata["comment_karma"],
                    "link_karma": metadata["link_karma"],
                    "is_gold": metadata["is_gold"],
                    "is_mod": metadata["is_mod"],
                },
                "recent_comments": comments_data if comments_data else [],
                "recent_submissions": submissions_data if submissions_data else []
            } if settings.retain_raw_data else None
            
            if settings.anonymize_data and raw_data:
                raw_data = self.anonymize_data(raw_data)
            
            return ProfileData(
                platform=self.platform,
                username=username,
                user_id=getattr(user, 'id', None),
                profile_text=profile_text,
                metadata=metadata,
                raw_data=raw_data
            )
            
        except Exception as e:
            raise ValueError(f"Failed to fetch Reddit profile for {username}: {e}")
    
    def _build_profile_text(self, user, comments_data: Optional[List], submissions_data: Optional[List]) -> str:
        """Build comprehensive text representation."""
        parts = []
        
        parts.append(f"Reddit user: {user.name}")
        parts.append(f"Account created: {datetime.fromtimestamp(user.created_utc).strftime('%B %Y')}")
        parts.append(f"Comment karma: {getattr(user, 'comment_karma', 0)}")
        parts.append(f"Link karma: {getattr(user, 'link_karma', 0)}")
        
        if getattr(user, 'is_gold', False):
            parts.append("Reddit Gold member")
        
        if getattr(user, 'is_mod', False):
            parts.append("Moderator status")
        
        # Analyze comment content for interests
        if comments_data:
            parts.append(f"\nRecent comment topics (last {len(comments_data)} comments):")
            subreddits = {}
            for comment in comments_data:
                subreddit = comment.get('subreddit', 'unknown')
                subreddits[subreddit] = subreddits.get(subreddit, 0) + 1
            
            top_subreddits = sorted(subreddits.items(), key=lambda x: x[1], reverse=True)[:5]
            for subreddit, count in top_subreddits:
                parts.append(f"  r/{subreddit}: {count} comments")
        
        # Analyze submission content
        if submissions_data:
            parts.append(f"\nRecent submissions (last {len(submissions_data)} posts):")
            for submission in submissions_data[:3]:
                title = submission.get('title', '')[:100]
                subreddit = submission.get('subreddit', 'unknown')
                parts.append(f"  r/{subreddit}: {title}...")
        
        return "\n".join(parts)
    
    async def _get_recent_comments(self, user, limit: int = 25) -> Optional[List[Dict[str, Any]]]:
        """Get recent comments for analysis."""
        try:
            comments_data = []
            
            for comment in user.comments.new(limit=limit):
                try:
                    comment_info = {
                        "id": comment.id,
                        "body": comment.body[:500],  # Limit content length
                        "score": comment.score,
                        "subreddit": str(comment.subreddit),
                        "created_utc": comment.created_utc,
                        "is_submitter": comment.is_submitter,
                    }
                    comments_data.append(comment_info)
                except Exception as e:
                    # Skip comments we can't access
                    continue
            
            return comments_data if comments_data else None
            
        except Exception as e:
            print(f"Warning: Could not fetch recent comments: {e}")
            return None
    
    async def _get_recent_submissions(self, user, limit: int = 10) -> Optional[List[Dict[str, Any]]]:
        """Get recent submissions for analysis."""
        try:
            submissions_data = []
            
            for submission in user.submissions.new(limit=limit):
                try:
                    submission_info = {
                        "id": submission.id,
                        "title": submission.title,
                        "selftext": submission.selftext[:500] if submission.selftext else "",
                        "score": submission.score,
                        "subreddit": str(submission.subreddit),
                        "created_utc": submission.created_utc,
                        "num_comments": submission.num_comments,
                        "upvote_ratio": submission.upvote_ratio,
                        "is_self": submission.is_self,
                    }
                    submissions_data.append(submission_info)
                except Exception as e:
                    # Skip submissions we can't access
                    continue
            
            return submissions_data if submissions_data else None
            
        except Exception as e:
            print(f"Warning: Could not fetch recent submissions: {e}")
            return None
    
    def _analyze_activity_patterns(self, comments_data: Optional[List], submissions_data: Optional[List]) -> Optional[Dict[str, Any]]:
        """Analyze user activity patterns."""
        try:
            all_timestamps = []
            
            if comments_data:
                all_timestamps.extend([c['created_utc'] for c in comments_data])
            
            if submissions_data:
                all_timestamps.extend([s['created_utc'] for s in submissions_data])
            
            if not all_timestamps:
                return None
            
            # Convert to datetime objects
            datetimes = [datetime.fromtimestamp(ts) for ts in all_timestamps]
            
            # Analyze patterns
            hour_counts = [0] * 24
            day_counts = [0] * 7
            
            for dt in datetimes:
                hour_counts[dt.hour] += 1
                day_counts[dt.weekday()] += 1
            
            return {
                "total_activities": len(all_timestamps),
                "peak_hour": hour_counts.index(max(hour_counts)),
                "peak_day": day_counts.index(max(day_counts)),
                "hour_distribution": hour_counts,
                "day_distribution": day_counts,
                "most_recent_activity": max(all_timestamps),
                "activity_span_days": (max(all_timestamps) - min(all_timestamps)) / 86400 if len(all_timestamps) > 1 else 0
            }
            
        except Exception as e:
            print(f"Warning: Could not analyze activity patterns: {e}")
            return None
