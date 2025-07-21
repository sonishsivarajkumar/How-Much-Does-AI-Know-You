"""Base connector interface."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from ..models import ProfileData, Platform


class BaseConnector(ABC):
    """Base class for platform connectors."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.platform = self.get_platform()
    
    @abstractmethod
    def get_platform(self) -> Platform:
        """Return the platform this connector handles."""
        pass
    
    @abstractmethod
    async def get_profile_data(self, username: str) -> ProfileData:
        """Fetch profile data for a given username."""
        pass
    
    @abstractmethod
    def is_configured(self) -> bool:
        """Check if the connector is properly configured."""
        pass
    
    def anonymize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove or hash sensitive information."""
        # Basic anonymization - can be extended
        sensitive_fields = ["email", "phone", "address", "full_name"]
        cleaned = data.copy()
        
        for field in sensitive_fields:
            if field in cleaned:
                cleaned[field] = "[REDACTED]"
                
        return cleaned
