# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-07-21

### Added
- Initial release of "How Much Does AI Know You?"
- CLI tool (`ai-audit`) with commands for scanning, reporting, and monitoring
- GitHub profile connector for analyzing repositories and commit patterns
- Twitter/X profile connector for analyzing tweets and profile data
- OpenAI and Anthropic inference engines for AI-based analysis
- Privacy risk scoring and recommendations system
- Local SQLite storage for audit data
- Web dashboard for viewing results and analytics
- Support for 10 inference types:
  - Programming skills
  - Location information
  - Age range estimation
  - Interests and hobbies
  - Sentiment analysis
  - Political leaning detection
  - Work schedule patterns
  - Education level
  - Health signals
  - Purchasing power indicators
- Privacy-by-design architecture with local data storage
- Configurable AI providers and platform connectors
- Rich CLI output with tables and progress indicators
- Comprehensive test suite
- Developer documentation and contribution guidelines

### Security
- API keys stored in environment variables only
- Optional data anonymization
- Local-first data storage approach
- No cloud dependencies by default

### Documentation
- Complete README with installation and usage instructions
- Contributing guidelines for developers
- Example configuration file
- Architecture overview and design principles

## [Unreleased]

### Planned for Phase 2
- Reddit profile connector
- LinkedIn profile connector  
- Expanded health and political inference capabilities
- Automated remediation suggestions
- Breach monitoring integration
- Plugin ecosystem foundation

### Planned for Phase 3
- Real-time monitoring dashboard
- Browser extension for live analysis
- Advanced correlation detection
- Custom inference plugins
- Enterprise features
