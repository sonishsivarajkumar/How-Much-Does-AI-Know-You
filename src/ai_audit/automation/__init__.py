"""Automated remediation system."""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import json

from ..models import RemediationAction, ProfileData, Inference, Platform, Recommendation
from ..config import settings
from ..storage import db


class RemediationEngine:
    """Automated remediation engine for privacy issues."""
    
    def __init__(self):
        self.actions_queue = []
        self.active_actions = {}
    
    async def analyze_and_create_actions(
        self, 
        profile_data: List[ProfileData], 
        inferences: List[Inference],
        recommendations: List[Recommendation]
    ) -> List[RemediationAction]:
        """Analyze data and create automated remediation actions."""
        actions = []
        
        # Create actions based on high-risk inferences
        high_risk_inferences = [i for i in inferences if i.confidence >= 0.8]
        
        for inference in high_risk_inferences:
            if inference.type.value == "location" and inference.confidence >= 0.8:
                actions.extend(await self._create_location_remediation_actions(inference, profile_data))
            
            elif inference.type.value == "work_schedule" and inference.confidence >= 0.7:
                actions.extend(await self._create_schedule_remediation_actions(inference, profile_data))
            
            elif inference.type.value == "programming_skills" and inference.confidence >= 0.9:
                actions.extend(await self._create_skills_remediation_actions(inference, profile_data))
        
        # Create actions based on direct metadata exposure
        for profile in profile_data:
            actions.extend(await self._create_metadata_remediation_actions(profile))
        
        return actions
    
    async def _create_location_remediation_actions(
        self, 
        inference: Inference, 
        profile_data: List[ProfileData]
    ) -> List[RemediationAction]:
        """Create actions to reduce location exposure."""
        actions = []
        
        for profile in profile_data:
            if profile.platform in inference.source_platforms:
                if profile.metadata.get('location'):
                    action = RemediationAction(
                        action_id=f"remove_location_{profile.platform.value}_{datetime.now().timestamp()}",
                        action_type="update_privacy",
                        platform=profile.platform,
                        description=f"Remove location information from {profile.platform.value} profile",
                        scheduled_for=datetime.now() + timedelta(hours=1)
                    )
                    actions.append(action)
        
        return actions
    
    async def _create_schedule_remediation_actions(
        self, 
        inference: Inference, 
        profile_data: List[ProfileData]
    ) -> List[RemediationAction]:
        """Create actions to reduce schedule pattern exposure."""
        actions = []
        
        for profile in profile_data:
            if profile.platform == Platform.GITHUB and profile.platform in inference.source_platforms:
                action = RemediationAction(
                    action_id=f"randomize_commits_{profile.platform.value}_{datetime.now().timestamp()}",
                    action_type="update_privacy",
                    platform=profile.platform,
                    description="Enable commit timestamp randomization to obscure work schedule patterns",
                    scheduled_for=datetime.now() + timedelta(hours=2)
                )
                actions.append(action)
        
        return actions
    
    async def _create_skills_remediation_actions(
        self, 
        inference: Inference, 
        profile_data: List[ProfileData]
    ) -> List[RemediationAction]:
        """Create actions to manage skills exposure."""
        actions = []
        
        for profile in profile_data:
            if profile.platform == Platform.GITHUB and profile.platform in inference.source_platforms:
                repos = profile.metadata.get('repositories', [])
                experimental_repos = [r for r in repos if r.get('description', '').lower().find('experiment') != -1]
                
                if experimental_repos:
                    action = RemediationAction(
                        action_id=f"archive_experimental_repos_{profile.platform.value}_{datetime.now().timestamp()}",
                        action_type="update_privacy",
                        platform=profile.platform,
                        description=f"Archive {len(experimental_repos)} experimental repositories to reduce skills noise",
                        scheduled_for=datetime.now() + timedelta(hours=24)
                    )
                    actions.append(action)
        
        return actions
    
    async def _create_metadata_remediation_actions(self, profile: ProfileData) -> List[RemediationAction]:
        """Create actions for direct metadata exposure."""
        actions = []
        
        # Check for email exposure
        if profile.metadata.get('email'):
            action = RemediationAction(
                action_id=f"remove_email_{profile.platform.value}_{datetime.now().timestamp()}",
                action_type="remove_data",
                platform=profile.platform,
                description=f"Remove public email address from {profile.platform.value} profile",
                scheduled_for=datetime.now() + timedelta(minutes=30)
            )
            actions.append(action)
        
        # Check for excessive personal website links
        if profile.metadata.get('blog') or profile.metadata.get('website'):
            action = RemediationAction(
                action_id=f"review_links_{profile.platform.value}_{datetime.now().timestamp()}",
                action_type="update_privacy",
                platform=profile.platform,
                description=f"Review and potentially remove personal website links from {profile.platform.value}",
                scheduled_for=datetime.now() + timedelta(hours=4)
            )
            actions.append(action)
        
        return actions
    
    async def execute_action(self, action: RemediationAction) -> bool:
        """Execute a remediation action."""
        try:
            action.status = "in_progress"
            await db.update_remediation_action(action)
            
            success = await self._execute_platform_action(action)
            
            if success:
                action.status = "completed"
                action.completed_at = datetime.now()
            else:
                action.status = "failed"
                action.error_message = "Platform-specific execution failed"
            
            await db.update_remediation_action(action)
            return success
            
        except Exception as e:
            action.status = "failed"
            action.error_message = str(e)
            await db.update_remediation_action(action)
            return False
    
    async def _execute_platform_action(self, action: RemediationAction) -> bool:
        """Execute platform-specific remediation action."""
        if action.platform == Platform.GITHUB:
            return await self._execute_github_action(action)
        elif action.platform == Platform.TWITTER:
            return await self._execute_twitter_action(action)
        elif action.platform == Platform.REDDIT:
            return await self._execute_reddit_action(action)
        elif action.platform == Platform.LINKEDIN:
            return await self._execute_linkedin_action(action)
        else:
            print(f"Platform {action.platform} not supported for automated actions")
            return False
    
    async def _execute_github_action(self, action: RemediationAction) -> bool:
        """Execute GitHub-specific action."""
        print(f"🔧 Executing GitHub action: {action.description}")
        
        if action.action_type == "remove_data":
            # For demo: simulate removing email from profile
            print("  • Simulating email removal from GitHub profile")
            await asyncio.sleep(1)
            return True
        
        elif action.action_type == "update_privacy":
            if "location" in action.description.lower():
                print("  • Simulating location removal from GitHub profile")
                await asyncio.sleep(1)
                return True
            elif "commit" in action.description.lower():
                print("  • Simulating commit timestamp randomization setup")
                await asyncio.sleep(2)
                return True
            elif "archive" in action.description.lower():
                print("  • Simulating repository archival")
                await asyncio.sleep(1)
                return True
        
        return False
    
    async def _execute_twitter_action(self, action: RemediationAction) -> bool:
        """Execute Twitter-specific action."""
        print(f"🔧 Executing Twitter action: {action.description}")
        
        if action.action_type == "remove_data":
            print("  • Simulating data removal from Twitter profile")
            await asyncio.sleep(1)
            return True
        
        elif action.action_type == "update_privacy":
            print("  • Simulating Twitter privacy settings update")
            await asyncio.sleep(1)
            return True
        
        return False
    
    async def _execute_reddit_action(self, action: RemediationAction) -> bool:
        """Execute Reddit-specific action."""
        print(f"🔧 Executing Reddit action: {action.description}")
        
        if action.action_type == "remove_data":
            print("  • Simulating data removal from Reddit profile")
            await asyncio.sleep(1)
            return True
        
        return False
    
    async def _execute_linkedin_action(self, action: RemediationAction) -> bool:
        """Execute LinkedIn-specific action."""
        print(f"🔧 Executing LinkedIn action: {action.description}")
        
        if action.action_type == "update_privacy":
            print("  • Simulating LinkedIn privacy settings update")
            await asyncio.sleep(1)
            return True
        
        return False
    
    async def schedule_and_execute_actions(self, actions: List[RemediationAction]):
        """Schedule and execute remediation actions."""
        print(f"📅 Scheduling {len(actions)} remediation actions...")
        
        # Store actions in database
        for action in actions:
            await db.store_remediation_action(action)
        
        # Sort by scheduled time
        actions.sort(key=lambda x: x.scheduled_for or datetime.now())
        
        for action in actions:
            # Wait until scheduled time
            wait_time = (action.scheduled_for - datetime.now()).total_seconds()
            if wait_time > 0:
                print(f"⏰ Waiting {wait_time:.0f} seconds for action: {action.description}")
                await asyncio.sleep(min(wait_time, 10))  # Cap wait time for demo
            
            # Execute action
            success = await self.execute_action(action)
            status_emoji = "✅" if success else "❌"
            print(f"{status_emoji} Action {action.action_id}: {action.status}")
            
            # Brief pause between actions
            await asyncio.sleep(1)
    
    async def rollback_action(self, action_id: str) -> bool:
        """Rollback a completed remediation action."""
        try:
            action = await db.get_remediation_action(action_id)
            if not action or action.status != "completed":
                return False
            
            print(f"🔄 Rolling back action: {action.description}")
            
            # Execute rollback based on action type
            if action.rollback_info:
                # Use stored rollback information
                rollback_success = await self._execute_rollback(action)
            else:
                # Generic rollback
                rollback_success = await self._generic_rollback(action)
            
            if rollback_success:
                action.status = "rolled_back"
                await db.update_remediation_action(action)
                print("✅ Rollback completed successfully")
            else:
                print("❌ Rollback failed")
            
            return rollback_success
            
        except Exception as e:
            print(f"❌ Rollback error: {e}")
            return False
    
    async def _execute_rollback(self, action: RemediationAction) -> bool:
        """Execute rollback using stored rollback information."""
        print(f"  • Executing specific rollback for {action.action_type}")
        await asyncio.sleep(1)
        return True
    
    async def _generic_rollback(self, action: RemediationAction) -> bool:
        """Execute generic rollback."""
        print(f"  • Executing generic rollback for {action.action_type}")
        await asyncio.sleep(1)
        return True
    
    async def get_action_status(self, action_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a remediation action."""
        action = await db.get_remediation_action(action_id)
        if not action:
            return None
        
        return {
            "action_id": action.action_id,
            "status": action.status,
            "description": action.description,
            "platform": action.platform.value,
            "scheduled_for": action.scheduled_for.isoformat() if action.scheduled_for else None,
            "completed_at": action.completed_at.isoformat() if action.completed_at else None,
            "error_message": action.error_message
        }


class SmartRemediation:
    """Smart remediation with ML-based recommendations."""
    
    def __init__(self):
        self.remediation_engine = RemediationEngine()
    
    async def suggest_optimal_actions(
        self, 
        profile_data: List[ProfileData], 
        inferences: List[Inference]
    ) -> List[RemediationAction]:
        """Use ML to suggest optimal remediation actions."""
        # This could integrate with ML models to predict effectiveness
        actions = await self.remediation_engine.analyze_and_create_actions(
            profile_data, inferences, []
        )
        
        # Sort by predicted effectiveness (mock for now)
        actions.sort(key=lambda x: self._calculate_action_effectiveness(x), reverse=True)
        
        return actions
    
    def _calculate_action_effectiveness(self, action: RemediationAction) -> float:
        """Calculate predicted effectiveness of an action."""
        # Mock effectiveness calculation
        effectiveness_map = {
            "remove_data": 0.9,
            "update_privacy": 0.7,
            "contact_platform": 0.5
        }
        
        base_effectiveness = effectiveness_map.get(action.action_type, 0.5)
        
        # Adjust based on platform
        platform_multipliers = {
            Platform.GITHUB: 1.2,
            Platform.TWITTER: 1.0,
            Platform.LINKEDIN: 0.8,
            Platform.REDDIT: 0.9
        }
        
        multiplier = platform_multipliers.get(action.platform, 1.0)
        return base_effectiveness * multiplier
