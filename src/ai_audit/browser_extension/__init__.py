"""Browser extension integration for real-time privacy analysis."""

import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

from ..models import BrowserExtensionData, Platform
from ..config import settings


class BrowserExtensionAPI:
    """API for browser extension communication."""
    
    def __init__(self):
        self.extension_data_dir = settings.data_dir / "extension"
        self.extension_data_dir.mkdir(exist_ok=True)
        self.risk_thresholds = {
            "low": 3.0,
            "medium": 6.0,
            "high": 8.0
        }
    
    async def analyze_page_elements(self, url: str, elements: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze page elements for privacy risks."""
        platform = self._detect_platform(url)
        risky_elements = []
        total_risk = 0.0
        
        for element in elements:
            element_risk = await self._analyze_element(element, platform)
            if element_risk["risk_score"] > 2.0:
                risky_elements.append(element_risk)
                total_risk += element_risk["risk_score"]
        
        # Normalize risk score
        normalized_risk = min(total_risk / max(len(elements), 1), 10.0)
        
        return {
            "url": url,
            "platform": platform,
            "total_risk_score": normalized_risk,
            "risk_level": self._get_risk_level(normalized_risk),
            "risky_elements": risky_elements,
            "recommendations": self._generate_page_recommendations(risky_elements, platform),
            "analysis_timestamp": datetime.now().isoformat()
        }
    
    def _detect_platform(self, url: str) -> str:
        """Detect platform from URL."""
        if "github.com" in url:
            return "github"
        elif "twitter.com" in url or "x.com" in url:
            return "twitter"
        elif "linkedin.com" in url:
            return "linkedin"
        elif "reddit.com" in url:
            return "reddit"
        elif "facebook.com" in url:
            return "facebook"
        elif "instagram.com" in url:
            return "instagram"
        elif "tiktok.com" in url:
            return "tiktok"
        else:
            return "unknown"
    
    async def _analyze_element(self, element: Dict[str, Any], platform: str) -> Dict[str, Any]:
        """Analyze individual page element for privacy risks."""
        element_type = element.get("type", "unknown")
        content = element.get("content", "")
        field_name = element.get("field_name", "")
        
        risk_score = 0.0
        risk_reasons = []
        
        # Analyze based on element type and content
        if element_type == "profile_field":
            risk_score, risk_reasons = self._analyze_profile_field(field_name, content, platform)
        elif element_type == "post_content":
            risk_score, risk_reasons = self._analyze_post_content(content, platform)
        elif element_type == "bio_text":
            risk_score, risk_reasons = self._analyze_bio_text(content, platform)
        elif element_type == "contact_info":
            risk_score, risk_reasons = self._analyze_contact_info(content, platform)
        elif element_type == "location_data":
            risk_score, risk_reasons = self._analyze_location_data(content, platform)
        
        return {
            "element_id": element.get("element_id"),
            "element_type": element_type,
            "field_name": field_name,
            "content_preview": content[:100] + "..." if len(content) > 100 else content,
            "risk_score": risk_score,
            "risk_reasons": risk_reasons,
            "recommendations": self._get_element_recommendations(element_type, risk_reasons)
        }
    
    def _analyze_profile_field(self, field_name: str, content: str, platform: str) -> tuple[float, List[str]]:
        """Analyze profile field for privacy risks."""
        risk_score = 0.0
        risk_reasons = []
        
        # High-risk fields
        if field_name.lower() in ["email", "phone", "address"]:
            risk_score += 8.0
            risk_reasons.append(f"Personal contact information ({field_name}) publicly visible")
        
        elif field_name.lower() in ["location", "city", "country"]:
            risk_score += 6.0
            risk_reasons.append("Location information publicly visible")
        
        elif field_name.lower() in ["company", "employer", "work"]:
            risk_score += 4.0
            risk_reasons.append("Employment information publicly visible")
        
        elif field_name.lower() in ["birthday", "age", "birth_date"]:
            risk_score += 7.0
            risk_reasons.append("Birth date/age information publicly visible")
        
        # Content analysis
        content_lower = content.lower()
        
        # Check for phone numbers
        import re
        phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
        if re.search(phone_pattern, content):
            risk_score += 8.0
            risk_reasons.append("Phone number detected in content")
        
        # Check for email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        if re.search(email_pattern, content):
            risk_score += 7.0
            risk_reasons.append("Email address detected in content")
        
        return min(risk_score, 10.0), risk_reasons
    
    def _analyze_post_content(self, content: str, platform: str) -> tuple[float, List[str]]:
        """Analyze post content for privacy risks."""
        risk_score = 0.0
        risk_reasons = []
        
        content_lower = content.lower()
        
        # Location mentions
        location_keywords = ["at", "in", "visiting", "location", "here", "currently"]
        if any(keyword in content_lower for keyword in location_keywords):
            risk_score += 3.0
            risk_reasons.append("Potential location sharing in post")
        
        # Personal information
        personal_keywords = ["my phone", "my email", "my address", "call me", "text me"]
        if any(keyword in content_lower for keyword in personal_keywords):
            risk_score += 6.0
            risk_reasons.append("Personal contact information in post")
        
        # Financial information
        financial_keywords = ["salary", "income", "expensive", "cost me", "paid", "investment"]
        if any(keyword in content_lower for keyword in financial_keywords):
            risk_score += 4.0
            risk_reasons.append("Financial information mentioned")
        
        # Schedule/routine information
        schedule_keywords = ["every day", "always", "routine", "schedule", "going to"]
        if any(keyword in content_lower for keyword in schedule_keywords):
            risk_score += 2.0
            risk_reasons.append("Personal schedule/routine information")
        
        return min(risk_score, 10.0), risk_reasons
    
    def _analyze_bio_text(self, content: str, platform: str) -> tuple[float, List[str]]:
        """Analyze bio/description text for privacy risks."""
        risk_score = 0.0
        risk_reasons = []
        
        content_lower = content.lower()
        
        # Contact information in bio
        if "@" in content and "." in content:
            risk_score += 5.0
            risk_reasons.append("Email or website in bio")
        
        # Location in bio
        location_indicators = ["based in", "from", "located", "city", "country"]
        if any(indicator in content_lower for indicator in location_indicators):
            risk_score += 4.0
            risk_reasons.append("Location information in bio")
        
        # Personal details
        personal_indicators = ["age", "years old", "birthday", "married", "single", "parent"]
        if any(indicator in content_lower for indicator in personal_indicators):
            risk_score += 3.0
            risk_reasons.append("Personal details in bio")
        
        return min(risk_score, 10.0), risk_reasons
    
    def _analyze_contact_info(self, content: str, platform: str) -> tuple[float, List[str]]:
        """Analyze contact information for privacy risks."""
        return 9.0, ["Contact information publicly visible"]
    
    def _analyze_location_data(self, content: str, platform: str) -> tuple[float, List[str]]:
        """Analyze location data for privacy risks."""
        return 7.0, ["Location data publicly accessible"]
    
    def _get_risk_level(self, risk_score: float) -> str:
        """Get risk level from numeric score."""
        if risk_score >= self.risk_thresholds["high"]:
            return "high"
        elif risk_score >= self.risk_thresholds["medium"]:
            return "medium"
        elif risk_score >= self.risk_thresholds["low"]:
            return "low"
        else:
            return "minimal"
    
    def _generate_page_recommendations(self, risky_elements: List[Dict], platform: str) -> List[str]:
        """Generate recommendations for the page."""
        recommendations = []
        
        if risky_elements:
            recommendations.append("Review highlighted elements for privacy risks")
            
            # Specific recommendations based on element types
            element_types = [elem["element_type"] for elem in risky_elements]
            
            if "profile_field" in element_types:
                recommendations.append("Consider removing or limiting personal information in profile fields")
            
            if "contact_info" in element_types:
                recommendations.append("Remove public contact information - use private messaging instead")
            
            if "location_data" in element_types:
                recommendations.append("Disable location sharing or make it visible to friends only")
            
            if "post_content" in element_types:
                recommendations.append("Review post content for unintended personal information sharing")
        
        # Platform-specific recommendations
        if platform == "github":
            recommendations.append("Review commit timestamps and repository descriptions")
        elif platform == "twitter":
            recommendations.append("Check tweet privacy settings and follower visibility")
        elif platform == "linkedin":
            recommendations.append("Review professional information visibility settings")
        
        return recommendations
    
    def _get_element_recommendations(self, element_type: str, risk_reasons: List[str]) -> List[str]:
        """Get specific recommendations for an element."""
        recommendations = []
        
        for reason in risk_reasons:
            if "contact information" in reason.lower():
                recommendations.append("Remove or make this information private")
            elif "location" in reason.lower():
                recommendations.append("Consider removing location details")
            elif "personal details" in reason.lower():
                recommendations.append("Review if this personal information is necessary to share")
            elif "financial" in reason.lower():
                recommendations.append("Avoid sharing financial information publicly")
        
        if not recommendations:
            recommendations.append("Review this element for privacy implications")
        
        return recommendations
    
    async def store_extension_data(self, data: BrowserExtensionData):
        """Store data from browser extension."""
        # Store in database for analysis
        file_path = self.extension_data_dir / f"session_{data.session_id}.json"
        
        with open(file_path, 'w') as f:
            json.dump(data.dict(), f, indent=2, default=str)
    
    async def get_extension_settings(self) -> Dict[str, Any]:
        """Get browser extension settings."""
        return {
            "risk_thresholds": self.risk_thresholds,
            "highlight_colors": {
                "high": "#ff4444",
                "medium": "#ffaa00", 
                "low": "#ffff00",
                "minimal": "#88ff88"
            },
            "auto_scan": True,
            "show_notifications": True,
            "anonymize_data": settings.anonymize_data
        }
    
    async def update_extension_settings(self, new_settings: Dict[str, Any]):
        """Update browser extension settings."""
        if "risk_thresholds" in new_settings:
            self.risk_thresholds.update(new_settings["risk_thresholds"])
        
        # Save settings to file
        settings_file = self.extension_data_dir / "extension_settings.json"
        with open(settings_file, 'w') as f:
            json.dump(new_settings, f, indent=2)


class ExtensionManifestGenerator:
    """Generate browser extension manifest and files."""
    
    def __init__(self):
        self.extension_dir = Path(__file__).parent / "browser_extension"
        self.extension_dir.mkdir(exist_ok=True)
    
    def generate_manifest(self) -> Dict[str, Any]:
        """Generate Chrome extension manifest."""
        return {
            "manifest_version": 3,
            "name": "AI Audit Privacy Monitor",
            "version": "1.0.0",
            "description": "Real-time privacy risk analysis for social media profiles",
            "permissions": [
                "activeTab",
                "storage",
                "notifications"
            ],
            "host_permissions": [
                "https://github.com/*",
                "https://twitter.com/*",
                "https://x.com/*",
                "https://linkedin.com/*",
                "https://reddit.com/*",
                "https://facebook.com/*",
                "https://instagram.com/*",
                "https://tiktok.com/*"
            ],
            "background": {
                "service_worker": "background.js"
            },
            "content_scripts": [
                {
                    "matches": [
                        "https://github.com/*",
                        "https://twitter.com/*",
                        "https://x.com/*",
                        "https://linkedin.com/*",
                        "https://reddit.com/*",
                        "https://facebook.com/*",
                        "https://instagram.com/*",
                        "https://tiktok.com/*"
                    ],
                    "js": ["content.js"],
                    "css": ["styles.css"]
                }
            ],
            "action": {
                "default_popup": "popup.html",
                "default_title": "AI Audit Privacy Monitor"
            },
            "icons": {
                "16": "icons/icon16.png",
                "48": "icons/icon48.png",
                "128": "icons/icon128.png"
            }
        }
    
    def generate_content_script(self) -> str:
        """Generate content script for browser extension."""
        return """
// AI Audit Privacy Monitor - Content Script
(function() {
    'use strict';
    
    const API_BASE = 'http://localhost:8000';
    let isAnalyzing = false;
    let highlightedElements = [];
    
    // Initialize the privacy monitor
    function initPrivacyMonitor() {
        console.log('AI Audit Privacy Monitor initialized');
        
        // Add style for highlighted elements
        addHighlightStyles();
        
        // Analyze page on load
        setTimeout(analyzePage, 2000);
        
        // Listen for DOM changes
        const observer = new MutationObserver(debounce(analyzePage, 1000));
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }
    
    function addHighlightStyles() {
        const style = document.createElement('style');
        style.textContent = `
            .ai-audit-highlight {
                position: relative;
                outline: 2px solid transparent;
                transition: outline-color 0.3s ease;
            }
            .ai-audit-highlight-high { outline-color: #ff4444; }
            .ai-audit-highlight-medium { outline-color: #ffaa00; }
            .ai-audit-highlight-low { outline-color: #ffff00; }
            .ai-audit-highlight-minimal { outline-color: #88ff88; }
            
            .ai-audit-tooltip {
                position: absolute;
                top: -30px;
                left: 0;
                background: #333;
                color: white;
                padding: 5px 10px;
                border-radius: 4px;
                font-size: 12px;
                z-index: 10000;
                display: none;
                white-space: nowrap;
            }
            
            .ai-audit-highlight:hover .ai-audit-tooltip {
                display: block;
            }
        `;
        document.head.appendChild(style);
    }
    
    async function analyzePage() {
        if (isAnalyzing) return;
        isAnalyzing = true;
        
        try {
            const elements = extractPageElements();
            if (elements.length === 0) {
                isAnalyzing = false;
                return;
            }
            
            const analysis = await analyzeElements(elements);
            if (analysis && analysis.risky_elements) {
                highlightRiskyElements(analysis.risky_elements);
                updateBadge(analysis.risk_level);
            }
        } catch (error) {
            console.error('Privacy analysis error:', error);
        }
        
        isAnalyzing = false;
    }
    
    function extractPageElements() {
        const elements = [];
        const url = window.location.href;
        
        // Extract profile fields based on platform
        if (url.includes('github.com')) {
            extractGitHubElements(elements);
        } else if (url.includes('twitter.com') || url.includes('x.com')) {
            extractTwitterElements(elements);
        } else if (url.includes('linkedin.com')) {
            extractLinkedInElements(elements);
        }
        
        return elements;
    }
    
    function extractGitHubElements(elements) {
        // GitHub profile elements
        const bio = document.querySelector('.user-profile-bio');
        if (bio) {
            elements.push({
                element_id: 'github-bio',
                type: 'bio_text',
                field_name: 'bio',
                content: bio.textContent.trim(),
                element: bio
            });
        }
        
        const location = document.querySelector('[itemprop="homeLocation"]');
        if (location) {
            elements.push({
                element_id: 'github-location',
                type: 'location_data',
                field_name: 'location',
                content: location.textContent.trim(),
                element: location
            });
        }
        
        const email = document.querySelector('[itemprop="email"]');
        if (email) {
            elements.push({
                element_id: 'github-email',
                type: 'contact_info',
                field_name: 'email',
                content: email.textContent.trim(),
                element: email
            });
        }
    }
    
    function extractTwitterElements(elements) {
        // Twitter profile elements
        const bio = document.querySelector('[data-testid="UserDescription"]');
        if (bio) {
            elements.push({
                element_id: 'twitter-bio',
                type: 'bio_text',
                field_name: 'bio',
                content: bio.textContent.trim(),
                element: bio
            });
        }
        
        const location = document.querySelector('[data-testid="UserLocation"]');
        if (location) {
            elements.push({
                element_id: 'twitter-location',
                type: 'location_data',
                field_name: 'location',
                content: location.textContent.trim(),
                element: location
            });
        }
    }
    
    function extractLinkedInElements(elements) {
        // LinkedIn profile elements
        const headline = document.querySelector('.text-heading-xlarge');
        if (headline) {
            elements.push({
                element_id: 'linkedin-headline',
                type: 'profile_field',
                field_name: 'headline',
                content: headline.textContent.trim(),
                element: headline
            });
        }
        
        const location = document.querySelector('.text-body-small.inline');
        if (location) {
            elements.push({
                element_id: 'linkedin-location',
                type: 'location_data',
                field_name: 'location',
                content: location.textContent.trim(),
                element: location
            });
        }
    }
    
    async function analyzeElements(elements) {
        try {
            const response = await fetch(`${API_BASE}/api/browser-extension/analyze`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    url: window.location.href,
                    elements: elements.map(e => ({
                        element_id: e.element_id,
                        type: e.type,
                        field_name: e.field_name,
                        content: e.content
                    }))
                })
            });
            
            if (response.ok) {
                return await response.json();
            }
        } catch (error) {
            console.error('Analysis request failed:', error);
        }
        
        return null;
    }
    
    function highlightRiskyElements(riskyElements) {
        // Clear previous highlights
        clearHighlights();
        
        riskyElements.forEach(element => {
            const domElement = document.querySelector(`[data-element-id="${element.element_id}"]`) ||
                             findElementByContent(element.content_preview);
            
            if (domElement) {
                highlightElement(domElement, element);
            }
        });
    }
    
    function highlightElement(element, riskData) {
        element.classList.add('ai-audit-highlight');
        element.classList.add(`ai-audit-highlight-${riskData.risk_level || 'medium'}`);
        
        // Add tooltip
        const tooltip = document.createElement('div');
        tooltip.className = 'ai-audit-tooltip';
        tooltip.textContent = `Privacy Risk: ${riskData.risk_score}/10 - ${riskData.risk_reasons[0] || 'Review recommended'}`;
        element.appendChild(tooltip);
        
        highlightedElements.push(element);
    }
    
    function clearHighlights() {
        highlightedElements.forEach(element => {
            element.classList.remove('ai-audit-highlight', 'ai-audit-highlight-high', 
                                   'ai-audit-highlight-medium', 'ai-audit-highlight-low', 
                                   'ai-audit-highlight-minimal');
            const tooltip = element.querySelector('.ai-audit-tooltip');
            if (tooltip) {
                tooltip.remove();
            }
        });
        highlightedElements = [];
    }
    
    function findElementByContent(content) {
        const elements = document.querySelectorAll('*');
        for (let element of elements) {
            if (element.textContent.includes(content.substring(0, 50))) {
                return element;
            }
        }
        return null;
    }
    
    function updateBadge(riskLevel) {
        chrome.runtime.sendMessage({
            action: 'updateBadge',
            riskLevel: riskLevel
        });
    }
    
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initPrivacyMonitor);
    } else {
        initPrivacyMonitor();
    }
})();
"""
    
    def generate_popup_html(self) -> str:
        """Generate popup HTML for browser extension."""
        return """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {
            width: 300px;
            padding: 15px;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            margin: 0;
        }
        .header {
            text-align: center;
            margin-bottom: 15px;
        }
        .logo {
            font-size: 20px;
            font-weight: bold;
            color: #1a73e8;
        }
        .risk-score {
            background: #f1f3f4;
            border-radius: 8px;
            padding: 10px;
            margin-bottom: 15px;
            text-align: center;
        }
        .risk-high { border-left: 4px solid #ea4335; }
        .risk-medium { border-left: 4px solid #fbbc04; }
        .risk-low { border-left: 4px solid #34a853; }
        .risk-minimal { border-left: 4px solid #34a853; }
        .recommendations {
            margin-bottom: 15px;
        }
        .recommendation {
            font-size: 12px;
            color: #5f6368;
            margin-bottom: 5px;
        }
        .actions {
            display: flex;
            gap: 10px;
        }
        .btn {
            flex: 1;
            padding: 8px 12px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
        }
        .btn-primary {
            background: #1a73e8;
            color: white;
        }
        .btn-secondary {
            background: #f1f3f4;
            color: #3c4043;
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">🛡️ AI Audit</div>
        <div style="font-size: 12px; color: #5f6368;">Privacy Monitor</div>
    </div>
    
    <div id="risk-score" class="risk-score">
        <div style="font-size: 14px; font-weight: bold;">Privacy Risk</div>
        <div id="risk-value" style="font-size: 24px; font-weight: bold; margin: 5px 0;">--</div>
        <div id="risk-level" style="font-size: 12px; color: #5f6368;">Analyzing...</div>
    </div>
    
    <div class="recommendations">
        <div style="font-weight: bold; margin-bottom: 8px;">Recommendations:</div>
        <div id="recommendations-list"></div>
    </div>
    
    <div class="actions">
        <button id="scan-btn" class="btn btn-primary">Scan Page</button>
        <button id="settings-btn" class="btn btn-secondary">Settings</button>
    </div>
    
    <script src="popup.js"></script>
</body>
</html>
"""
    
    def generate_all_files(self):
        """Generate all browser extension files."""
        files = {
            "manifest.json": json.dumps(self.generate_manifest(), indent=2),
            "content.js": self.generate_content_script(),
            "popup.html": self.generate_popup_html(),
            # Additional files would be generated here
        }
        
        for filename, content in files.items():
            file_path = self.extension_dir / filename
            with open(file_path, 'w') as f:
                f.write(content)
        
        print(f"Browser extension files generated in: {self.extension_dir}")
        return self.extension_dir


# Global extension API instance
extension_api = BrowserExtensionAPI()
