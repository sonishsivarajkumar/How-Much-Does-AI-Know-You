"""Configuration management for AI Audit."""

import os
from typing import Optional
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Keys
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(None, env="ANTHROPIC_API_KEY")
    cohere_api_key: Optional[str] = Field(None, env="COHERE_API_KEY")
    
    # Platform API Keys
    github_token: Optional[str] = Field(None, env="GITHUB_TOKEN")
    twitter_bearer_token: Optional[str] = Field(None, env="TWITTER_BEARER_TOKEN")
    reddit_client_id: Optional[str] = Field(None, env="REDDIT_CLIENT_ID")
    reddit_client_secret: Optional[str] = Field(None, env="REDDIT_CLIENT_SECRET")
    linkedin_client_id: Optional[str] = Field(None, env="LINKEDIN_CLIENT_ID")
    linkedin_client_secret: Optional[str] = Field(None, env="LINKEDIN_CLIENT_SECRET")
    
    # Phase 2 & 3 API Keys
    hibp_api_key: Optional[str] = Field(None, env="HIBP_API_KEY")
    
    # Local Storage
    data_dir: Path = Field(Path.home() / ".ai-audit", env="DATA_DIR")
    cache_ttl: int = Field(3600, env="CACHE_TTL")  # 1 hour
    
    # Inference Settings
    use_local_models: bool = Field(False, env="USE_LOCAL_MODELS")
    local_model_path: Optional[Path] = Field(None, env="LOCAL_MODEL_PATH")
    default_llm_provider: str = Field("openai", env="DEFAULT_LLM_PROVIDER")
    max_inference_requests: int = Field(10, env="MAX_INFERENCE_REQUESTS")
    
    # Privacy Settings
    anonymize_data: bool = Field(True, env="ANONYMIZE_DATA")
    retain_raw_data: bool = Field(False, env="RETAIN_RAW_DATA")
    
    # Web Server
    web_host: str = Field("127.0.0.1", env="WEB_HOST")
    web_port: int = Field(8000, env="WEB_PORT")
    debug_mode: bool = Field(False, env="DEBUG_MODE")
    
    # Phase 2 & 3 Settings
    demo_mode: bool = Field(False, env="DEMO_MODE")
    debug: bool = Field(False, env="DEBUG")
    
    # Monitoring Settings
    monitoring_enabled: bool = Field(True, env="MONITORING_ENABLED")
    breach_check_interval: int = Field(86400, env="BREACH_CHECK_INTERVAL")  # 24 hours
    
    # Automation Settings
    auto_remediation_enabled: bool = Field(False, env="AUTO_REMEDIATION_ENABLED")
    max_automation_actions: int = Field(5, env="MAX_AUTOMATION_ACTIONS")
    
    # Plugin Settings
    plugins_enabled: bool = Field(True, env="PLUGINS_ENABLED")
    plugin_dir: Path = Field(Path.home() / ".ai-audit" / "plugins", env="PLUGIN_DIR")
    
    # Browser Extension Settings
    extension_enabled: bool = Field(False, env="EXTENSION_ENABLED")
    extension_port: int = Field(8001, env="EXTENSION_PORT")

    class Config:
        env_file = ".env"
        case_sensitive = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure data directory exists
        self.data_dir.mkdir(parents=True, exist_ok=True)
        # Ensure plugin directory exists
        self.plugin_dir.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
