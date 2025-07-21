# Contributing to How Much Does AI Know You?

Thank you for your interest in contributing to this privacy-focused project! We welcome contributions from developers, privacy advocates, and anyone interested in digital privacy.

## 🎯 Project Goals

- Help users understand their digital privacy exposure
- Provide actionable privacy recommendations
- Maintain ethical AI practices
- Keep the tool free and open-source

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Git
- API keys for AI providers (OpenAI, Anthropic, etc.)
- Platform API tokens (GitHub, Twitter, etc.)

### Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/YOUR-USERNAME/How-Much-Does-AI-Know-You.git
   cd How-Much-Does-AI-Know-You
   ```

2. **Set up Python environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -e ".[dev]"
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

4. **Run tests**
   ```bash
   pytest tests/
   ```

5. **Start development server**
   ```bash
   ai-audit serve --port 8000
   ```

## 📝 How to Contribute

### 1. Issues

- **Bug Reports**: Use the bug report template
- **Feature Requests**: Use the feature request template
- **Privacy Concerns**: Label with "privacy" tag

### 2. Pull Requests

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Follow the existing code style
   - Add tests for new functionality
   - Update documentation if needed

3. **Test your changes**
   ```bash
   # Run tests
   pytest tests/
   
   # Check code style
   black src/ tests/
   isort src/ tests/
   flake8 src/ tests/
   
   # Type checking
   mypy src/
   ```

4. **Submit pull request**
   - Use the pull request template
   - Reference any related issues
   - Include screenshots for UI changes

### 3. Code Style

We use Python best practices:

- **Black** for code formatting
- **isort** for import sorting
- **flake8** for linting
- **mypy** for type checking
- **pytest** for testing

```bash
# Format code
black src/ tests/
isort src/ tests/

# Check style
flake8 src/ tests/
mypy src/
```

## 🏗️ Architecture Overview

```
src/ai_audit/
├── cli.py              # Command-line interface
├── config.py           # Configuration management
├── models.py           # Data models
├── analyzer.py         # Privacy risk analysis
├── connectors/         # Platform integrations
│   ├── github.py
│   ├── twitter.py
│   └── ...
├── inference/          # AI inference engines
├── storage/            # Local data storage
└── web/                # Web dashboard
    └── server.py
```

## 🔒 Privacy Guidelines

This project handles sensitive personal data. Please follow these guidelines:

### Data Handling
- **Minimize data collection**: Only collect what's necessary
- **Local storage first**: Default to local storage over cloud
- **User consent**: Always ask before analyzing someone's data
- **Anonymization**: Remove/hash sensitive data when possible

### AI Ethics
- **Responsible inference**: Don't make harmful or invasive conclusions
- **Transparency**: Explain how inferences are made
- **Bias awareness**: Consider AI model biases
- **User control**: Let users control what data is analyzed

### Security
- **API key protection**: Never commit API keys
- **Input validation**: Validate all user inputs
- **Rate limiting**: Respect platform API limits
- **Error handling**: Don't expose sensitive info in errors

## 🧪 Testing

### Test Types

1. **Unit Tests**: Test individual components
   ```bash
   pytest tests/test_models.py
   ```

2. **Integration Tests**: Test component interactions
   ```bash
   pytest tests/test_connectors.py
   ```

3. **Privacy Tests**: Verify privacy protections
   ```bash
   pytest tests/test_privacy.py
   ```

### Test Guidelines

- Mock external API calls
- Test error conditions
- Verify privacy protections
- Test with various data formats

## 📚 Documentation

### Code Documentation
- Use docstrings for all public functions
- Include type hints
- Comment complex algorithms

### User Documentation
- Update README.md for new features
- Add CLI help text
- Document configuration options

## 🔄 Release Process

1. **Version Bump**: Update version in `pyproject.toml`
2. **Changelog**: Update CHANGELOG.md
3. **Testing**: Run full test suite
4. **Tag Release**: Create git tag
5. **Publish**: Create GitHub release

## 🤝 Community

### Communication
- **GitHub Discussions**: For general questions
- **Issues**: For bugs and feature requests
- **Pull Requests**: For code contributions

### Code of Conduct
- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and contribute
- Respect privacy and security concerns

## 🏷️ Labels

We use these labels for organization:

- `bug`: Something isn't working
- `enhancement`: New feature or request
- `privacy`: Privacy-related issue
- `security`: Security concern
- `good first issue`: Good for newcomers
- `help wanted`: Extra attention needed
- `platform:github`: GitHub-specific
- `platform:twitter`: Twitter-specific
- `ai:inference`: AI inference related

## ❓ Questions?

- Check existing [Issues](https://github.com/sonishsivarajkumar/How-Much-Does-AI-Know-You/issues)
- Start a [Discussion](https://github.com/sonishsivarajkumar/How-Much-Does-AI-Know-You/discussions)
- Read the [Documentation](https://github.com/sonishsivarajkumar/How-Much-Does-AI-Know-You/wiki)

Thank you for contributing to digital privacy! 🛡️
