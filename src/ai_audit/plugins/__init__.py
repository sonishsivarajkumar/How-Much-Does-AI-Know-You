"""Plugin system for AI Audit extensibility."""

import importlib
import inspect
import json
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Type
import asyncio

from ..models import PluginConfig, ProfileData, Inference, InferenceType, Platform
from ..config import settings


class BasePlugin(ABC):
    """Base class for all AI Audit plugins."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.enabled = True
        self.name = self.__class__.__name__
        self.version = "1.0.0"
    
    @abstractmethod
    def get_plugin_info(self) -> Dict[str, Any]:
        """Return plugin information."""
        pass
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the plugin."""
        pass
    
    @abstractmethod
    async def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the plugin with provided data."""
        pass
    
    async def cleanup(self):
        """Cleanup resources when plugin is disabled."""
        pass


class DataConnectorPlugin(BasePlugin):
    """Base class for data connector plugins."""
    
    @abstractmethod
    async def collect_profile_data(self, username: str) -> ProfileData:
        """Collect profile data from the platform."""
        pass
    
    @abstractmethod
    def get_supported_platform(self) -> Platform:
        """Return the platform this connector supports."""
        pass


class InferencePlugin(BasePlugin):
    """Base class for inference plugins."""
    
    @abstractmethod
    async def make_inference(
        self, 
        profile_data: ProfileData, 
        inference_type: InferenceType
    ) -> Optional[Inference]:
        """Make an inference about the profile data."""
        pass
    
    @abstractmethod
    def get_supported_inference_types(self) -> List[InferenceType]:
        """Return the inference types this plugin supports."""
        pass


class AnalysisPlugin(BasePlugin):
    """Base class for custom analysis plugins."""
    
    @abstractmethod
    async def analyze_data(
        self, 
        profile_data: List[ProfileData], 
        inferences: List[Inference]
    ) -> Dict[str, Any]:
        """Perform custom analysis on profile data and inferences."""
        pass


# Example Plugin Implementations

class WearableHealthPlugin(AnalysisPlugin):
    """Plugin to analyze wearable health data signals."""
    
    def get_plugin_info(self) -> Dict[str, Any]:
        return {
            "name": "Wearable Health Analyzer",
            "version": "1.0.0",
            "description": "Analyzes health signals from wearable device data mentions",
            "author": "AI Audit Team",
            "requires": []
        }
    
    async def initialize(self) -> bool:
        """Initialize the health analysis plugin."""
        self.health_keywords = {
            'fitness': ['workout', 'exercise', 'gym', 'running', 'cycling', 'fitness'],
            'sleep': ['sleep', 'insomnia', 'tired', 'rest', 'bedtime'],
            'heart': ['heart rate', 'cardio', 'pulse', 'bpm'],
            'stress': ['stress', 'anxiety', 'meditation', 'mindfulness'],
            'diet': ['diet', 'nutrition', 'calories', 'healthy eating', 'weight']
        }
        return True
    
    async def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute health analysis."""
        profile_data = data.get('profile_data', [])
        return await self.analyze_data(profile_data, [])
    
    async def analyze_data(
        self, 
        profile_data: List[ProfileData], 
        inferences: List[Inference]
    ) -> Dict[str, Any]:
        """Analyze health-related signals."""
        health_signals = {}
        
        for profile in profile_data:
            profile_text_lower = profile.profile_text.lower()
            
            for category, keywords in self.health_keywords.items():
                matches = [kw for kw in keywords if kw in profile_text_lower]
                if matches:
                    if category not in health_signals:
                        health_signals[category] = []
                    health_signals[category].extend(matches)
        
        # Calculate health privacy risk
        risk_score = len(health_signals) * 1.5
        
        return {
            "health_signals": health_signals,
            "health_privacy_risk": min(risk_score, 10.0),
            "recommendations": self._generate_health_recommendations(health_signals)
        }
    
    def _generate_health_recommendations(self, health_signals: Dict[str, List[str]]) -> List[str]:
        """Generate health-specific privacy recommendations."""
        recommendations = []
        
        if health_signals:
            recommendations.append("Consider limiting health-related posts on public platforms")
            recommendations.append("Review privacy settings on fitness apps and wearables")
            recommendations.append("Be cautious about sharing workout locations and schedules")
        
        if 'stress' in health_signals:
            recommendations.append("Avoid posting about mental health struggles on professional platforms")
        
        if 'diet' in health_signals:
            recommendations.append("Be mindful of food photos that might reveal health conditions")
        
        return recommendations


class CryptocurrencyPlugin(AnalysisPlugin):
    """Plugin to analyze cryptocurrency and financial signals."""
    
    def get_plugin_info(self) -> Dict[str, Any]:
        return {
            "name": "Cryptocurrency Analyzer",
            "version": "1.0.0",
            "description": "Analyzes cryptocurrency usage and financial signals",
            "author": "AI Audit Team",
            "requires": []
        }
    
    async def initialize(self) -> bool:
        """Initialize the crypto analysis plugin."""
        self.crypto_keywords = [
            'bitcoin', 'btc', 'ethereum', 'eth', 'cryptocurrency', 'crypto',
            'blockchain', 'defi', 'nft', 'web3', 'wallet', 'hodl', 'trading'
        ]
        self.financial_keywords = [
            'investment', 'portfolio', 'stock', 'trading', 'finance',
            'money', 'salary', 'income', 'expensive', 'luxury'
        ]
        return True
    
    async def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute crypto analysis."""
        profile_data = data.get('profile_data', [])
        return await self.analyze_data(profile_data, [])
    
    async def analyze_data(
        self, 
        profile_data: List[ProfileData], 
        inferences: List[Inference]
    ) -> Dict[str, Any]:
        """Analyze cryptocurrency and financial signals."""
        crypto_signals = []
        financial_signals = []
        
        for profile in profile_data:
            profile_text_lower = profile.profile_text.lower()
            
            # Check for crypto mentions
            crypto_matches = [kw for kw in self.crypto_keywords if kw in profile_text_lower]
            crypto_signals.extend(crypto_matches)
            
            # Check for financial mentions
            financial_matches = [kw for kw in self.financial_keywords if kw in profile_text_lower]
            financial_signals.extend(financial_matches)
        
        # Calculate financial privacy risk
        total_signals = len(set(crypto_signals + financial_signals))
        risk_score = total_signals * 1.2
        
        return {
            "crypto_signals": list(set(crypto_signals)),
            "financial_signals": list(set(financial_signals)),
            "financial_privacy_risk": min(risk_score, 10.0),
            "recommendations": self._generate_financial_recommendations(crypto_signals, financial_signals)
        }
    
    def _generate_financial_recommendations(self, crypto_signals: List[str], financial_signals: List[str]) -> List[str]:
        """Generate financial privacy recommendations."""
        recommendations = []
        
        if crypto_signals:
            recommendations.extend([
                "Avoid posting cryptocurrency wallet addresses publicly",
                "Be cautious about sharing trading strategies or holdings",
                "Consider using pseudonyms for crypto-related discussions"
            ])
        
        if financial_signals:
            recommendations.extend([
                "Limit sharing of financial information on social media",
                "Avoid posting about expensive purchases or income",
                "Be wary of investment scams targeting your profile"
            ])
        
        return recommendations


class TikTokConnectorPlugin(DataConnectorPlugin):
    """Plugin to connect to TikTok (mock implementation)."""
    
    def get_plugin_info(self) -> Dict[str, Any]:
        return {
            "name": "TikTok Connector",
            "version": "1.0.0",
            "description": "Connects to TikTok to analyze public profile data",
            "author": "AI Audit Team",
            "requires": ["requests"]
        }
    
    async def initialize(self) -> bool:
        """Initialize TikTok connector."""
        # This would initialize TikTok API client
        return True
    
    async def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute TikTok data collection."""
        username = data.get('username')
        if not username:
            return {"error": "Username required"}
        
        profile_data = await self.collect_profile_data(username)
        return {"profile_data": profile_data}
    
    def get_supported_platform(self) -> Platform:
        return Platform.TIKTOK
    
    async def collect_profile_data(self, username: str) -> ProfileData:
        """Collect TikTok profile data (mock implementation)."""
        # This would use TikTok's API to collect profile data
        # For now, return mock data
        
        mock_data = {
            "username": username,
            "followers": 1234,
            "following": 567,
            "likes": 89012,
            "videos": 45,
            "bio": f"TikTok user @{username}",
            "verified": False
        }
        
        profile_text = f"""
TikTok Profile: @{username}
Followers: {mock_data['followers']}
Following: {mock_data['following']}
Total Likes: {mock_data['likes']}
Videos: {mock_data['videos']}
Bio: {mock_data['bio']}
"""
        
        return ProfileData(
            platform=Platform.TIKTOK,
            username=username,
            user_id=username,
            profile_text=profile_text.strip(),
            metadata=mock_data
        )


class PluginManager:
    """Manages AI Audit plugins."""
    
    def __init__(self):
        self.plugins: Dict[str, BasePlugin] = {}
        self.plugin_configs: Dict[str, PluginConfig] = {}
        self.plugins_dir = settings.data_dir / "plugins"
        self.plugins_dir.mkdir(exist_ok=True)
    
    async def initialize(self):
        """Initialize the plugin system."""
        await self.load_built_in_plugins()
        await self.load_external_plugins()
        await self.initialize_plugins()
    
    async def load_built_in_plugins(self):
        """Load built-in plugins."""
        built_in_plugins = [
            WearableHealthPlugin,
            CryptocurrencyPlugin,
            TikTokConnectorPlugin
        ]
        
        for plugin_class in built_in_plugins:
            config = {}
            plugin = plugin_class(config)
            
            plugin_config = PluginConfig(
                plugin_id=plugin.name,
                plugin_name=plugin.name,
                plugin_version=plugin.version,
                enabled=True,
                config_data=config
            )
            
            self.plugins[plugin.name] = plugin
            self.plugin_configs[plugin.name] = plugin_config
    
    async def load_external_plugins(self):
        """Load external plugins from plugins directory."""
        for plugin_file in self.plugins_dir.glob("*.py"):
            try:
                await self.load_plugin_from_file(plugin_file)
            except Exception as e:
                print(f"Warning: Failed to load plugin {plugin_file}: {e}")
    
    async def load_plugin_from_file(self, plugin_file: Path):
        """Load a plugin from a Python file."""
        # This would dynamically import and load external plugins
        # For security, this should include validation and sandboxing
        pass
    
    async def initialize_plugins(self):
        """Initialize all loaded plugins."""
        for plugin_name, plugin in self.plugins.items():
            try:
                if plugin.enabled:
                    success = await plugin.initialize()
                    if not success:
                        print(f"Warning: Plugin {plugin_name} failed to initialize")
                        plugin.enabled = False
            except Exception as e:
                print(f"Warning: Plugin {plugin_name} initialization error: {e}")
                plugin.enabled = False
    
    async def execute_plugin(self, plugin_name: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Execute a specific plugin."""
        if plugin_name not in self.plugins:
            return None
        
        plugin = self.plugins[plugin_name]
        if not plugin.enabled:
            return None
        
        try:
            return await plugin.execute(data)
        except Exception as e:
            print(f"Error executing plugin {plugin_name}: {e}")
            return None
    
    async def execute_analysis_plugins(
        self, 
        profile_data: List[ProfileData], 
        inferences: List[Inference]
    ) -> Dict[str, Any]:
        """Execute all analysis plugins."""
        results = {}
        
        data = {
            'profile_data': profile_data,
            'inferences': inferences
        }
        
        for plugin_name, plugin in self.plugins.items():
            if isinstance(plugin, AnalysisPlugin) and plugin.enabled:
                try:
                    result = await plugin.execute(data)
                    if result:
                        results[plugin_name] = result
                except Exception as e:
                    print(f"Error in analysis plugin {plugin_name}: {e}")
        
        return results
    
    async def get_connector_plugins(self) -> Dict[Platform, DataConnectorPlugin]:
        """Get all available data connector plugins."""
        connectors = {}
        
        for plugin in self.plugins.values():
            if isinstance(plugin, DataConnectorPlugin) and plugin.enabled:
                platform = plugin.get_supported_platform()
                connectors[platform] = plugin
        
        return connectors
    
    def get_plugin_list(self) -> List[Dict[str, Any]]:
        """Get list of all plugins with their status."""
        plugin_list = []
        
        for plugin_name, plugin in self.plugins.items():
            info = plugin.get_plugin_info()
            info.update({
                "enabled": plugin.enabled,
                "type": plugin.__class__.__base__.__name__
            })
            plugin_list.append(info)
        
        return plugin_list
    
    async def enable_plugin(self, plugin_name: str) -> bool:
        """Enable a plugin."""
        if plugin_name in self.plugins:
            self.plugins[plugin_name].enabled = True
            return await self.plugins[plugin_name].initialize()
        return False
    
    async def disable_plugin(self, plugin_name: str) -> bool:
        """Disable a plugin."""
        if plugin_name in self.plugins:
            self.plugins[plugin_name].enabled = False
            await self.plugins[plugin_name].cleanup()
            return True
        return False
    
    async def install_plugin(self, plugin_path: str, config: Dict[str, Any] = None) -> bool:
        """Install a new plugin."""
        try:
            # This would handle plugin installation with proper validation
            # For security, plugins should be signed and verified
            print(f"Installing plugin from {plugin_path}")
            return True
        except Exception as e:
            print(f"Plugin installation failed: {e}")
            return False
    
    async def uninstall_plugin(self, plugin_name: str) -> bool:
        """Uninstall a plugin."""
        if plugin_name in self.plugins:
            await self.disable_plugin(plugin_name)
            del self.plugins[plugin_name]
            del self.plugin_configs[plugin_name]
            return True
        return False


# Global plugin manager instance
plugin_manager = PluginManager()
