#!/bin/bash

# Quick setup script for How Much Does AI Know You?
# This script helps you get started quickly with the tool

set -e

echo "🛡️  Setting up How Much Does AI Know You? ..."
echo

# Check if Python 3.8+ is available
python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
required_version="3.8"

if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)" 2>/dev/null; then
    echo "❌ Python 3.8+ is required. Found: $python_version"
    echo "Please install Python 3.8 or later and try again."
    exit 1
fi

echo "✅ Python version check passed: $(python3 --version)"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install the package
echo "📥 Installing AI Audit..."
pip install -e .

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "⚙️  Creating configuration file..."
    cp .env.example .env
    echo "📝 Please edit .env file with your API keys:"
    echo "   - OpenAI API key (required)"
    echo "   - GitHub token (required for GitHub analysis)"
    echo "   - Twitter Bearer token (required for Twitter analysis)"
    echo
else
    echo "✅ Configuration file (.env) already exists"
fi

# Test installation
echo "🧪 Testing installation..."
if ai-audit --version > /dev/null 2>&1; then
    echo "✅ Installation successful!"
else
    echo "❌ Installation test failed"
    exit 1
fi

echo
echo "🎉 Setup complete! Here's what you can do next:"
echo
echo "1. Configure your API keys:"
echo "   nano .env"
echo
echo "2. Check your configuration:"
echo "   ai-audit status"
echo
echo "3. Run your first privacy audit:"
echo "   ai-audit scan --platforms github --username YOUR_GITHUB_USERNAME"
echo
echo "4. Start the web dashboard:"
echo "   ai-audit serve"
echo
echo "5. Get help:"
echo "   ai-audit --help"
echo
echo "📚 Read the full documentation: https://github.com/sonishsivarajkumar/How-Much-Does-AI-Know-You"
echo "🔒 Remember: This tool is for auditing YOUR OWN data only!"
echo
