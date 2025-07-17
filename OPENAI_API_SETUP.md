# OpenAI API Key Configuration Guide

## Overview
This guide explains how to properly configure the OpenAI API key for the legal document extraction system.

## Method 1: Environment Variable (Recommended)

### Step 1: Get Your OpenAI API Key
1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Sign in to your account
3. Navigate to "API Keys" in the left sidebar
4. Click "Create new secret key"
5. Give it a name (e.g., "Legal Document Extractor")
6. Copy the generated API key (starts with `sk-`)

### Step 2: Set Environment Variable

#### Windows (PowerShell):
```powershell
# Set for current session
$env:OPENAI_API_KEY="sk-your-actual-api-key-here"

# Set permanently (requires admin)
[Environment]::SetEnvironmentVariable("OPENAI_API_KEY", "sk-your-actual-api-key-here", "User")
```

#### Windows (Command Prompt):
```cmd
# Set for current session
set OPENAI_API_KEY=sk-your-actual-api-key-here

# Set permanently
setx OPENAI_API_KEY "sk-your-actual-api-key-here"
```

#### Linux/Mac:
```bash
# Set for current session
export OPENAI_API_KEY="sk-your-actual-api-key-here"

# Set permanently (add to ~/.bashrc or ~/.zshrc)
echo 'export OPENAI_API_KEY="sk-your-actual-api-key-here"' >> ~/.bashrc
source ~/.bashrc
```

## Method 2: Configuration File

### Step 1: Edit the Config File
Open `scripts/ai_config.json` and replace the placeholder:

```json
{
    "openai_api_key": "sk-your-actual-api-key-here",
    "huggingface_api_key": "",
    "enable_llm_extraction": true,
    "enable_spacy_extraction": true,
    "confidence_threshold": 0.7,
    "max_results_per_field": 5,
    "timeout_seconds": 30
}
```

**⚠️ Security Warning**: Never commit your API key to version control!

## Method 3: .env File (Alternative)

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=sk-your-actual-api-key-here
```

Then install python-dotenv:
```bash
pip install python-dotenv
```

## Testing Your Configuration

### Test 1: Check if API Key is Loaded
```bash
python scripts/metadata_extractor.py test_file.pdf petitioner
```

If configured correctly, you should see:
- "AI extractor initialized for OpenAI-only extraction"
- No "401 Unauthorized" errors

### Test 2: Test with a Sample PDF
```bash
python scripts/metadata_extractor.py "path/to/your/test.pdf" petitioner
```

## Troubleshooting

### Common Issues:

1. **401 Unauthorized Error**
   - Check if your API key is correct
   - Ensure you have sufficient credits in your OpenAI account
   - Verify the API key starts with `sk-`

2. **API Key Not Found**
   - Check if environment variable is set: `echo $OPENAI_API_KEY`
   - Verify the config file path and format
   - Restart your terminal/IDE after setting environment variables

3. **Rate Limiting**
   - Check your OpenAI usage limits
   - Consider upgrading your plan if needed

### Debug Commands:

```bash
# Check environment variable
echo $OPENAI_API_KEY

# Test OpenAI API directly
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"model":"gpt-3.5-turbo","messages":[{"role":"user","content":"Hello"}]}' \
     https://api.openai.com/v1/chat/completions
```

## Security Best Practices

1. **Never hardcode API keys** in your source code
2. **Use environment variables** for production deployments
3. **Rotate API keys** regularly
4. **Monitor usage** to avoid unexpected charges
5. **Use API key restrictions** in OpenAI dashboard if available

## Cost Considerations

- GPT-3.5-turbo: ~$0.002 per 1K tokens
- Typical legal document extraction: 2-5K tokens per document
- Estimated cost: $0.004-$0.01 per document

## Support

If you continue having issues:
1. Check OpenAI's [API documentation](https://platform.openai.com/docs/api-reference)
2. Verify your account has sufficient credits
3. Check the server logs for detailed error messages 