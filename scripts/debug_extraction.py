#!/usr/bin/env python3
"""
Debug script to diagnose metadata extraction issues.
"""

import os
import sys
import json
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_ai_configuration():
    """Check AI configuration and API key setup"""
    print("=" * 60)
    print("AI CONFIGURATION DIAGNOSTICS")
    print("=" * 60)
    
    # Check environment variable
    env_key = os.getenv('OPENAI_API_KEY')
    print(f"Environment variable OPENAI_API_KEY: {'SET' if env_key else 'NOT SET'}")
    if env_key:
        print(f"  Key starts with: {env_key[:10]}...")
    
    # Check config file
    config_path = os.path.join(os.path.dirname(__file__), 'ai_config.json')
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                config_key = config.get('openai_api_key', '')
                print(f"Config file API key: {'SET' if config_key and config_key != 'YOUR_OPENAI_API_KEY_HERE' else 'NOT SET/PLACEHOLDER'}")
                if config_key and config_key != 'YOUR_OPENAI_API_KEY_HERE':
                    print(f"  Key starts with: {config_key[:10]}...")
        except Exception as e:
            print(f"Error reading config file: {e}")
    else:
        print("Config file: NOT FOUND")
    
    # Test AI extractor initialization
    try:
        from ai_extractor import AIExtractor
        extractor = AIExtractor()
        print(f"AI Extractor initialization: {'SUCCESS' if extractor.openai_api_key else 'FAILED - NO API KEY'}")
        if extractor.openai_api_key:
            print(f"  API key available: {extractor.openai_api_key[:10]}...")
        else:
            print("  No API key available - extraction will fail")
    except Exception as e:
        print(f"AI Extractor initialization: FAILED - {e}")

def test_text_extraction(file_path: str):
    """Test text extraction from PDF"""
    print("\n" + "=" * 60)
    print("TEXT EXTRACTION TEST")
    print("=" * 60)
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return None
    
    try:
        from metadata_extractor import extract_text_from_pdf, extract_text_from_pdf_with_pdfplumber
        
        # Try PyMuPDF first
        text = extract_text_from_pdf(file_path)
        print(f"PyMuPDF extraction: {'SUCCESS' if text.strip() else 'FAILED'}")
        print(f"  Text length: {len(text)} characters")
        print(f"  First 200 chars: {text[:200]}...")
        
        if not text.strip():
            # Try pdfplumber
            text = extract_text_from_pdf_with_pdfplumber(file_path)
            print(f"PDFPlumber extraction: {'SUCCESS' if text.strip() else 'FAILED'}")
            print(f"  Text length: {len(text)} characters")
            print(f"  First 200 chars: {text[:200]}...")
        
        return text
    except Exception as e:
        print(f"Text extraction failed: {e}")
        return None

def test_metadata_extraction(file_path: str):
    """Test metadata extraction"""
    print("\n" + "=" * 60)
    print("METADATA EXTRACTION TEST")
    print("=" * 60)
    
    try:
        from metadata_extractor import extract_all_metadata
        
        metadata = extract_all_metadata(file_path)
        
        print("Extraction Results:")
        for field, value in metadata.items():
            status = "✓" if value and value != "Not found" else "✗"
            print(f"  {status} {field}: {value}")
        
        return metadata
    except Exception as e:
        print(f"Metadata extraction failed: {e}")
        return None

def test_simple_extraction(file_path: str):
    """Test simple field extraction"""
    print("\n" + "=" * 60)
    print("SIMPLE FIELD EXTRACTION TEST")
    print("=" * 60)
    
    try:
        from metadata_extractor import extract_text_from_pdf, extract_metadata
        
        # Extract text
        text = extract_text_from_pdf(file_path)
        if not text.strip():
            from metadata_extractor import extract_text_from_pdf_with_pdfplumber
            text = extract_text_from_pdf_with_pdfplumber(file_path)
        
        if not text.strip():
            print("No text extracted from PDF")
            return
        
        print(f"Extracted text length: {len(text)} characters")
        print(f"Sample text: {text[:500]}...")
        
        # Test individual fields
        test_fields = ['court_name', 'judge', 'citation_year', 'advocates']
        
        for field in test_fields:
            try:
                result = extract_metadata(text, field)
                status = "✓" if result and result != "Not found" else "✗"
                print(f"  {status} {result}")
            except Exception as e:
                print(f"  ✗ {field}: ERROR - {e}")
                
    except Exception as e:
        print(f"Simple extraction test failed: {e}")

def main():
    """Main debug function"""
    if len(sys.argv) < 2:
        print("Usage: python debug_extraction.py <pdf_file_path>")
        print("This will diagnose extraction issues step by step.")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    print("METADATA EXTRACTION DEBUG TOOL")
    print("=" * 60)
    print(f"Testing file: {file_path}")
    
    # Step 1: Check AI configuration
    check_ai_configuration()
    
    # Step 2: Test text extraction
    text = test_text_extraction(file_path)
    
    # Step 3: Test metadata extraction
    metadata = test_metadata_extraction(file_path)
    
    # Step 4: Test simple extraction
    test_simple_extraction(file_path)
    
    print("\n" + "=" * 60)
    print("RECOMMENDATIONS")
    print("=" * 60)
    
    if not os.getenv('OPENAI_API_KEY'):
        print("1. Set your OpenAI API key as environment variable:")
        print("   set OPENAI_API_KEY=your_api_key_here")
        print("   OR")
        print("   $env:OPENAI_API_KEY = 'your_api_key_here'")
    
    config_path = os.path.join(os.path.dirname(__file__), 'ai_config.json')
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)
            if config.get('openai_api_key') == 'YOUR_OPENAI_API_KEY_HERE':
                print("2. Update ai_config.json with your actual OpenAI API key")
    
    print("3. After setting the API key, run the extraction again")
    print("4. If text extraction fails, the PDF might be image-based and need OCR")

if __name__ == "__main__":
    main() 