#!/usr/bin/env python3
"""
Test OpenAI API Status and Rate Limits
Helps diagnose API connectivity and rate limiting issues
"""

import sys
import json
import time
import os
from datetime import datetime, timedelta

try:
    from openai import OpenAI
    from openai import RateLimitError, APIError, APITimeoutError
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    print("❌ OpenAI library not available. Install with: pip install openai")

def load_api_key():
    """Load API key from environment or config file"""
    # Try environment variable first
    api_key = os.environ.get('OPENAI_API_KEY')
    if api_key:
        return api_key
    
    # Try config file
    config_path = os.path.join(os.path.dirname(__file__), 'ai_config.json')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        api_key = config.get('openai_api_key')
        if api_key and api_key.startswith('sk-'):
            return api_key
    except Exception as e:
        print(f"⚠️  Could not load config file: {e}")
    
    return None

def test_api_connection(api_key):
    """Test basic API connectivity"""
    print("🔍 Testing API connectivity...")
    
    try:
        client = OpenAI(api_key=api_key, max_retries=0)
        
        # Simple test call
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=5
        )
        
        print("✅ API connection successful!")
        print(f"   Model: {response.model}")
        print(f"   Response: {response.choices[0].message.content}")
        return True
        
    except RateLimitError as e:
        retry_after = getattr(e, 'retry_after', None)
        print("❌ Rate limit exceeded!")
        if retry_after:
            reset_time = datetime.now() + timedelta(seconds=int(retry_after))
            print(f"   Retry after: {retry_after} seconds")
            print(f"   Reset time: {reset_time.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print("   No retry-after header provided")
        return False
        
    except APIError as e:
        print(f"❌ API Error: {e}")
        return False
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def test_rate_limits(api_key):
    """Test rate limiting behavior"""
    print("\n🚀 Testing rate limits...")
    
    client = OpenAI(api_key=api_key, max_retries=0)
    
    # Make multiple rapid requests to test rate limiting
    for i in range(5):
        try:
            print(f"   Request {i+1}/5...")
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": f"Test message {i+1}"}],
                max_tokens=5
            )
            print(f"   ✅ Success: {response.choices[0].message.content}")
            
            # Small delay between requests
            if i < 4:
                time.sleep(0.5)
                
        except RateLimitError as e:
            retry_after = getattr(e, 'retry_after', None)
            print(f"   ❌ Rate limited on request {i+1}")
            if retry_after:
                print(f"      Retry after: {retry_after} seconds")
            return False
            
        except Exception as e:
            print(f"   ❌ Error on request {i+1}: {e}")
            return False
    
    print("✅ Rate limit test completed successfully!")
    return True

def check_usage_limits(api_key):
    """Check current usage and limits"""
    print("\n📊 Checking usage limits...")
    
    try:
        client = OpenAI(api_key=api_key, max_retries=0)
        
        # Note: OpenAI doesn't provide usage info via API in the same way
        # This is a placeholder for future implementation
        print("ℹ️  Usage information not available via API")
        print("   Check your usage at: https://platform.openai.com/usage")
        print("   Check your limits at: https://platform.openai.com/account/limits")
        
    except Exception as e:
        print(f"❌ Could not check usage: {e}")

def main():
    """Main function"""
    print("🔧 OpenAI API Status Checker")
    print("=" * 40)
    
    # Check if OpenAI is available
    if not AI_AVAILABLE:
        print("❌ OpenAI library not available")
        print("   Install with: pip install openai")
        sys.exit(1)
    
    # Load API key
    api_key = load_api_key()
    if not api_key:
        print("❌ No API key found!")
        print("   Set OPENAI_API_KEY environment variable")
        print("   Or add to scripts/ai_config.json")
        sys.exit(1)
    
    print(f"✅ API key loaded: {api_key[:10]}...")
    
    # Test connection
    if not test_api_connection(api_key):
        print("\n💡 Suggestions:")
        print("   1. Check your API key is correct")
        print("   2. Verify your OpenAI account has credits")
        print("   3. Check if you're hitting rate limits")
        print("   4. Try again in a few minutes")
        sys.exit(1)
    
    # Test rate limits
    test_rate_limits(api_key)
    
    # Check usage
    check_usage_limits(api_key)
    
    print("\n✅ API status check completed!")
    print("\n💡 Tips for avoiding rate limits:")
    print("   1. Add delays between requests (1-2 seconds)")
    print("   2. Use exponential backoff for retries")
    print("   3. Monitor your usage at platform.openai.com")
    print("   4. Consider upgrading your plan if needed")

if __name__ == "__main__":
    main() 