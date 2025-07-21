# How Much Does AI Know You?

An open-source toolkit that helps you audit your "exposure" to AI models and data brokers by analyzing your public digital footprint.

## 🎯 Core Goals

- **Visibility**: Reveal what personal signals AI APIs can infer about you
- **Auditability**: Generate "privacy scorecards" from your public footprint  
- **Actionability**: Recommend concrete steps to reduce unwanted exposure

## 🚀 Features

### Phase 1 (MVP) ✅ COMPLETED
- ✅ GitHub profile analysis
- ✅ Twitter/X profile analysis  
- ✅ LLM inference for core signals (dev skills, sentiment, location)
- ✅ CLI reporting tool
- ✅ Basic web dashboard

### Phase 2 (Expanded) ✅ COMPLETED
- ✅ Reddit & LinkedIn connectors
- ✅ Expanded inference types (health, political leaning, purchasing power, financial status)
- ✅ Real-time breach monitoring with HaveIBeenPwned integration
- ✅ Automated remediation suggestions & execution
- ✅ Enhanced privacy risk scoring

### Phase 3 (Advanced) ✅ COMPLETED  
- ✅ Real-time breach monitoring & threat intelligence
- ✅ Comprehensive plugin ecosystem
- ✅ Browser extension with real-time privacy analysis
- ✅ Advanced automated remediation with rollback capabilities
- ✅ Multi-platform continuous monitoring

## 🏗️ Architecture

```
├── CLI Tool (ai-audit)           # Command-line interface
├── Web Dashboard                 # React + Tailwind UI
├── FastAPI Backend              # API service
├── Data Connectors              # Platform integrations
├── Inference Engine             # LLM analysis
└── Local Storage                # SQLite cache
```

## 🔧 Installation

```bash
# Clone the repository
git clone git@github.com:sonishsivarajkumar/How-Much-Does-AI-Know-You.git
cd How-Much-Does-AI-Know-You

# Install dependencies
pip install -e .

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys
```

## 🚀 Quick Start

### CLI Usage

#### Basic Scanning
```bash
# Run a complete audit
ai-audit scan --platforms github,twitter --output report.json

# Analyze specific profile
ai-audit analyze-github --username your-username
```

#### Phase 2 Features
```bash
# Analyze Reddit & LinkedIn profiles
ai-audit analyze-reddit --username your-reddit-username
ai-audit analyze-linkedin --username your-linkedin-username

# Monitor for data breaches
ai-audit breach-monitor --email your-email@example.com

# Run automated remediation (dry-run first)
ai-audit auto-remediate --platforms github,twitter --dry-run
ai-audit auto-remediate --platforms github,twitter --schedule-delay 2
```

#### Phase 3 Features
```bash
# Comprehensive audit with all features
ai-audit full-audit --platforms github,twitter,reddit,linkedin \
  --enable-monitoring --enable-remediation

# Manage plugins
ai-audit plugins --list
ai-audit plugins --enable WearableHealthPlugin
ai-audit plugins --install TikTokConnectorPlugin

# Browser extension
ai-audit browser-extension --generate
ai-audit browser-extension --serve-api

# Threat intelligence analysis
ai-audit threat-intel --platforms github,twitter --username your-username

# System status
ai-audit status
```

### Web Dashboard

```bash
# Start web server
ai-audit serve --port 8000

# Visit http://localhost:8000 for interactive dashboard
```

### Plugin Development

```python
# Example custom plugin
from ai_audit.plugins import AnalysisPlugin

class MyCustomPlugin(AnalysisPlugin):
    def get_plugin_info(self):
        return {
            "name": "My Custom Analyzer",
            "version": "1.0.0",
            "description": "Custom privacy analysis"
        }
    
    async def analyze_data(self, profile_data, inferences):
        # Your custom analysis logic
        return {"custom_metric": 0.85}
```

## 🔧 Configuration

### Environment Variables

```bash
# Core AI APIs (at least one required)
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# Platform APIs
GITHUB_TOKEN=your_github_token
TWITTER_BEARER_TOKEN=your_twitter_token
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_secret
LINKEDIN_CLIENT_ID=your_linkedin_client_id
LINKEDIN_CLIENT_SECRET=your_linkedin_secret

# Phase 2 & 3 APIs
HIBP_API_KEY=your_haveibeenpwned_key

# Settings
MONITORING_ENABLED=true
AUTO_REMEDIATION_ENABLED=false
PLUGINS_ENABLED=true
EXTENSION_ENABLED=true
```

## 📊 Phase 2 & 3 Capabilities

### Enhanced Analysis
- **20+ Inference Types**: Health signals, political leaning, financial status, personality traits
- **Cross-Platform Correlation**: Combine insights from multiple platforms
- **Advanced Risk Scoring**: Sophisticated privacy risk assessment

### Automated Remediation
- **Smart Actions**: AI-powered remediation suggestions
- **Scheduled Execution**: Automated privacy improvements
- **Rollback Support**: Undo changes if needed
- **Platform Integration**: Direct API calls to update privacy settings

### Monitoring & Alerting
- **Breach Detection**: Real-time monitoring with HaveIBeenPwned
- **Threat Intelligence**: Advanced threat analysis
- **Continuous Monitoring**: Ongoing privacy posture assessment
- **Alert System**: Email notifications for privacy risks

### Plugin Ecosystem
- **Extensible Architecture**: Add custom analysis capabilities
- **Pre-built Plugins**: Health data, cryptocurrency, social signals
- **Plugin Marketplace**: Share and discover plugins
- **Sandboxed Execution**: Safe plugin environment

### Browser Extension
- **Real-time Analysis**: Analyze privacy risks as you browse
- **Risk Highlighting**: Visual indicators on risky elements
- **One-click Actions**: Quick privacy improvements
- **Cross-browser Support**: Chrome, Firefox, Safari
````
