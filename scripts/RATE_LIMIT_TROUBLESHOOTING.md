# OpenAI API Rate Limiting Troubleshooting Guide

## Understanding Rate Limits

OpenAI API has different rate limits depending on your plan:

### Free Tier (Trial)
- **Requests per minute**: 3
- **Requests per day**: 200
- **Tokens per minute**: 150,000
- **Tokens per day**: 40,000

### Pay-as-you-go
- **Requests per minute**: 3,500
- **Requests per day**: 90,000
- **Tokens per minute**: 90,000
- **Tokens per day**: 2,000,000

### Team/Enterprise
- Higher limits based on your plan

## Common Rate Limit Errors

### HTTP 429 - Too Many Requests
```
HTTP/1.1 429 Too Many Requests
Retry-After: 60
```

This means you've exceeded the rate limit. The `Retry-After` header tells you how many seconds to wait.

### Error Messages
- `Rate limit exceeded for requests`
- `Rate limit exceeded for tokens`
- `You exceeded your current quota`

## Immediate Solutions

### 1. Check Your Current Status
```bash
python scripts/test_api_status.py
```

### 2. Wait for Rate Limit Reset
- **Per-minute limits**: Reset every minute
- **Per-day limits**: Reset at midnight UTC
- **Quota limits**: Reset based on your billing cycle

### 3. Use Regex-Only Mode
```bash
python scripts/legal_document_extractor_simple.py --regex-only your_file.txt
```

### 4. Check Your Usage
Visit: https://platform.openai.com/usage

## Prevention Strategies

### 1. Add Delays Between Requests
The improved extractor now includes:
- Minimum 1-second delay between calls
- 2-second delay for batch processing
- Exponential backoff for retries

### 2. Use Batch Processing with Delays
```python
extractor = AILegalDocumentExtractor(max_retries=3)
results = extractor.extract_batch(texts, delay_between_requests=3.0)
```

### 3. Monitor Rate Limits
```python
status = extractor.check_api_status()
if status.get('status') == 'rate_limited':
    print(f"Wait {status.get('retry_after')} seconds")
```

### 4. Implement Circuit Breaker Pattern
The extractor now tracks rate limit reset times and waits automatically.

## Configuration Options

### Update `scripts/ai_config.json`
```json
{
  "openai_api_key": "your_api_key_here",
  "max_retries": 3,
  "min_delay_between_calls": 1.0,
  "batch_delay": 2.0,
  "rate_limit_caps": {
    "rate_limit": 120,
    "api_error": 60,
    "timeout": 30,
    "general": 15
  }
}
```

### Environment Variables
```bash
export OPENAI_API_KEY="your_api_key_here"
```

## Advanced Solutions

### 1. Upgrade Your Plan
- Visit: https://platform.openai.com/account/billing
- Consider upgrading to pay-as-you-go or team plan

### 2. Use Multiple API Keys
Rotate between different API keys to distribute load.

### 3. Implement Caching
Cache results to avoid repeated API calls for the same content.

### 4. Use Different Models
- `gpt-3.5-turbo`: Faster, cheaper, lower limits
- `gpt-4`: Slower, more expensive, higher limits

## Debugging Commands

### Test API Status
```bash
python scripts/test_api_status.py
```

### Check Rate Limits
```bash
python scripts/legal_document_extractor_simple.py --check-api
```

### Force Regex Mode
```bash
python scripts/legal_document_extractor_simple.py --no-ai your_file.txt
```

### Test with Sample
```bash
python scripts/legal_document_extractor_simple.py --text "sample legal text"
```

## Error Recovery

### Automatic Recovery
The improved extractor includes:
- ✅ Automatic retry with exponential backoff
- ✅ Rate limit reset time tracking
- ✅ Graceful fallback to regex extraction
- ✅ Minimum delay enforcement

### Manual Recovery
1. Wait for rate limit reset
2. Check your usage at platform.openai.com
3. Consider upgrading your plan
4. Use regex-only mode temporarily

## Best Practices

### 1. Always Handle Rate Limits
```python
try:
    result = extractor.extract_from_text(text)
except RateLimitError as e:
    # Handle gracefully
    result = extractor.extract_from_text(text, use_ai=False)
```

### 2. Use Batch Processing
```python
# Process multiple documents with delays
results = extractor.extract_batch(documents, delay_between_requests=2.0)
```

### 3. Monitor Usage
- Set up usage alerts
- Check usage regularly
- Plan for peak usage periods

### 4. Implement Fallbacks
- Always have regex extraction as backup
- Cache successful results
- Use multiple extraction methods

## Emergency Procedures

### If You're Completely Rate Limited

1. **Immediate**: Use regex-only mode
   ```bash
   python scripts/legal_document_extractor_simple.py --regex-only your_file.txt
   ```

2. **Short-term**: Wait for reset and reduce frequency
   ```python
   # Increase delays
   extractor.min_delay_between_calls = 5.0
   ```

3. **Long-term**: Upgrade plan or implement caching

### If You Need Immediate Processing

1. Use regex extraction (less accurate but immediate)
2. Process in smaller batches
3. Use multiple API keys if available
4. Consider alternative AI services

## Support Resources

- **OpenAI Status**: https://status.openai.com/
- **API Documentation**: https://platform.openai.com/docs/
- **Usage Dashboard**: https://platform.openai.com/usage
- **Billing**: https://platform.openai.com/account/billing
- **Rate Limits**: https://platform.openai.com/docs/guides/rate-limits

## Quick Reference

| Issue | Solution |
|-------|----------|
| HTTP 429 | Wait for retry-after seconds |
| Quota exceeded | Upgrade plan or wait for reset |
| Too many requests | Add delays between calls |
| Need immediate processing | Use regex-only mode |
| Batch processing | Use extract_batch with delays |

Remember: The improved extractor now handles most rate limiting automatically. If you're still having issues, check your usage and consider upgrading your OpenAI plan. 