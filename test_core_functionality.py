#!/usr/bin/env python3
"""
Simple Core Functionality Test
Tests the basic API functionality without triggering rate limits
"""

import requests
import os
import time

BASE_URL = "http://localhost:3000"

def test_health_check():
    """Test health check endpoint"""
    print("🏥 Testing Health Check...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health Check: {data.get('status')} - Version {data.get('version')}")
            return True
        else:
            print(f"❌ Health Check Failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health Check Error: {str(e)}")
        return False

def test_single_metadata_extraction():
    """Test single metadata extraction"""
    print("\n🔍 Testing Single Metadata Extraction...")
    
    pdf_file = "testsprite_tests/test_files/Ravinder Kaur - UK.pdf"
    if not os.path.exists(pdf_file):
        print(f"⚠️ Test file not found: {pdf_file}")
        return False
    
    try:
        with open(pdf_file, 'rb') as f:
            files = {'pdf': (os.path.basename(pdf_file), f, 'application/pdf')}
            response = requests.post(f"{BASE_URL}/extract-metadata", files=files, timeout=120)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Metadata Extraction Successful!")
            print(f"  File Size: {data.get('fileInfo', {}).get('fileSizeMB', 'N/A')} MB")
            print(f"  Appellant: {data.get('metadata', {}).get('appellant', 'N/A')}")
            print(f"  Respondent: {data.get('metadata', {}).get('respondent', 'N/A')}")
            print(f"  Judge: {data.get('metadata', {}).get('judgeName', 'N/A')}")
            return True
        else:
            print(f"❌ Metadata Extraction Failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Metadata Extraction Error: {str(e)}")
        return False

def test_single_docx_conversion():
    """Test single DOCX conversion"""
    print("\n📄 Testing Single DOCX Conversion...")
    
    pdf_file = "testsprite_tests/test_files/anita_yuvraj_test.pdf"
    if not os.path.exists(pdf_file):
        print(f"⚠️ Test file not found: {pdf_file}")
        return False
    
    try:
        with open(pdf_file, 'rb') as f:
            files = {'pdf': (os.path.basename(pdf_file), f, 'application/pdf')}
            response = requests.post(f"{BASE_URL}/generate-docx", files=files, timeout=120)
        
        if response.status_code == 200:
            output_file = f"test_output_{os.path.basename(pdf_file).replace('.pdf', '.docx')}"
            with open(output_file, 'wb') as f:
                f.write(response.content)
            print(f"✅ DOCX Conversion Successful! Saved as: {output_file}")
            return True
        else:
            print(f"❌ DOCX Conversion Failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ DOCX Conversion Error: {str(e)}")
        return False

def main():
    """Run core functionality tests"""
    print("🚀 Testing Core Functionality")
    print("=" * 40)
    
    # Wait a bit to avoid rate limiting
    print("⏳ Waiting 30 seconds to avoid rate limiting...")
    time.sleep(30)
    
    tests_passed = 0
    total_tests = 0
    
    # Test 1: Health Check
    total_tests += 1
    if test_health_check():
        tests_passed += 1
    
    # Test 2: Metadata Extraction
    total_tests += 1
    if test_single_metadata_extraction():
        tests_passed += 1
    
    # Test 3: DOCX Conversion
    total_tests += 1
    if test_single_docx_conversion():
        tests_passed += 1
    
    # Summary
    print("\n" + "=" * 40)
    print(f"📊 Core Functionality Results:")
    print(f"   Tests Passed: {tests_passed}/{total_tests}")
    print(f"   Success Rate: {(tests_passed/total_tests)*100:.1f}%" if total_tests > 0 else "N/A")
    
    if tests_passed == total_tests:
        print("🎉 All core functionality tests passed!")
    else:
        print("⚠️ Some tests failed. Check the output above.")

if __name__ == "__main__":
    main() 