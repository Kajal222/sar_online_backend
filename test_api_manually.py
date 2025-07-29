#!/usr/bin/env python3
"""
Manual API Testing Script for Legal Document Extractor
Tests the API endpoints with actual PDF files from the uploads directory
"""

import requests
import json
import os
import time
from pathlib import Path

# API Configuration
BASE_URL = "http://localhost:3000"
UPLOADS_DIR = Path("uploads")
TEST_FILES_DIR = Path("testsprite_tests/test_files")

def test_extract_metadata(pdf_file):
    """Test the /extract-metadata endpoint"""
    print(f"\n🔍 Testing metadata extraction with: {pdf_file}")
    
    url = f"{BASE_URL}/extract-metadata"
    
    try:
        with open(pdf_file, 'rb') as f:
            files = {'pdf': (os.path.basename(pdf_file), f, 'application/pdf')}
            response = requests.post(url, files=files, timeout=60)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Success!")
            print(f"Extracted Data:")
            print(f"  - Appellant: {data.get('metadata', {}).get('appellant', 'N/A')}")
            print(f"  - Respondent: {data.get('metadata', {}).get('respondent', 'N/A')}")
            print(f"  - Judge: {data.get('metadata', {}).get('judgeName', 'N/A')}")
            print(f"  - Case Result: {data.get('metadata', {}).get('caseResult', 'N/A')}")
            print(f"  - Processing Method: {data.get('processingInfo', {}).get('extractionMethod', 'N/A')}")
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return False

def test_generate_docx(pdf_file):
    """Test the /generate-docx endpoint"""
    print(f"\n📄 Testing DOCX conversion with: {pdf_file}")
    
    url = f"{BASE_URL}/generate-docx"
    
    try:
        with open(pdf_file, 'rb') as f:
            files = {'pdf': (os.path.basename(pdf_file), f, 'application/pdf')}
            response = requests.post(url, files=files, timeout=60)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            # Save the DOCX file
            output_file = f"output_{os.path.basename(pdf_file).replace('.pdf', '.docx')}"
            with open(output_file, 'wb') as f:
                f.write(response.content)
            print(f"✅ Success! DOCX saved as: {output_file}")
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return False

def test_error_handling():
    """Test error handling with invalid inputs"""
    print(f"\n🚫 Testing error handling")
    
    url = f"{BASE_URL}/extract-metadata"
    
    # Test 1: No file uploaded
    print("Test 1: No file uploaded")
    response = requests.post(url, timeout=10)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 400:
        print("✅ Correctly rejected missing file")
    else:
        print("❌ Should have rejected missing file")
    
    # Test 2: Invalid file type
    print("\nTest 2: Invalid file type")
    files = {'pdf': ('test.txt', b'This is not a PDF', 'text/plain')}
    response = requests.post(url, files=files, timeout=10)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 400:
        print("✅ Correctly rejected invalid file type")
    else:
        print("❌ Should have rejected invalid file type")

def main():
    """Run all tests"""
    print("🚀 Starting Manual API Tests")
    print("=" * 50)
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/extract-metadata", timeout=5)
        print("✅ Server is running")
    except:
        print("❌ Server is not running. Please start the server first.")
        return
    
    # Test with different PDF files
    test_files = [
        "testsprite_tests/test_files/anita_yuvraj_test.pdf",
        "testsprite_tests/test_files/Tej Karan - Jodhpur.pdf",
        "testsprite_tests/test_files/Ravinder Kaur - UK.pdf"
    ]
    
    successful_tests = 0
    total_tests = 0
    
    # Test metadata extraction
    for pdf_file in test_files:
        if os.path.exists(pdf_file):
            total_tests += 1
            if test_extract_metadata(pdf_file):
                successful_tests += 1
        else:
            print(f"⚠️ File not found: {pdf_file}")
    
    # Test DOCX conversion with first available file
    if test_files and os.path.exists(test_files[0]):
        total_tests += 1
        if test_generate_docx(test_files[0]):
            successful_tests += 1
    
    # Test error handling
    test_error_handling()
    
    # Summary
    print("\n" + "=" * 50)
    print(f"📊 Test Summary:")
    print(f"   Successful: {successful_tests}/{total_tests}")
    print(f"   Success Rate: {(successful_tests/total_tests)*100:.1f}%" if total_tests > 0 else "N/A")

if __name__ == "__main__":
    main() 