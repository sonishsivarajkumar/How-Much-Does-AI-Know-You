# How Much Does AI Know You?

An open-source toolkit that helps you audit your "exposure" to AI models and data brokers by analyzing your public digital footprint.

## ⚡ Quick Demo

Want to see it in action immediately? Try these commands:

```bash
# Install and run (takes ~2 minutes)
git clone https://github.com/sonishsivarajkumar/How-Much-Does-AI-Know-You.git
cd How-Much-Does-AI-Know-You
pip install -e .

# Quick status check
ai-audit status

# Demo with mock data (no API keys needed)
export DEMO_MODE=true
ai-audit scan --platforms github,twitter --username demo_user

# See all available commands
ai-audit --help
```

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

## ▶️ How to Run the App

### 1. Initial Setup & Verification

```bash
# Check system status and configuration
ai-audit status

# Verify all components are working
ai-audit --help
```

### 2. Basic Privacy Audit

```bash
# Quick scan of GitHub and Twitter
ai-audit scan --platforms github,twitter --username your-username

# Analyze a specific platform
ai-audit analyze-github --username your-github-username
ai-audit analyze-reddit --username your-reddit-username
```

### 3. Advanced Phase 2 Features

```bash
# Comprehensive breach monitoring
ai-audit breach-monitor --email your-email@example.com

# Automated privacy remediation (dry-run first)
ai-audit auto-remediate --platforms github,twitter --dry-run
ai-audit auto-remediate --platforms github,twitter --schedule-delay 2

# LinkedIn professional analysis
ai-audit analyze-linkedin --username your-linkedin-username
```

### 4. Advanced Phase 3 Features

```bash
# Full audit with all advanced features
ai-audit full-audit --platforms github,twitter,reddit,linkedin \
  --enable-monitoring --enable-remediation

# Plugin management
ai-audit plugins --list
ai-audit plugins --enable WearableHealthPlugin

# Browser extension setup
ai-audit browser-extension --generate
ai-audit browser-extension --serve-api

# Threat intelligence analysis
ai-audit threat-intel --platforms all --username your-username
```

### 5. Web Dashboard

```bash
# Start the web server
ai-audit serve --port 8000 --host 0.0.0.0

# Access the dashboard at: http://localhost:8000
```

### 6. Generate Reports

```bash
# Generate comprehensive privacy report
ai-audit report --format json --output my-privacy-report.json
ai-audit report --format text --output my-privacy-report.txt
```

### 7. Real-Time Monitoring

```bash
# Start continuous monitoring
ai-audit monitor --schedule daily --platforms all

# Check monitoring status
ai-audit status
```

## 📋 Step-by-Step First Run

### Step 1: Configure Your API Keys
Edit `.env` file with your credentials:
```bash
# Required: At least one AI API
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here

# Platform APIs (configure as needed)
GITHUB_TOKEN=your_github_token
TWITTER_BEARER_TOKEN=your_twitter_token
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_secret
LINKEDIN_CLIENT_ID=your_linkedin_client_id
LINKEDIN_CLIENT_SECRET=your_linkedin_secret

# Optional: Breach monitoring
HIBP_API_KEY=your_haveibeenpwned_key
```

### Step 2: Verify Installation
```bash
ai-audit status
```
Expected output:
```
✅ AI Audit Status
┏━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Service   ┃ Status        ┃ Notes                         ┃
┡━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ OpenAI    │ ✅ Configured │ Required for AI inference     │
│ GitHub    │ ✅ Configured │ Required for GitHub analysis  │
└───────────┴───────────────┴───────────────────────────────┘
```

### Step 3: Run Your First Privacy Audit
```bash
# Start with a basic scan
ai-audit scan --platforms github --username your-username

# Or run the comprehensive audit
ai-audit full-audit --platforms github,twitter --username your-username
```

### Step 4: Explore Advanced Features
```bash
# Check for data breaches
ai-audit breach-monitor --email your-email@example.com

# List available plugins
ai-audit plugins --list

# Generate browser extension
ai-audit browser-extension --generate
```

### Step 5: Access Web Dashboard
```bash
# Start web server
ai-audit serve

# Open your browser to: http://localhost:8000
```

## 🔧 Configuration Options

### Environment Variables
```bash
# Core settings
DEBUG=true                          # Enable debug logging
DEMO_MODE=true                      # Use mock data for testing

# Privacy settings
ANONYMIZE_DATA=true                 # Anonymize sensitive data
RETAIN_RAW_DATA=false              # Keep raw API responses

# Performance settings
MAX_INFERENCE_REQUESTS=10          # Concurrent AI requests
CACHE_TTL=3600                     # Cache expiration (seconds)

# Monitoring settings
MONITORING_ENABLED=true            # Enable continuous monitoring
AUTO_REMEDIATION_ENABLED=false     # Enable automated fixes

# Plugin settings
PLUGINS_ENABLED=true               # Enable plugin system
EXTENSION_ENABLED=true             # Enable browser extension
```

## 🚨 Troubleshooting

### Common Issues

#### 1. "No API key configured"
```bash
# Check your .env file exists
ls -la .env

# Verify API keys are set
ai-audit status
```

#### 2. "Package not found"
```bash
# Reinstall in development mode
pip install -e .

# Check installation
ai-audit --version
```

#### 3. "Platform API errors"
```bash
# Test with demo mode
export DEMO_MODE=true
ai-audit scan --platforms github --username demo_user
```

#### 4. Web dashboard not accessible
```bash
# Check if server is running
ai-audit serve --host 0.0.0.0 --port 8000

# Try different port
ai-audit serve --port 8080
```

### Debug Mode
```bash
# Enable verbose logging
export DEBUG=true
ai-audit scan --platforms github --username your-username
```

## 🎯 Example Workflows

### Personal Privacy Audit
```bash
# 1. Check current exposure
ai-audit scan --platforms github,twitter --username your-username

# 2. Monitor for breaches
ai-audit breach-monitor --email your-email@example.com

# 3. Get remediation suggestions
ai-audit auto-remediate --dry-run --platforms all

# 4. Generate report
ai-audit report --output my-privacy-audit.json
```

### Enterprise Team Audit
```bash
# 1. Start web dashboard for team access
ai-audit serve --host 0.0.0.0 --port 8000

# 2. Run comprehensive audit
ai-audit full-audit --enable-monitoring --enable-remediation

# 3. Setup continuous monitoring
ai-audit monitor --schedule daily --platforms all
```

### Developer Integration
```bash
# 1. Enable plugins for custom analysis
ai-audit plugins --enable all

# 2. Generate browser extension
ai-audit browser-extension --generate

# 3. Setup API endpoint
ai-audit browser-extension --serve-api
```
