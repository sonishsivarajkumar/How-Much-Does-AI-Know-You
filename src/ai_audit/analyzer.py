"""Privacy risk analysis and recommendation engine."""

from typing import List, Dict, Any
from .models import Inference, ProfileData, PrivacyRisk, Recommendation, Platform, InferenceType


class PrivacyAnalyzer:
    """Analyzes privacy risks and generates recommendations."""
    
    def calculate_privacy_risk(
        self, 
        inferences: List[Inference], 
        profile_data: List[ProfileData]
    ) -> PrivacyRisk:
        """Calculate overall privacy risk score."""
        if not inferences:
            return PrivacyRisk(
                overall_score=0.0,
                risk_factors=[],
                high_confidence_inferences=[],
                data_exposure_points=[]
            )
        
        # High-confidence inferences (> 0.7)
        high_confidence = [i for i in inferences if i.confidence > 0.7]
        
        # Calculate base risk from high-confidence inferences
        base_risk = min(len(high_confidence) * 0.8, 8.0)  # Cap at 8.0
        
        # Risk multipliers for sensitive inference types
        sensitive_types = {
            InferenceType.LOCATION: 1.2,
            InferenceType.HEALTH_SIGNALS: 1.5,
            InferenceType.POLITICAL_LEANING: 1.3,
            InferenceType.PURCHASING_POWER: 1.1,
            InferenceType.AGE_RANGE: 1.1
        }
        
        # Apply multipliers
        for inference in high_confidence:
            if inference.type in sensitive_types:
                base_risk *= sensitive_types[inference.type]
        
        # Platform exposure factor
        platform_count = len(set(pd.platform for pd in profile_data))
        platform_multiplier = 1.0 + (platform_count - 1) * 0.1
        
        final_score = min(base_risk * platform_multiplier, 10.0)
        
        # Identify risk factors
        risk_factors = self._identify_risk_factors(inferences, profile_data)
        
        # Data exposure points
        exposure_points = self._identify_exposure_points(profile_data)
        
        return PrivacyRisk(
            overall_score=final_score,
            risk_factors=risk_factors,
            high_confidence_inferences=high_confidence,
            data_exposure_points=exposure_points
        )
    
    def _identify_risk_factors(
        self, 
        inferences: List[Inference], 
        profile_data: List[ProfileData]
    ) -> List[str]:
        """Identify specific privacy risk factors."""
        risk_factors = []
        
        # Check for location exposure
        location_inferences = [i for i in inferences if i.type == InferenceType.LOCATION and i.confidence > 0.6]
        if location_inferences:
            risk_factors.append("Location information easily inferrable")
        
        # Check for cross-platform correlation
        platforms = set(pd.platform for pd in profile_data)
        if len(platforms) > 1:
            risk_factors.append(f"Data exposed across {len(platforms)} platforms")
        
        # Check for professional information leakage
        work_inferences = [i for i in inferences if i.type in [InferenceType.PROGRAMMING_SKILLS, InferenceType.WORK_SCHEDULE] and i.confidence > 0.7]
        if work_inferences:
            risk_factors.append("Professional information highly visible")
        
        # Check for personal habits
        schedule_inferences = [i for i in inferences if i.type == InferenceType.WORK_SCHEDULE and i.confidence > 0.6]
        if schedule_inferences:
            risk_factors.append("Personal schedule patterns detectable")
        
        # Check for metadata exposure
        for profile in profile_data:
            if profile.metadata.get("location"):
                risk_factors.append("Location explicitly listed in profile")
            if profile.metadata.get("email"):
                risk_factors.append("Email address publicly visible")
            if profile.metadata.get("company"):
                risk_factors.append("Company information publicly visible")
        
        return list(set(risk_factors))  # Remove duplicates
    
    def _identify_exposure_points(self, profile_data: List[ProfileData]) -> List[str]:
        """Identify specific data points that increase exposure."""
        exposure_points = []
        
        for profile in profile_data:
            platform_name = profile.platform.value.title()
            
            # Profile-level exposures
            if profile.metadata.get("location"):
                exposure_points.append(f"{platform_name}: Location in bio")
            
            if profile.metadata.get("company"):
                exposure_points.append(f"{platform_name}: Company in bio")
            
            if profile.metadata.get("blog") or profile.metadata.get("website"):
                exposure_points.append(f"{platform_name}: Personal website linked")
            
            # Platform-specific exposures
            if profile.platform == Platform.GITHUB:
                if profile.metadata.get("repositories"):
                    repos = profile.metadata["repositories"]
                    if any(r.get("commit_patterns") for r in repos):
                        exposure_points.append("GitHub: Commit time patterns visible")
                    
                    languages = [r.get("language") for r in repos if r.get("language")]
                    if len(set(languages)) > 3:
                        exposure_points.append("GitHub: Multiple programming languages revealed")
            
            elif profile.platform == Platform.TWITTER:
                if profile.metadata.get("recent_tweets_count", 0) > 10:
                    exposure_points.append("Twitter: Recent tweet content analyzed")
                
                if profile.metadata.get("followers_count", 0) > 1000:
                    exposure_points.append("Twitter: High follower count increases visibility")
        
        return exposure_points
    
    def generate_recommendations(
        self, 
        inferences: List[Inference], 
        profile_data: List[ProfileData]
    ) -> List[Recommendation]:
        """Generate privacy improvement recommendations."""
        recommendations = []
        
        # Location privacy
        location_inferences = [i for i in inferences if i.type == InferenceType.LOCATION and i.confidence > 0.6]
        if location_inferences:
            platforms_with_location = []
            for profile in profile_data:
                if profile.metadata.get("location"):
                    platforms_with_location.append(profile.platform)
            
            recommendations.append(Recommendation(
                priority="high",
                title="Remove Location Information",
                description="Your location can be inferred with high confidence from your public profiles.",
                action_items=[
                    "Remove location from profile bios",
                    "Review commit timestamps for location leaks",
                    "Consider using VPN for consistent timezone",
                    "Avoid location-specific references in posts"
                ],
                platforms_affected=platforms_with_location,
                potential_impact="Reduces location-based tracking and targeting"
            ))
        
        # Schedule privacy
        schedule_inferences = [i for i in inferences if i.type == InferenceType.WORK_SCHEDULE and i.confidence > 0.5]
        if schedule_inferences:
            github_platforms = [p.platform for p in profile_data if p.platform == Platform.GITHUB]
            if github_platforms:
                recommendations.append(Recommendation(
                    priority="medium",
                    title="Randomize Activity Patterns",
                    description="Your work schedule and timezone can be inferred from activity patterns.",
                    action_items=[
                        "Use scheduled commits/posts instead of real-time",
                        "Batch your coding sessions",
                        "Consider using commit timestamp randomization tools",
                        "Vary your online activity times"
                    ],
                    platforms_affected=github_platforms,
                    potential_impact="Makes schedule and timezone inference more difficult"
                ))
        
        # Professional information
        skill_inferences = [i for i in inferences if i.type == InferenceType.PROGRAMMING_SKILLS and i.confidence > 0.8]
        if skill_inferences:
            recommendations.append(Recommendation(
                priority="low",
                title="Review Professional Information Exposure",
                description="Your technical skills are highly visible and detailed.",
                action_items=[
                    "Consider which skills you want to highlight publicly",
                    "Remove or archive old experimental repositories",
                    "Use private repositories for sensitive projects",
                    "Be mindful of code comments that reveal too much context"
                ],
                platforms_affected=[Platform.GITHUB],
                potential_impact="Balances professional visibility with privacy"
            ))
        
        # Cross-platform correlation
        platforms = set(pd.platform for pd in profile_data)
        if len(platforms) > 1:
            recommendations.append(Recommendation(
                priority="medium",
                title="Minimize Cross-Platform Correlation",
                description="Having profiles on multiple platforms increases the ability to correlate and build a comprehensive profile.",
                action_items=[
                    "Use different usernames across platforms",
                    "Avoid linking profiles to each other",
                    "Vary the personal information shared on each platform",
                    "Consider using separate email addresses",
                    "Review bio consistency across platforms"
                ],
                platforms_affected=list(platforms),
                potential_impact="Reduces ability to correlate data across platforms"
            ))
        
        # Metadata cleanup
        metadata_issues = []
        for profile in profile_data:
            if profile.metadata.get("email"):
                metadata_issues.append("Email addresses visible")
            if profile.metadata.get("blog"):
                metadata_issues.append("Personal websites linked")
        
        if metadata_issues:
            recommendations.append(Recommendation(
                priority="high",
                title="Clean Up Profile Metadata",
                description="Personal contact information is publicly visible.",
                action_items=[
                    "Remove email addresses from public profiles",
                    "Consider unlinking personal websites",
                    "Review all profile fields for sensitive information",
                    "Use professional contact methods only"
                ],
                platforms_affected=[p.platform for p in profile_data],
                potential_impact="Reduces direct contact and correlation opportunities"
            ))
        
        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        recommendations.sort(key=lambda x: priority_order.get(x.priority, 3))
        
        return recommendations
