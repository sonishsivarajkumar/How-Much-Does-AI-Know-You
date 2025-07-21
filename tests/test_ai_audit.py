"""Tests for AI Audit."""

import pytest
import asyncio
from unittest.mock import Mock, patch
from ai_audit.models import ProfileData, Platform, InferenceType
from ai_audit.connectors.github import GitHubConnector
from ai_audit.analyzer import PrivacyAnalyzer


class TestProfileData:
    """Test profile data models."""
    
    def test_profile_data_creation(self):
        """Test creating profile data."""
        profile = ProfileData(
            platform=Platform.GITHUB,
            username="testuser",
            profile_text="Test profile",
            metadata={"followers": 100}
        )
        
        assert profile.platform == Platform.GITHUB
        assert profile.username == "testuser"
        assert profile.metadata["followers"] == 100


class TestPrivacyAnalyzer:
    """Test privacy risk analysis."""
    
    def test_empty_inferences(self):
        """Test analyzer with no inferences."""
        analyzer = PrivacyAnalyzer()
        risk = analyzer.calculate_privacy_risk([], [])
        
        assert risk.overall_score == 0.0
        assert len(risk.risk_factors) == 0
    
    def test_high_confidence_inferences(self):
        """Test with high confidence inferences."""
        from ai_audit.models import Inference
        
        inferences = [
            Inference(
                type=InferenceType.LOCATION,
                value="San Francisco, CA",
                confidence=0.9,
                source_platforms=[Platform.GITHUB],
                model_used="test"
            )
        ]
        
        analyzer = PrivacyAnalyzer()
        risk = analyzer.calculate_privacy_risk(inferences, [])
        
        assert risk.overall_score > 0
        assert len(risk.high_confidence_inferences) == 1


@pytest.mark.asyncio
async def test_github_connector():
    """Test GitHub connector (mocked)."""
    with patch('ai_audit.connectors.github.Github') as mock_github:
        # Mock GitHub API response
        mock_user = Mock()
        mock_user.login = "testuser"
        mock_user.name = "Test User"
        mock_user.bio = "Test bio"
        mock_user.location = "Test Location"
        mock_user.company = "Test Company"
        mock_user.blog = "https://test.com"
        mock_user.email = None
        mock_user.hireable = True
        mock_user.public_repos = 10
        mock_user.followers = 100
        mock_user.following = 50
        mock_user.created_at = None
        mock_user.updated_at = None
        mock_user.id = 12345
        
        mock_github.return_value.get_user.return_value = mock_user
        
        connector = GitHubConnector(api_key="test_token")
        profile_data = await connector.get_profile_data("testuser")
        
        assert profile_data.username == "testuser"
        assert profile_data.platform == Platform.GITHUB
        assert "Test User" in profile_data.profile_text


if __name__ == "__main__":
    pytest.main([__file__])
