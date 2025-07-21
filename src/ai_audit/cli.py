"""Command Line Interface for AI Audit."""

import asyncio
import click
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.panel import Panel

from .config import settings
from .models import Platform, ScanSession, PrivacyRisk, Recommendation, AuditReport
from .connectors.github import GitHubConnector
from .connectors.twitter import TwitterConnector
from .inference import InferenceOrchestrator
from .storage import db
from .analyzer import PrivacyAnalyzer
from .web.server import start_web_server

# New imports for Phase 2 & 3
from .connectors.reddit import RedditConnector
from .connectors.linkedin import LinkedInConnector
from .monitoring import BreachMonitor, ThreatIntelligence
from .automation import RemediationEngine, SmartRemediation
from .plugins import plugin_manager
from .browser_extension import extension_api, ExtensionManifestGenerator

console = Console()


@click.group()
@click.version_option(version="0.1.0")
def main():
    """AI Audit - Discover what AI models can infer about you from your public data."""
    pass


@main.command()
@click.option("--platforms", "-p", default="github,twitter", 
              help="Comma-separated list of platforms to scan (github,twitter)")
@click.option("--username", "-u", help="Username to analyze (if different from config)")
@click.option("--output", "-o", type=click.Path(), help="Output file for results")
@click.option("--format", "-f", type=click.Choice(["json", "text"]), default="text",
              help="Output format")
def scan(platforms: str, username: Optional[str], output: Optional[str], format: str):
    """Run a complete privacy audit scan."""
    console.print(Panel.fit("🔍 Starting Privacy Audit Scan", style="bold blue"))
    
    try:
        asyncio.run(_run_scan(platforms, username, output, format))
    except KeyboardInterrupt:
        console.print("\n❌ Scan cancelled by user", style="yellow")
    except Exception as e:
        console.print(f"❌ Scan failed: {e}", style="red")


async def _run_scan(platforms: str, username: Optional[str], output: Optional[str], format: str):
    """Run the actual scan process."""
    # Initialize database
    await db.initialize()
    
    # Parse platforms
    platform_list = [Platform(p.strip()) for p in platforms.split(",")]
    
    # Create scan session
    session_id = str(uuid.uuid4())
    session = ScanSession(
        session_id=session_id,
        platforms=platform_list
    )
    await db.create_scan_session(session)
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            # Collect profile data
            task = progress.add_task("Collecting profile data...", total=None)
            profile_data_list = await _collect_profile_data(platform_list, username, progress, task)
            
            if not profile_data_list:
                console.print("❌ No profile data collected", style="red")
                await db.update_scan_session(session_id, "failed", "No profile data collected")
                return
            
            # Make inferences
            progress.update(task, description="Analyzing with AI models...")
            orchestrator = InferenceOrchestrator()
            inferences = await orchestrator.analyze_profiles(profile_data_list)
            
            # Store inferences
            for inference in inferences:
                await db.store_inference(inference)
            
            # Generate privacy analysis
            progress.update(task, description="Calculating privacy risk...")
            analyzer = PrivacyAnalyzer()
            privacy_risk = analyzer.calculate_privacy_risk(inferences, profile_data_list)
            recommendations = analyzer.generate_recommendations(inferences, profile_data_list)
            
            # Create audit report
            report = AuditReport(
                user_id=username or "current_user",
                platforms_analyzed=platform_list,
                profile_data=profile_data_list,
                inferences=inferences,
                privacy_risk=privacy_risk,
                recommendations=recommendations
            )
            
            # Store report
            await db.store_audit_report(report)
            await db.update_scan_session(session_id, "completed")
            
            progress.update(task, description="✅ Scan completed!")
        
        # Display results
        _display_results(report, format)
        
        # Save to file if requested
        if output:
            _save_results(report, output, format)
            console.print(f"📄 Results saved to {output}")
    
    except Exception as e:
        await db.update_scan_session(session_id, "failed", str(e))
        raise


async def _collect_profile_data(platform_list: List[Platform], username: Optional[str], progress, task):
    """Collect profile data from specified platforms."""
    profile_data_list = []
    
    for platform in platform_list:
        try:
            progress.update(task, description=f"Collecting data from {platform.value}...")
            
            if platform == Platform.GITHUB:
                connector = GitHubConnector()
                if not connector.is_configured():
                    console.print(f"⚠️  GitHub token not configured, skipping...", style="yellow")
                    continue
                
                # Use provided username or try to get current user
                target_username = username
                if not target_username:
                    # Try to get current authenticated user
                    try:
                        user = connector.client.get_user()
                        target_username = user.login
                    except:
                        console.print("⚠️  No GitHub username provided and could not detect current user", style="yellow")
                        continue
                
                profile_data = await connector.get_profile_data(target_username)
                
            elif platform == Platform.TWITTER:
                connector = TwitterConnector()
                if not connector.is_configured():
                    console.print(f"⚠️  Twitter token not configured, skipping...", style="yellow")
                    continue
                
                if not username:
                    console.print("⚠️  Twitter username required", style="yellow")
                    continue
                
                profile_data = await connector.get_profile_data(username)
            
            else:
                console.print(f"⚠️  Platform {platform.value} not yet supported", style="yellow")
                continue
            
            profile_data_list.append(profile_data)
            await db.store_profile_data(profile_data)
            
        except Exception as e:
            console.print(f"⚠️  Failed to collect {platform.value} data: {e}", style="yellow")
    
    return profile_data_list


def _display_results(report: AuditReport, format: str):
    """Display scan results."""
    if format == "json":
        console.print(report.json(indent=2))
        return
    
    # Text format display
    console.print("\n" + "="*60)
    console.print("🛡️  AI PRIVACY AUDIT REPORT", style="bold green", justify="center")
    console.print("="*60)
    
    # Summary
    risk_color = "red" if report.privacy_risk.overall_score >= 7 else "yellow" if report.privacy_risk.overall_score >= 4 else "green"
    console.print(f"\n📊 Overall Privacy Risk: {report.privacy_risk.overall_score:.1f}/10", style=f"bold {risk_color}")
    console.print(f"🔍 Platforms Analyzed: {', '.join([p.value for p in report.platforms_analyzed])}")
    console.print(f"🤖 Inferences Made: {len(report.inferences)}")
    
    # High-confidence inferences
    high_conf_inferences = [i for i in report.inferences if i.confidence >= 0.7]
    if high_conf_inferences:
        console.print("\n🎯 High-Confidence Inferences:", style="bold")
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Type", style="cyan")
        table.add_column("Value", style="white")
        table.add_column("Confidence", style="green")
        table.add_column("Source", style="blue")
        
        for inference in high_conf_inferences[:10]:  # Show top 10
            platforms = ", ".join([p.value for p in inference.source_platforms])
            table.add_row(
                inference.type.value.replace("_", " ").title(),
                inference.value[:50] + "..." if len(inference.value) > 50 else inference.value,
                f"{inference.confidence:.0%}",
                platforms
            )
        
        console.print(table)
    
    # Recommendations
    if report.recommendations:
        console.print("\n💡 Privacy Recommendations:", style="bold")
        
        for i, rec in enumerate(report.recommendations[:5], 1):  # Show top 5
            priority_color = "red" if rec.priority == "high" else "yellow" if rec.priority == "medium" else "green"
            console.print(f"\n{i}. {rec.title}", style=f"bold {priority_color}")
            console.print(f"   {rec.description}")
            
            if rec.action_items:
                console.print("   Action items:")
                for item in rec.action_items:
                    console.print(f"   • {item}")
    
    console.print(f"\n📅 Generated: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}")


def _save_results(report: AuditReport, output_path: str, format: str):
    """Save results to file."""
    path = Path(output_path)
    
    if format == "json":
        path.write_text(report.json(indent=2))
    else:
        # Generate text report
        text_report = _generate_text_report(report)
        path.write_text(text_report)


def _generate_text_report(report: AuditReport) -> str:
    """Generate a text-based report."""
    lines = []
    lines.append("AI PRIVACY AUDIT REPORT")
    lines.append("=" * 50)
    lines.append("")
    lines.append(f"Generated: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Platforms: {', '.join([p.value for p in report.platforms_analyzed])}")
    lines.append(f"Privacy Risk Score: {report.privacy_risk.overall_score:.1f}/10")
    lines.append("")
    
    lines.append("HIGH-CONFIDENCE INFERENCES:")
    lines.append("-" * 30)
    high_conf = [i for i in report.inferences if i.confidence >= 0.7]
    for inference in high_conf:
        lines.append(f"• {inference.type.value.replace('_', ' ').title()}: {inference.value} ({inference.confidence:.0%})")
    
    lines.append("")
    lines.append("RECOMMENDATIONS:")
    lines.append("-" * 30)
    for i, rec in enumerate(report.recommendations, 1):
        lines.append(f"{i}. {rec.title}")
        lines.append(f"   {rec.description}")
        lines.append("")
    
    return "\n".join(lines)


@main.command("analyze-github")
@click.option("--username", "-u", required=True, help="GitHub username to analyze")
def analyze_github(username: str):
    """Analyze a specific GitHub profile."""
    asyncio.run(_analyze_github(username))


async def _analyze_github(username: str):
    """Analyze GitHub profile."""
    console.print(f"🔍 Analyzing GitHub profile: {username}")
    
    try:
        connector = GitHubConnector()
        if not connector.is_configured():
            console.print("❌ GitHub token not configured", style="red")
            return
        
        profile_data = await connector.get_profile_data(username)
        console.print("✅ Profile data collected")
        
        # Quick analysis display
        console.print(f"\n📊 Profile Summary:")
        console.print(f"• Repositories: {profile_data.metadata.get('public_repos', 'N/A')}")
        console.print(f"• Followers: {profile_data.metadata.get('followers', 'N/A')}")
        console.print(f"• Location: {profile_data.metadata.get('location', 'Not specified')}")
        console.print(f"• Company: {profile_data.metadata.get('company', 'Not specified')}")
        
    except Exception as e:
        console.print(f"❌ Analysis failed: {e}", style="red")


@main.command("analyze-reddit")
@click.option("--username", "-u", required=True, help="Reddit username to analyze")
def analyze_reddit(username: str):
    """Analyze a specific Reddit profile."""
    asyncio.run(_analyze_reddit(username))


async def _analyze_reddit(username: str):
    """Analyze Reddit profile."""
    console.print(f"🔍 Analyzing Reddit profile: {username}")
    
    try:
        connector = RedditConnector()
        if not connector.is_configured():
            console.print("❌ Reddit API credentials not configured", style="red")
            return
        
        profile_data = await connector.get_profile_data(username)
        console.print("✅ Profile data collected")
        
        # Quick analysis display
        console.print(f"\n📊 Profile Summary:")
        console.print(f"• Comment Karma: {profile_data.metadata.get('comment_karma', 'N/A')}")
        console.print(f"• Link Karma: {profile_data.metadata.get('link_karma', 'N/A')}")
        console.print(f"• Account Age: {profile_data.metadata.get('account_created', 'N/A')}")
        console.print(f"• Recent Comments: {profile_data.metadata.get('recent_comments_count', 'N/A')}")
        
    except Exception as e:
        console.print(f"❌ Analysis failed: {e}", style="red")


@main.command("analyze-linkedin")
@click.option("--username", "-u", required=True, help="LinkedIn username to analyze")
def analyze_linkedin(username: str):
    """Analyze a specific LinkedIn profile."""
    asyncio.run(_analyze_linkedin(username))


async def _analyze_linkedin(username: str):
    """Analyze LinkedIn profile."""
    console.print(f"🔍 Analyzing LinkedIn profile: {username}")
    
    try:
        connector = LinkedInConnector()
        profile_data = await connector.get_profile_data(username)
        console.print("✅ Profile data collected")
        
        # Quick analysis display
        console.print(f"\n📊 Profile Summary:")
        console.print(f"• Industry: {profile_data.metadata.get('industry', 'N/A')}")
        console.print(f"• Location: {profile_data.metadata.get('location', 'N/A')}")
        console.print(f"• Connections: {profile_data.metadata.get('connections_count', 'N/A')}")
        console.print(f"• Experience: {profile_data.metadata.get('experience_count', 'N/A')} positions")
        
    except Exception as e:
        console.print(f"❌ Analysis failed: {e}", style="red")


@main.command()
@click.option("--format", "-f", type=click.Choice(["json", "text", "pdf"]), default="text",
              help="Report format")
@click.option("--output", "-o", type=click.Path(), help="Output file")
def report(format: str, output: Optional[str]):
    """Generate a privacy report from stored data."""
    asyncio.run(_generate_report(format, output))


async def _generate_report(format: str, output: Optional[str]):
    """Generate report from stored data."""
    await db.initialize()
    
    # Get recent inferences
    inferences = await db.get_recent_inferences()
    
    if not inferences:
        console.print("❌ No data available. Run a scan first.", style="red")
        return
    
    console.print(f"📊 Found {len(inferences)} recent inferences")
    
    # Display summary
    high_conf = [i for i in inferences if i.confidence >= 0.7]
    console.print(f"🎯 High-confidence inferences: {len(high_conf)}")
    
    for inference in high_conf[:5]:
        console.print(f"• {inference.type.value}: {inference.value} ({inference.confidence:.0%})")


@main.command()
@click.option("--port", "-p", default=8000, help="Port to run web server on")
@click.option("--host", "-h", default="127.0.0.1", help="Host to bind to")
def serve(port: int, host: str):
    """Start the web dashboard."""
    console.print(f"🌐 Starting web dashboard at http://{host}:{port}")
    console.print("Press Ctrl+C to stop")
    
    try:
        start_web_server(host, port)
    except KeyboardInterrupt:
        console.print("\n👋 Web server stopped")


@main.command()
@click.option("--interval", type=click.Choice(["daily", "weekly"]), default="daily",
              help="Monitoring interval")
def monitor(interval: str):
    """Start continuous monitoring (placeholder)."""
    console.print(f"🔄 Starting {interval} monitoring...")
    console.print("⚠️  Monitoring feature coming in Phase 2")


@main.command()
def status():
    """Show configuration and system status."""
    console.print("🔧 AI Audit Status", style="bold blue")
    
    # Check API keys
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Service", style="cyan")
    table.add_column("Status", style="white")
    table.add_column("Notes", style="blue")
    
    # OpenAI
    openai_status = "✅ Configured" if settings.openai_api_key else "❌ Not configured"
    table.add_row("OpenAI", openai_status, "Required for AI inference")
    
    # Anthropic
    anthropic_status = "✅ Configured" if settings.anthropic_api_key else "❌ Not configured"
    table.add_row("Anthropic", anthropic_status, "Alternative AI provider")
    
    # GitHub
    github_status = "✅ Configured" if settings.github_token else "❌ Not configured"
    table.add_row("GitHub", github_status, "Required for GitHub analysis")
    
    # Twitter
    twitter_status = "✅ Configured" if settings.twitter_bearer_token else "❌ Not configured"
    table.add_row("Twitter", twitter_status, "Required for Twitter analysis")
    
    console.print(table)
    
    # Data directory
    console.print(f"\n📁 Data Directory: {settings.data_dir}")
    console.print(f"🎯 Default LLM: {settings.default_llm_provider}")


@main.command()
@click.option("--email", "-e", multiple=True, help="Email addresses to monitor")
@click.option("--continuous", "-c", is_flag=True, help="Run continuous monitoring")
@click.option("--interval", "-i", default=24, help="Check interval in hours")
def breach_monitor(email: tuple, continuous: bool, interval: int):
    """Monitor email addresses for data breaches."""
    if not email:
        console.print("❌ At least one email address required", style="red")
        return
    
    console.print(f"🔍 Monitoring {len(email)} email address(es) for breaches...")
    
    try:
        if continuous:
            asyncio.run(_run_continuous_breach_monitoring(list(email), interval))
        else:
            asyncio.run(_run_breach_check(list(email)))
    except KeyboardInterrupt:
        console.print("\n👋 Breach monitoring stopped")


async def _run_breach_check(email_list: List[str]):
    """Run a one-time breach check."""
    monitor = BreachMonitor()
    
    for email in email_list:
        console.print(f"Checking: {email}")
        alerts = await monitor.check_email_breaches(email)
        
        if alerts:
            console.print(f"🚨 Found {len(alerts)} breach(es) for {email}:", style="red")
            for alert in alerts:
                console.print(f"  • {alert.breach_name} ({alert.severity}) - {alert.breach_date.strftime('%Y-%m-%d')}")
        else:
            console.print(f"✅ No breaches found for {email}", style="green")


async def _run_continuous_breach_monitoring(email_list: List[str], interval: int):
    """Run continuous breach monitoring."""
    monitor = BreachMonitor()
    await monitor.continuous_monitoring(email_list, interval)


@main.command("auto-remediate")
@click.option("--platforms", "-p", default="github,twitter", 
              help="Platforms to analyze for remediation")
@click.option("--username", "-u", help="Username to analyze")
@click.option("--dry-run", "-d", is_flag=True, help="Show actions without executing")
@click.option("--schedule-delay", "-s", default=1, help="Delay between actions in hours")
def auto_remediate(platforms: str, username: Optional[str], dry_run: bool, schedule_delay: int):
    """Run automated privacy remediation."""
    console.print("🔧 Starting automated privacy remediation...")
    
    try:
        asyncio.run(_run_auto_remediation(platforms, username, dry_run, schedule_delay))
    except KeyboardInterrupt:
        console.print("\n❌ Remediation cancelled")


async def _run_auto_remediation(platforms: str, username: Optional[str], dry_run: bool, schedule_delay: int):
    """Run automated remediation process."""
    # Initialize components
    await db.initialize()
    
    # Collect profile data
    platform_list = [Platform(p.strip()) for p in platforms.split(",")]
    profile_data_list = await _collect_profile_data(platform_list, username, None, None)
    
    if not profile_data_list:
        console.print("❌ No profile data collected", style="red")
        return
    
    # Get inferences
    orchestrator = InferenceOrchestrator()
    inferences = await orchestrator.analyze_profiles(profile_data_list)
    
    # Create remediation actions
    remediation_engine = RemediationEngine()
    actions = await remediation_engine.analyze_and_create_actions(profile_data_list, inferences, [])
    
    if not actions:
        console.print("✅ No remediation actions needed", style="green")
        return
    
    console.print(f"📋 Found {len(actions)} remediation actions:")
    
    for i, action in enumerate(actions, 1):
        console.print(f"{i}. {action.description}")
        console.print(f"   Platform: {action.platform.value}")
        console.print(f"   Type: {action.action_type}")
    
    if dry_run:
        console.print("\n🔍 Dry run completed - no actions executed")
        return
    
    # Execute actions
    if click.confirm("\nProceed with remediation actions?"):
        await remediation_engine.schedule_and_execute_actions(actions)
        console.print("✅ Remediation completed")


@main.command("plugins")
@click.option("--list", "-l", "list_plugins", is_flag=True, help="List available plugins")
@click.option("--enable", "-e", help="Enable a plugin")
@click.option("--disable", "-d", help="Disable a plugin")
@click.option("--install", "-i", help="Install a plugin from path")
def plugins(list_plugins: bool, enable: Optional[str], disable: Optional[str], install: Optional[str]):
    """Manage AI Audit plugins."""
    asyncio.run(_manage_plugins(list_plugins, enable, disable, install))


async def _manage_plugins(list_plugins: bool, enable: Optional[str], disable: Optional[str], install: Optional[str]):
    """Manage plugins."""
    await plugin_manager.initialize()
    
    if list_plugins:
        plugins_list = plugin_manager.get_plugin_list()
        
        console.print("🔌 Available Plugins:", style="bold blue")
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Name", style="cyan")
        table.add_column("Version", style="white")
        table.add_column("Type", style="blue")
        table.add_column("Status", style="green")
        table.add_column("Description", style="white")
        
        for plugin in plugins_list:
            status = "✅ Enabled" if plugin["enabled"] else "❌ Disabled"
            table.add_row(
                plugin["name"],
                plugin["version"],
                plugin["type"],
                status,
                plugin["description"][:50] + "..." if len(plugin["description"]) > 50 else plugin["description"]
            )
        
        console.print(table)
    
    elif enable:
        success = await plugin_manager.enable_plugin(enable)
        if success:
            console.print(f"✅ Plugin '{enable}' enabled", style="green")
        else:
            console.print(f"❌ Failed to enable plugin '{enable}'", style="red")
    
    elif disable:
        success = await plugin_manager.disable_plugin(disable)
        if success:
            console.print(f"✅ Plugin '{disable}' disabled", style="green")
        else:
            console.print(f"❌ Failed to disable plugin '{disable}'", style="red")
    
    elif install:
        success = await plugin_manager.install_plugin(install)
        if success:
            console.print(f"✅ Plugin installed from '{install}'", style="green")
        else:
            console.print(f"❌ Failed to install plugin from '{install}'", style="red")


@main.command("browser-extension")
@click.option("--generate", "-g", is_flag=True, help="Generate browser extension files")
@click.option("--serve-api", "-s", is_flag=True, help="Serve browser extension API")
def browser_extension(generate: bool, serve_api: bool):
    """Manage browser extension integration."""
    if generate:
        generator = ExtensionManifestGenerator()
        extension_dir = generator.generate_all_files()
        console.print(f"🌐 Browser extension generated in: {extension_dir}")
        console.print("To install:")
        console.print("1. Open Chrome and go to chrome://extensions/")
        console.print("2. Enable Developer mode")
        console.print("3. Click 'Load unpacked' and select the extension directory")
    
    elif serve_api:
        console.print("🔌 Starting browser extension API server...")
        # This would start the API server for browser extension communication
        console.print("API server would run alongside the main web server")


@main.command("threat-intel")
@click.option("--platforms", "-p", default="github,twitter", 
              help="Platforms to analyze for threats")
@click.option("--username", "-u", help="Username to analyze")
def threat_intel(platforms: str, username: Optional[str]):
    """Run threat intelligence analysis."""
    console.print("🕵️ Running threat intelligence analysis...")
    
    try:
        asyncio.run(_run_threat_analysis(platforms, username))
    except Exception as e:
        console.print(f"❌ Threat analysis failed: {e}", style="red")


async def _run_threat_analysis(platforms: str, username: Optional[str]):
    """Run threat intelligence analysis."""
    # Collect profile data
    platform_list = [Platform(p.strip()) for p in platforms.split(",")]
    profile_data_list = await _collect_profile_data(platform_list, username, None, None)
    
    if not profile_data_list:
        console.print("❌ No profile data collected", style="red")
        return
    
    # Run threat analysis
    threat_intel = ThreatIntelligence()
    risk_assessment = await threat_intel.assess_exposure_risk(profile_data_list)
    
    console.print(f"\n🎯 Threat Intelligence Report:")
    console.print(f"Overall Risk Score: {risk_assessment['overall_risk']:.1f}/10")
    
    if risk_assessment['risk_factors']:
        console.print(f"\n⚠️ Risk Factors:")
        for factor in risk_assessment['risk_factors']:
            console.print(f"  • {factor}")
    
    if risk_assessment['exposed_data_types']:
        console.print(f"\n📊 Exposed Data Types:")
        for data_type in risk_assessment['exposed_data_types']:
            console.print(f"  • {data_type}")
    
    if risk_assessment['recommendations']:
        console.print(f"\n💡 Threat-Specific Recommendations:")
        for rec in risk_assessment['recommendations']:
            console.print(f"  • {rec}")


@main.command("full-audit")
@click.option("--platforms", "-p", default="github,twitter,reddit,linkedin", 
              help="Platforms to include in audit")
@click.option("--username", "-u", help="Username to analyze")
@click.option("--enable-monitoring", "-m", is_flag=True, help="Enable continuous monitoring")
@click.option("--enable-remediation", "-r", is_flag=True, help="Enable automated remediation")
@click.option("--output", "-o", type=click.Path(), help="Output file for comprehensive report")
def full_audit(platforms: str, username: Optional[str], enable_monitoring: bool, 
               enable_remediation: bool, output: Optional[str]):
    """Run a comprehensive privacy audit with all Phase 2 & 3 features."""
    console.print(Panel.fit("🔍 Starting Comprehensive Privacy Audit", style="bold blue"))
    
    try:
        asyncio.run(_run_full_audit(platforms, username, enable_monitoring, enable_remediation, output))
    except KeyboardInterrupt:
        console.print("\n❌ Audit cancelled by user", style="yellow")
    except Exception as e:
        console.print(f"❌ Audit failed: {e}", style="red")


async def _run_full_audit(platforms: str, username: Optional[str], enable_monitoring: bool, 
                         enable_remediation: bool, output: Optional[str]):
    """Run comprehensive audit with all features."""
    # Initialize all components
    await db.initialize()
    await plugin_manager.initialize()
    
    # Parse platforms
    platform_list = [Platform(p.strip()) for p in platforms.split(",") if p.strip()]
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        
        # Phase 1: Collect profile data
        task = progress.add_task("Collecting profile data from all platforms...", total=None)
        profile_data_list = []
        
        for platform in platform_list:
            try:
                progress.update(task, description=f"Collecting data from {platform.value}...")
                
                if platform == Platform.GITHUB:
                    connector = GitHubConnector()
                elif platform == Platform.TWITTER:
                    connector = TwitterConnector()
                elif platform == Platform.REDDIT:
                    connector = RedditConnector()
                elif platform == Platform.LINKEDIN:
                    connector = LinkedInConnector()
                else:
                    console.print(f"⚠️ Platform {platform.value} not yet supported", style="yellow")
                    continue
                
                if not connector.is_configured():
                    console.print(f"⚠️ {platform.value} not configured, skipping...", style="yellow")
                    continue
                
                # Get username for platform
                target_username = username
                if not target_username and platform == Platform.GITHUB:
                    try:
                        user = connector.client.get_user()
                        target_username = user.login
                    except:
                        console.print(f"⚠️ No {platform.value} username provided", style="yellow")
                        continue
                elif not target_username:
                    console.print(f"⚠️ No {platform.value} username provided", style="yellow")
                    continue
                
                profile_data = await connector.get_profile_data(target_username)
                profile_data_list.append(profile_data)
                await db.store_profile_data(profile_data)
                
            except Exception as e:
                console.print(f"⚠️ Failed to collect {platform.value} data: {e}", style="yellow")
        
        if not profile_data_list:
            console.print("❌ No profile data collected", style="red")
            return
        
        # Phase 2: AI Inference
        progress.update(task, description="Running AI inference analysis...")
        orchestrator = InferenceOrchestrator()
        inferences = await orchestrator.analyze_profiles(profile_data_list)
        
        for inference in inferences:
            await db.store_inference(inference)
        
        # Phase 3: Plugin Analysis
        progress.update(task, description="Running plugin analysis...")
        plugin_results = await plugin_manager.execute_analysis_plugins(profile_data_list, inferences)
        
        # Phase 4: Privacy Risk Assessment
        progress.update(task, description="Calculating privacy risk...")
        analyzer = PrivacyAnalyzer()
        privacy_risk = analyzer.calculate_privacy_risk(inferences, profile_data_list)
        recommendations = analyzer.generate_recommendations(inferences, profile_data_list)
        
        # Phase 5: Threat Intelligence
        progress.update(task, description="Running threat intelligence analysis...")
        threat_intel = ThreatIntelligence()
        threat_assessment = await threat_intel.assess_exposure_risk(profile_data_list)
        
        # Phase 6: Breach Monitoring
        emails_to_monitor = []
        for profile in profile_data_list:
            if profile.metadata.get('email'):
                emails_to_monitor.append(profile.metadata['email'])
        
        breach_alerts = []
        if emails_to_monitor:
            progress.update(task, description="Checking for data breaches...")
            monitor = BreachMonitor()
            breach_alerts = await monitor.scan_profile_emails(profile_data_list)
        
        # Phase 7: Automated Remediation
        remediation_actions = []
        if enable_remediation:
            progress.update(task, description="Generating remediation actions...")
            remediation_engine = RemediationEngine()
            remediation_actions = await remediation_engine.analyze_and_create_actions(
                profile_data_list, inferences, recommendations
            )
        
        # Create comprehensive report
        progress.update(task, description="Generating comprehensive report...")
        
        report = AuditReport(
            user_id=username or "current_user",
            platforms_analyzed=platform_list,
            profile_data=profile_data_list,
            inferences=inferences,
            privacy_risk=privacy_risk,
            recommendations=recommendations
        )
        
        # Store report
        await db.store_audit_report(report)
        
        progress.update(task, description="✅ Comprehensive audit completed!")
    
    # Display comprehensive results
    _display_comprehensive_results(report, plugin_results, threat_assessment, breach_alerts, remediation_actions)
    
    # Save comprehensive report
    if output:
        _save_comprehensive_report(report, plugin_results, threat_assessment, breach_alerts, output)
        console.print(f"📄 Comprehensive report saved to {output}")
    
    # Execute remediation if enabled
    if enable_remediation and remediation_actions:
        if click.confirm(f"\n🔧 Execute {len(remediation_actions)} remediation actions?"):
            remediation_engine = RemediationEngine()
            await remediation_engine.schedule_and_execute_actions(remediation_actions)
    
    # Start monitoring if enabled
    if enable_monitoring and emails_to_monitor:
        if click.confirm(f"\n🔄 Start continuous monitoring for {len(emails_to_monitor)} email(s)?"):
            console.print("Starting background monitoring... (Press Ctrl+C to stop)")
            monitor = BreachMonitor()
            await monitor.continuous_monitoring(emails_to_monitor, 24)


def _display_comprehensive_results(report, plugin_results, threat_assessment, breach_alerts, remediation_actions):
    """Display comprehensive audit results."""
    console.print("\n" + "="*80)
    console.print("🛡️ COMPREHENSIVE AI PRIVACY AUDIT REPORT", style="bold green", justify="center")
    console.print("="*80)
    
    # Basic metrics
    risk_color = "red" if report.privacy_risk.overall_score >= 7 else "yellow" if report.privacy_risk.overall_score >= 4 else "green"
    console.print(f"\n📊 Overall Privacy Risk: {report.privacy_risk.overall_score:.1f}/10", style=f"bold {risk_color}")
    console.print(f"🔍 Platforms Analyzed: {', '.join([p.value for p in report.platforms_analyzed])}")
    console.print(f"🤖 AI Inferences: {len(report.inferences)}")
    console.print(f"🎯 Threat Risk: {threat_assessment['overall_risk']:.1f}/10")
    
    # Breach alerts
    if breach_alerts:
        console.print(f"\n🚨 Data Breach Alerts: {len(breach_alerts)}", style="bold red")
        for alert in breach_alerts[:3]:  # Show top 3
            console.print(f"  • {alert.breach_name} ({alert.severity}) - {alert.email}")
    
    # Plugin results
    if plugin_results:
        console.print(f"\n🔌 Plugin Analysis Results:", style="bold blue")
        for plugin_name, results in plugin_results.items():
            console.print(f"  • {plugin_name}: {len(results)} findings")
    
    # Remediation actions
    if remediation_actions:
        console.print(f"\n🔧 Automated Remediation: {len(remediation_actions)} actions available", style="bold yellow")
    
    # High-confidence inferences (same as before)
    high_conf_inferences = [i for i in report.inferences if i.confidence >= 0.7]
    if high_conf_inferences:
        console.print("\n🎯 High-Confidence Inferences:", style="bold")
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Type", style="cyan")
        table.add_column("Value", style="white")
        table.add_column("Confidence", style="green")
        table.add_column("Source", style="blue")
        
        for inference in high_conf_inferences[:10]:
            platforms = ", ".join([p.value for p in inference.source_platforms])
            table.add_row(
                inference.type.value.replace("_", " ").title(),
                inference.value[:50] + "..." if len(inference.value) > 50 else inference.value,
                f"{inference.confidence:.0%}",
                platforms
            )
        
        console.print(table)


def _save_comprehensive_report(report, plugin_results, threat_assessment, breach_alerts, output_path):
    """Save comprehensive report to file."""
    path = Path(output_path)
    
    # Generate comprehensive report
    lines = []
    lines.append("COMPREHENSIVE AI PRIVACY AUDIT REPORT")
    lines.append("=" * 50)
    lines.append("")
    lines.append(f"Generated: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Platforms: {', '.join([p.value for p in report.platforms_analyzed])}")
    lines.append(f"Privacy Risk Score: {report.privacy_risk.overall_score:.1f}/10")
    lines.append(f"Threat Risk Score: {threat_assessment['overall_risk']:.1f}/10")
    lines.append("")
    
    # Add all sections...
    # (Similar to existing report generation but more comprehensive)
    
    path.write_text("\n".join(lines))
