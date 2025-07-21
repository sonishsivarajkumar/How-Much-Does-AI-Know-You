# API Documentation

## CLI Commands

### `ai-audit scan`

Run a complete privacy audit scan across multiple platforms.

```bash
ai-audit scan [OPTIONS]
```

**Options:**
- `--platforms, -p TEXT`: Comma-separated list of platforms (default: "github,twitter")
- `--username, -u TEXT`: Username to analyze (if different from config)
- `--output, -o PATH`: Output file for results
- `--format, -f [json|text]`: Output format (default: "text")

**Examples:**
```bash
# Scan GitHub and Twitter
ai-audit scan --platforms github,twitter --username myusername

# Save results to file
ai-audit scan --output audit-report.json --format json

# GitHub only
ai-audit scan --platforms github
```

### `ai-audit analyze-github`

Analyze a specific GitHub profile.

```bash
ai-audit analyze-github --username USERNAME
```

### `ai-audit serve`

Start the web dashboard.

```bash
ai-audit serve [OPTIONS]
```

**Options:**
- `--port, -p INTEGER`: Port to run server on (default: 8000)
- `--host, -h TEXT`: Host to bind to (default: "127.0.0.1")

### `ai-audit status`

Show configuration and system status.

```bash
ai-audit status
```

### `ai-audit report`

Generate a privacy report from stored data.

```bash
ai-audit report [OPTIONS]
```

**Options:**
- `--format, -f [json|text|pdf]`: Report format (default: "text")
- `--output, -o PATH`: Output file

## Configuration

All configuration is done via environment variables or a `.env` file.

### Required Variables

**AI Provider APIs (at least one):**
- `OPENAI_API_KEY`: OpenAI API key
- `ANTHROPIC_API_KEY`: Anthropic API key

**Platform APIs:**
- `GITHUB_TOKEN`: GitHub Personal Access Token
- `TWITTER_BEARER_TOKEN`: Twitter API Bearer Token

### Optional Variables

**Storage Settings:**
- `AI_AUDIT_DATA_DIR`: Directory for local data storage (default: ~/.ai-audit)
- `AI_AUDIT_CACHE_TTL`: Cache time-to-live in seconds (default: 3600)

**Privacy Settings:**
- `ANONYMIZE_DATA`: Anonymize sensitive data (default: true)
- `RETAIN_RAW_DATA`: Keep raw API responses (default: false)

**AI Settings:**
- `DEFAULT_LLM_PROVIDER`: Default AI provider ("openai" or "anthropic")
- `USE_LOCAL_MODELS`: Use local models instead of APIs (default: false)
- `MAX_INFERENCE_REQUESTS`: Maximum inference requests per scan (default: 10)

**Web Server:**
- `WEB_HOST`: Web server host (default: "127.0.0.1")
- `WEB_PORT`: Web server port (default: 8000)
- `DEBUG_MODE`: Enable debug mode (default: false)

## Web API

When running `ai-audit serve`, the following API endpoints are available:

### GET `/api/dashboard-data`

Returns dashboard summary data including:
- Total inferences count
- High-confidence inferences
- Latest privacy risk score
- Recent inferences list
- Recommendations

### GET `/api/inferences`

Returns recent inferences.

**Query Parameters:**
- `limit` (int): Maximum number of results (default: 50)
- `min_confidence` (float): Minimum confidence threshold (default: 0.0)

### GET `/api/audit-history`

Returns audit report history.

**Query Parameters:**
- `limit` (int): Maximum number of reports (default: 10)

## Data Models

### ProfileData

Represents collected profile data from a platform.

```python
{
    "platform": "github",
    "username": "user123",
    "user_id": "12345",
    "profile_text": "Profile description...",
    "metadata": {...},
    "collected_at": "2025-07-21T10:00:00Z",
    "raw_data": {...}  # Optional
}
```

### Inference

Represents an AI inference about the user.

```python
{
    "type": "location",
    "value": "San Francisco, CA", 
    "confidence": 0.85,
    "confidence_level": "high",
    "reasoning": "Location explicitly mentioned...",
    "source_platforms": ["github", "twitter"],
    "model_used": "openai-gpt-4",
    "created_at": "2025-07-21T10:00:00Z"
}
```

### Inference Types

Available inference types:
- `programming_skills`: Technical skills and languages
- `location`: Geographic location
- `age_range`: Estimated age range
- `interests`: Hobbies and interests
- `sentiment`: Communication style and sentiment
- `political_leaning`: Political views (if evident)
- `work_schedule`: Activity patterns and timezone
- `education_level`: Educational background
- `health_signals`: Health-related mentions
- `purchasing_power`: Economic indicators

### AuditReport

Complete audit report structure.

```python
{
    "user_id": "user123",
    "platforms_analyzed": ["github", "twitter"],
    "profile_data": [...],  # ProfileData objects
    "inferences": [...],    # Inference objects
    "privacy_risk": {...},  # PrivacyRisk object
    "recommendations": [...], # Recommendation objects
    "generated_at": "2025-07-21T10:00:00Z",
    "report_version": "1.0"
}
```

## Error Handling

The tool handles various error conditions gracefully:

### API Errors
- **Rate limiting**: Automatic retry with exponential backoff
- **Authentication**: Clear error messages for invalid tokens
- **Network issues**: Timeout and retry logic

### Data Errors
- **Missing profiles**: Skips unavailable profiles with warnings
- **Invalid data**: Validates and sanitizes input data
- **Storage errors**: Fallback to memory storage if disk fails

### Privacy Safeguards
- **Permission errors**: Only analyzes accessible public data
- **Rate limiting**: Respects platform API limits
- **Data validation**: Prevents injection attacks

## Extending the Tool

### Adding New Platforms

1. Create a new connector in `src/ai_audit/connectors/`
2. Inherit from `BaseConnector`
3. Implement required methods:
   - `get_platform()`
   - `get_profile_data()`
   - `is_configured()`

### Adding New Inference Types

1. Add new type to `InferenceType` enum
2. Update inference engine prompts
3. Add analysis logic to `PrivacyAnalyzer`

### Custom AI Providers

1. Create new engine in `src/ai_audit/inference/`
2. Inherit from `BaseInferenceEngine`
3. Implement `make_inference()` method
4. Register in `InferenceOrchestrator`

## Security Considerations

### API Key Management
- Store keys in environment variables only
- Never commit keys to version control
- Use least-privilege API permissions
- Rotate keys regularly

### Data Privacy
- All data stored locally by default
- Optional anonymization of sensitive fields
- Configurable data retention policies
- No cloud dependencies unless explicitly configured

### Network Security
- HTTPS for all API requests
- Certificate validation enabled
- Request timeout limits
- Rate limiting compliance
