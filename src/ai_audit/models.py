"""Data models for AI Audit."""

from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field


class Platform(str, Enum):
    """Supported platforms for data collection."""
    GITHUB = "github"
    TWITTER = "twitter" 
    REDDIT = "reddit"
    LINKEDIN = "linkedin"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"


class InferenceType(str, Enum):
    """Types of inferences that can be made."""
    PROGRAMMING_SKILLS = "programming_skills"
    LOCATION = "location"
    AGE_RANGE = "age_range"
    INTERESTS = "interests"
    SENTIMENT = "sentiment"
    POLITICAL_LEANING = "political_leaning"
    WORK_SCHEDULE = "work_schedule"
    EDUCATION_LEVEL = "education_level"
    HEALTH_SIGNALS = "health_signals"
    PURCHASING_POWER = "purchasing_power"
    RELATIONSHIP_STATUS = "relationship_status"
    PERSONALITY_TRAITS = "personality_traits"
    CAREER_STAGE = "career_stage"
    COMMUNICATION_STYLE = "communication_style"
    RISK_TOLERANCE = "risk_tolerance"
    SOCIAL_INFLUENCE = "social_influence"
    LIFESTYLE_CHOICES = "lifestyle_choices"
    FINANCIAL_STATUS = "financial_status"
    TRAVEL_PATTERNS = "travel_patterns"
    FAMILY_STRUCTURE = "family_structure"


class ConfidenceLevel(str, Enum):
    """Confidence levels for inferences."""
    LOW = "low"      # < 0.4
    MEDIUM = "medium"  # 0.4 - 0.7
    HIGH = "high"    # > 0.7


class ProfileData(BaseModel):
    """Raw profile data from a platform."""
    platform: Platform
    username: str
    user_id: Optional[str] = None
    profile_text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    collected_at: datetime = Field(default_factory=datetime.now)
    raw_data: Optional[Dict[str, Any]] = None


class Inference(BaseModel):
    """An inference made about the user."""
    type: InferenceType
    value: str
    confidence: float = Field(ge=0.0, le=1.0)
    confidence_level: Optional[ConfidenceLevel] = None
    reasoning: Optional[str] = None
    source_platforms: List[Platform]
    model_used: str
    created_at: datetime = Field(default_factory=datetime.now)
    
    def __init__(self, **data):
        super().__init__(**data)
        # Auto-calculate confidence level if not provided
        if self.confidence_level is None:
            if self.confidence < 0.4:
                self.confidence_level = ConfidenceLevel.LOW
            elif self.confidence < 0.7:
                self.confidence_level = ConfidenceLevel.MEDIUM
            else:
                self.confidence_level = ConfidenceLevel.HIGH


class PrivacyRisk(BaseModel):
    """Privacy risk assessment."""
    overall_score: float = Field(ge=0.0, le=10.0)
    risk_factors: List[str]
    high_confidence_inferences: List[Inference]
    data_exposure_points: List[str]
    calculated_at: datetime = Field(default_factory=datetime.now)


class Recommendation(BaseModel):
    """Privacy improvement recommendation."""
    priority: str  # "high", "medium", "low"
    title: str
    description: str
    action_items: List[str]
    platforms_affected: List[Platform]
    potential_impact: str


class AuditReport(BaseModel):
    """Complete audit report."""
    user_id: str
    platforms_analyzed: List[Platform]
    profile_data: List[ProfileData]
    inferences: List[Inference]
    privacy_risk: PrivacyRisk
    recommendations: List[Recommendation]
    generated_at: datetime = Field(default_factory=datetime.now)
    report_version: str = "1.0"


class ScanSession(BaseModel):
    """A scanning session tracking."""
    session_id: str
    platforms: List[Platform]
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    status: str = "running"  # "running", "completed", "failed"
    error_message: Optional[str] = None


class BreachAlert(BaseModel):
    """Data breach alert information."""
    email: str
    breach_name: str
    breach_date: datetime
    compromised_data: List[str]
    severity: str  # "low", "medium", "high", "critical"
    detected_at: datetime = Field(default_factory=datetime.now)
    resolved: bool = False
    resolution_notes: Optional[str] = None


class RemediationAction(BaseModel):
    """Automated remediation action."""
    action_id: str
    action_type: str  # "remove_data", "update_privacy", "contact_platform"
    platform: Platform
    description: str
    status: str = "pending"  # "pending", "in_progress", "completed", "failed"
    scheduled_for: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    rollback_info: Optional[Dict[str, Any]] = None


class MonitoringSchedule(BaseModel):
    """Monitoring schedule configuration."""
    schedule_id: str
    platforms: List[Platform]
    frequency: str  # "daily", "weekly", "monthly"
    next_run: datetime
    last_run: Optional[datetime] = None
    enabled: bool = True
    notification_settings: Dict[str, Any] = Field(default_factory=dict)


class PluginConfig(BaseModel):
    """Plugin configuration."""
    plugin_id: str
    plugin_name: str
    plugin_version: str
    enabled: bool = True
    config_data: Dict[str, Any] = Field(default_factory=dict)
    installed_at: datetime = Field(default_factory=datetime.now)
    last_updated: Optional[datetime] = None


class BrowserExtensionData(BaseModel):
    """Data from browser extension."""
    session_id: str
    url: str
    platform: str
    elements_highlighted: List[Dict[str, Any]]
    risk_score: float
    detected_at: datetime = Field(default_factory=datetime.now)
    user_action: Optional[str] = None  # "ignored", "fixed", "saved"
