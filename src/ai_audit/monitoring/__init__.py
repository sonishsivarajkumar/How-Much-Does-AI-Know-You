"""Breach monitoring and alert system."""

import asyncio
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import requests
import smtplib

from ..models import BreachAlert, ProfileData
from ..config import settings
from ..storage import db


class BreachMonitor:
    """Monitor for data breaches using HaveIBeenPwned API."""
    
    def __init__(self):
        self.hibp_api_base = "https://haveibeenpwned.com/api/v3"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'AI-Audit/0.1.0',
            'hibp-api-key': settings.hibp_api_key if hasattr(settings, 'hibp_api_key') else None
        })
    
    async def check_email_breaches(self, email: str) -> List[BreachAlert]:
        """Check if email appears in known breaches."""
        try:
            # Check with HaveIBeenPwned
            response = self.session.get(
                f"{self.hibp_api_base}/breachedaccount/{email}",
                params={'truncateResponse': 'false'}
            )
            
            if response.status_code == 404:
                # No breaches found
                return []
            elif response.status_code == 200:
                breaches_data = response.json()
                return self._parse_breach_data(email, breaches_data)
            elif response.status_code == 429:
                # Rate limited
                print("Warning: HaveIBeenPwned rate limit reached")
                await asyncio.sleep(2)
                return []
            else:
                print(f"Warning: HaveIBeenPwned API error: {response.status_code}")
                return []
        
        except Exception as e:
            print(f"Warning: Could not check breaches for {email}: {e}")
            return []
    
    def _parse_breach_data(self, email: str, breaches_data: List[Dict]) -> List[BreachAlert]:
        """Parse breach data from HaveIBeenPwned."""
        alerts = []
        
        for breach in breaches_data:
            try:
                # Determine severity based on compromised data types
                data_classes = breach.get('DataClasses', [])
                severity = self._calculate_breach_severity(data_classes)
                
                alert = BreachAlert(
                    email=email,
                    breach_name=breach.get('Name', 'Unknown'),
                    breach_date=datetime.fromisoformat(breach.get('BreachDate', '1970-01-01')),
                    compromised_data=data_classes,
                    severity=severity
                )
                alerts.append(alert)
                
            except Exception as e:
                print(f"Warning: Could not parse breach data: {e}")
                continue
        
        return alerts
    
    def _calculate_breach_severity(self, data_classes: List[str]) -> str:
        """Calculate breach severity based on compromised data types."""
        critical_data = {'Passwords', 'Credit cards', 'Social security numbers', 'Bank account numbers'}
        high_data = {'Email addresses', 'Phone numbers', 'Physical addresses', 'Dates of birth'}
        medium_data = {'Names', 'Usernames', 'IP addresses', 'Job titles'}
        
        data_set = set(data_classes)
        
        if data_set & critical_data:
            return "critical"
        elif data_set & high_data:
            return "high"
        elif data_set & medium_data:
            return "medium"
        else:
            return "low"
    
    async def scan_profile_emails(self, profile_data: List[ProfileData]) -> List[BreachAlert]:
        """Scan all emails found in profile data for breaches."""
        all_alerts = []
        emails_to_check = set()
        
        # Extract emails from profile data
        for profile in profile_data:
            # Check metadata for email addresses
            if profile.metadata.get('email'):
                emails_to_check.add(profile.metadata['email'])
            
            # Check raw data for email patterns
            if profile.raw_data:
                emails = self._extract_emails_from_data(profile.raw_data)
                emails_to_check.update(emails)
        
        # Check each email
        for email in emails_to_check:
            if self._is_valid_email(email):
                alerts = await self.check_email_breaches(email)
                all_alerts.extend(alerts)
                
                # Rate limiting
                await asyncio.sleep(1.5)  # HaveIBeenPwned requires 1.5s between requests
        
        return all_alerts
    
    def _extract_emails_from_data(self, data: Dict[str, Any]) -> List[str]:
        """Extract email addresses from nested data structures."""
        import re
        emails = []
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        
        def extract_from_dict(d):
            if isinstance(d, dict):
                for value in d.values():
                    extract_from_dict(value)
            elif isinstance(d, list):
                for item in d:
                    extract_from_dict(item)
            elif isinstance(d, str):
                found_emails = re.findall(email_pattern, d)
                emails.extend(found_emails)
        
        extract_from_dict(data)
        return list(set(emails))  # Remove duplicates
    
    def _is_valid_email(self, email: str) -> bool:
        """Basic email validation."""
        import re
        pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$'
        return re.match(pattern, email) is not None
    
    async def continuous_monitoring(self, email_list: List[str], check_interval_hours: int = 24):
        """Continuously monitor emails for new breaches."""
        while True:
            try:
                print(f"Running breach check for {len(email_list)} emails...")
                
                for email in email_list:
                    alerts = await self.check_email_breaches(email)
                    
                    for alert in alerts:
                        # Check if this is a new breach
                        if await self._is_new_breach(alert):
                            await self._handle_new_breach(alert)
                            await db.store_breach_alert(alert)
                    
                    await asyncio.sleep(1.5)  # Rate limiting
                
                print(f"Breach check completed. Next check in {check_interval_hours} hours.")
                await asyncio.sleep(check_interval_hours * 3600)
                
            except Exception as e:
                print(f"Error in continuous monitoring: {e}")
                await asyncio.sleep(3600)  # Wait 1 hour on error
    
    async def _is_new_breach(self, alert: BreachAlert) -> bool:
        """Check if this breach alert is new."""
        # This would check against stored alerts in the database
        # For now, we'll assume all alerts are new
        return True
    
    async def _handle_new_breach(self, alert: BreachAlert):
        """Handle a new breach alert."""
        print(f"🚨 NEW BREACH ALERT: {alert.breach_name} ({alert.severity.upper()})")
        print(f"   Email: {alert.email}")
        print(f"   Date: {alert.breach_date.strftime('%Y-%m-%d')}")
        print(f"   Compromised: {', '.join(alert.compromised_data)}")
        
        # Send notification (if configured)
        await self._send_breach_notification(alert)
    
    async def _send_breach_notification(self, alert: BreachAlert):
        """Send breach notification via email/SMS."""
        try:
            if hasattr(settings, 'notification_email') and settings.notification_email:
                await self._send_email_notification(alert)
            
            if hasattr(settings, 'notification_webhook') and settings.notification_webhook:
                await self._send_webhook_notification(alert)
                
        except Exception as e:
            print(f"Warning: Could not send breach notification: {e}")
    
    async def _send_email_notification(self, alert: BreachAlert):
        """Send email notification."""
        # This would integrate with email service
        print(f"📧 Email notification sent for breach: {alert.breach_name}")
    
    async def _send_webhook_notification(self, alert: BreachAlert):
        """Send webhook notification."""
        # This would send to Slack, Discord, etc.
        print(f"🔗 Webhook notification sent for breach: {alert.breach_name}")


class DarkWebMonitor:
    """Monitor dark web for exposed personal information."""
    
    def __init__(self):
        # This would integrate with dark web monitoring services
        pass
    
    async def scan_for_exposed_data(self, personal_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Scan dark web for exposed personal information."""
        # This is a placeholder for dark web monitoring
        # In practice, this would integrate with services like:
        # - SpyCloud
        # - Digital Shadows
        # - Recorded Future
        
        print("🕵️ Dark web monitoring would scan for:")
        for key, value in personal_info.items():
            if value:
                print(f"  • {key}: {value}")
        
        # Return mock findings for demo
        return []


class ThreatIntelligence:
    """Threat intelligence and risk assessment."""
    
    def __init__(self):
        self.threat_feeds = []
    
    async def assess_exposure_risk(self, profile_data: List[ProfileData]) -> Dict[str, Any]:
        """Assess exposure risk based on threat intelligence."""
        risk_factors = []
        
        # Analyze exposed information types
        exposed_data_types = set()
        for profile in profile_data:
            if profile.metadata.get('email'):
                exposed_data_types.add('email')
            if profile.metadata.get('location'):
                exposed_data_types.add('location')
            if profile.metadata.get('company'):
                exposed_data_types.add('employer')
        
        # Calculate risk multipliers
        base_risk = len(exposed_data_types) * 1.5
        
        # Industry-specific risks
        tech_keywords = {'engineer', 'developer', 'programmer', 'software', 'tech'}
        finance_keywords = {'bank', 'finance', 'investment', 'trading'}
        
        for profile in profile_data:
            profile_text_lower = profile.profile_text.lower()
            
            if any(keyword in profile_text_lower for keyword in tech_keywords):
                risk_factors.append("Tech industry targeting risk")
                base_risk *= 1.2
            
            if any(keyword in profile_text_lower for keyword in finance_keywords):
                risk_factors.append("Finance industry targeting risk")
                base_risk *= 1.3
        
        return {
            "overall_risk": min(base_risk, 10.0),
            "risk_factors": risk_factors,
            "exposed_data_types": list(exposed_data_types),
            "recommendations": self._generate_threat_recommendations(risk_factors)
        }
    
    def _generate_threat_recommendations(self, risk_factors: List[str]) -> List[str]:
        """Generate threat-specific recommendations."""
        recommendations = []
        
        if "Tech industry targeting risk" in risk_factors:
            recommendations.extend([
                "Consider using separate professional and personal social media accounts",
                "Be cautious about sharing technical project details publicly",
                "Use strong, unique passwords for all development accounts"
            ])
        
        if "Finance industry targeting risk" in risk_factors:
            recommendations.extend([
                "Enable 2FA on all financial and work-related accounts",
                "Avoid sharing work location or schedule patterns",
                "Be extra cautious about phishing attempts"
            ])
        
        return recommendations
