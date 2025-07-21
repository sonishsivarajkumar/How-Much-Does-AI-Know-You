#!/usr/bin/env python3
"""
Demo script for How Much Does AI Know You?

This script demonstrates the key features of the AI privacy audit tool
with mock data for testing purposes.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path

# Import our modules
from ai_audit.models import (
    ProfileData, Platform, Inference, InferenceType, 
    PrivacyRisk, Recommendation, AuditReport
)
from ai_audit.analyzer import PrivacyAnalyzer
from ai_audit.storage import db


async def create_demo_data():
    """Create mock demo data for testing."""
    
    # Mock GitHub profile data
    github_profile = ProfileData(
        platform=Platform.GITHUB,
        username="demo_user",
        user_id="12345",
        profile_text="""
Name: Demo Developer
Bio: Full-stack developer passionate about AI and privacy
Location: San Francisco, CA
Company: TechCorp Inc.
Public repositories: 25
Followers: 150
Following: 80
Member since: January 2020

Recent repositories include Python ML projects, JavaScript web apps, 
and Go microservices. Active contributor to open source privacy tools.
Commits typically between 9 PM - 1 AM PST.
        """,
        metadata={
            "followers": 150,
            "following": 80,
            "public_repos": 25,
            "location": "San Francisco, CA",
            "company": "TechCorp Inc.",
            "repositories": [
                {
                    "name": "privacy-toolkit",
                    "language": "Python",
                    "description": "Tools for digital privacy analysis"
                },
                {
                    "name": "web-dashboard",
                    "language": "JavaScript", 
                    "description": "React dashboard for data visualization"
                }
            ]
        }
    )
    
    # Mock Twitter profile data
    twitter_profile = ProfileData(
        platform=Platform.TWITTER,
        username="demo_user",
        user_id="67890",
        profile_text="""
Name: Demo Developer
Bio: Building the future of privacy tech 🛡️ | Coffee enthusiast ☕ | SF Bay Area
Location: San Francisco
Followers: 1250
Following: 400
Tweets: 890
Member since: March 2019

Recent tweet content shows interests in:
- AI/ML developments and privacy implications
- San Francisco tech scene and startup events  
- Coffee shop recommendations in SOMA district
- Weekend hiking in Marin County
- Support for privacy-focused legislation
        """,
        metadata={
            "followers_count": 1250,
            "following_count": 400,
            "tweet_count": 890,
            "location": "San Francisco",
            "recent_tweets_count": 15
        }
    )
    
    return [github_profile, twitter_profile]


def create_demo_inferences():
    """Create mock AI inferences."""
    
    inferences = [
        Inference(
            type=InferenceType.PROGRAMMING_SKILLS,
            value="Python, JavaScript, Go, React, Machine Learning",
            confidence=0.92,
            reasoning="Multiple repositories in these languages with meaningful commit history",
            source_platforms=[Platform.GITHUB],
            model_used="demo-ai-v1"
        ),
        
        Inference(
            type=InferenceType.LOCATION,
            value="San Francisco Bay Area, California",
            confidence=0.85,
            reasoning="Explicit location in profiles, local references in tweets",
            source_platforms=[Platform.GITHUB, Platform.TWITTER],
            model_used="demo-ai-v1"
        ),
        
        Inference(
            type=InferenceType.WORK_SCHEDULE,
            value="Night owl - primarily works 9 PM to 1 AM PST",
            confidence=0.78,
            reasoning="Consistent commit patterns during late evening hours",
            source_platforms=[Platform.GITHUB],
            model_used="demo-ai-v1"
        ),
        
        Inference(
            type=InferenceType.INTERESTS,
            value="AI/ML, Privacy Technology, Coffee, Hiking, Startups",
            confidence=0.88,
            reasoning="Project topics, bio content, and social media activity patterns",
            source_platforms=[Platform.GITHUB, Platform.TWITTER],
            model_used="demo-ai-v1"
        ),
        
        Inference(
            type=InferenceType.AGE_RANGE,
            value="28-35 years old",
            confidence=0.65,
            reasoning="Account creation dates, technology choices, and cultural references",
            source_platforms=[Platform.GITHUB, Platform.TWITTER],
            model_used="demo-ai-v1"
        ),
        
        Inference(
            type=InferenceType.SENTIMENT,
            value="Generally positive and professional, with tech-optimistic outlook",
            confidence=0.72,
            reasoning="Positive language patterns and constructive engagement style",
            source_platforms=[Platform.TWITTER],
            model_used="demo-ai-v1"
        ),
        
        Inference(
            type=InferenceType.EDUCATION_LEVEL,
            value="College-educated, likely computer science or related technical field",
            confidence=0.81,
            reasoning="Technical depth, communication style, and project complexity",
            source_platforms=[Platform.GITHUB],
            model_used="demo-ai-v1"
        ),
        
        Inference(
            type=InferenceType.PURCHASING_POWER,
            value="Above-average income, tech industry salary range",
            confidence=0.69,
            reasoning="San Francisco location, tech company employment, lifestyle indicators",
            source_platforms=[Platform.GITHUB, Platform.TWITTER],
            model_used="demo-ai-v1"
        )
    ]
    
    return inferences


async def run_demo():
    """Run the complete demo."""
    
    print("🛡️  How Much Does AI Know You? - Demo")
    print("=" * 50)
    print()
    
    # Initialize database
    print("📊 Initializing demo database...")
    await db.initialize()
    
    # Create demo profile data
    print("👤 Creating demo profile data...")
    profile_data = await create_demo_data()
    
    # Store profile data
    for profile in profile_data:
        await db.store_profile_data(profile)
    
    # Create demo inferences
    print("🤖 Generating AI inferences...")
    inferences = create_demo_inferences()
    
    # Store inferences
    for inference in inferences:
        await db.store_inference(inference)
    
    # Analyze privacy risk
    print("⚠️  Calculating privacy risk...")
    analyzer = PrivacyAnalyzer()
    privacy_risk = analyzer.calculate_privacy_risk(inferences, profile_data)
    recommendations = analyzer.generate_recommendations(inferences, profile_data)
    
    # Create audit report
    report = AuditReport(
        user_id="demo_user",
        platforms_analyzed=[Platform.GITHUB, Platform.TWITTER],
        profile_data=profile_data,
        inferences=inferences,
        privacy_risk=privacy_risk,
        recommendations=recommendations
    )
    
    # Store report
    await db.store_audit_report(report)
    
    # Display results
    print("📋 DEMO AUDIT RESULTS")
    print("-" * 30)
    print(f"🎯 Privacy Risk Score: {privacy_risk.overall_score:.1f}/10")
    print(f"🔍 Total Inferences: {len(inferences)}")
    print(f"⚠️  High Confidence: {len([i for i in inferences if i.confidence > 0.7])}")
    print()
    
    print("🎯 High-Confidence Inferences:")
    for inference in inferences:
        if inference.confidence > 0.7:
            confidence_pct = f"{inference.confidence:.0%}"
            print(f"  • {inference.type.value.replace('_', ' ').title()}: {inference.value[:60]}... ({confidence_pct})")
    
    print()
    print("💡 Privacy Recommendations:")
    for i, rec in enumerate(recommendations[:3], 1):
        priority_icon = "🔴" if rec.priority == "high" else "🟡" if rec.priority == "medium" else "🟢"
        print(f"  {i}. {priority_icon} {rec.title}")
        print(f"     {rec.description}")
    
    print()
    print("✅ Demo data created successfully!")
    print("🌐 Start the web dashboard to explore: ai-audit serve")
    print("📊 View stored data: ai-audit report")


if __name__ == "__main__":
    asyncio.run(run_demo())
