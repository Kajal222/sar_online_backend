#!/usr/bin/env python3
"""
Test script for Enhanced PDF to DOCX API
========================================

This script tests the enhanced PDF to DOCX conversion API endpoint.
"""

import requests
import os
import time
from pathlib import Path

def test_health_endpoint():
    """Test the health endpoint."""
    print("Testing health endpoint...")
    
    try:
        response = requests.get("http://localhost:3000/health")
        if response.status_code == 200:
            print("✅ Health endpoint working")
            data = response.json()
            print(f"   Status: {data.get('status')}")
            print(f"   Endpoints: {data.get('endpoints')}")
            return True
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health endpoint error: {str(e)}")
        return False

def test_docx_generation(pdf_path):
    """Test the DOCX generation endpoint."""
    print(f"\nTesting DOCX generation with: {os.path.basename(pdf_path)}")
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF file not found: {pdf_path}")
        return False
    
    try:
        # Prepare the file upload
        with open(pdf_path, 'rb') as pdf_file:
            files = {'pdf': (os.path.basename(pdf_path), pdf_file, 'application/pdf')}
            
            print("   Uploading PDF...")
            start_time = time.time()
            
            response = requests.post(
                "http://localhost:3000/generate-docx",
                files=files,
                timeout=300  # 5 minutes timeout
            )
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            if response.status_code == 200:
                # Save the DOCX file
                output_filename = f"test_output_{os.path.basename(pdf_path).replace('.pdf', '')}.docx"
                with open(output_filename, 'wb') as docx_file:
                    docx_file.write(response.content)
                
                file_size = len(response.content)
                print(f"✅ DOCX generation successful!")
                print(f"   Processing time: {processing_time:.2f} seconds")
                print(f"   Output file: {output_filename}")
                print(f"   File size: {file_size:,} bytes")
                
                # Check if file has content
                if file_size > 1000:  # More than 1KB
                    print(f"   ✅ Output file has substantial content")
                else:
                    print(f"   ⚠️  Output file seems small, may need investigation")
                
                return True
            else:
                print(f"❌ DOCX generation failed: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data.get('error', 'Unknown error')}")
                    print(f"   Message: {error_data.get('message', 'No message')}")
                except:
                    print(f"   Response: {response.text[:200]}...")
                return False
                
    except requests.exceptions.Timeout:
        print("❌ Request timed out (5 minutes)")
        return False
    except Exception as e:
        print(f"❌ DOCX generation error: {str(e)}")
        return False

def test_error_handling():
    """Test error handling with invalid files."""
    print("\nTesting error handling...")
    
    # Test with non-PDF file
    print("   Testing with non-PDF file...")
    try:
        files = {'pdf': ('test.txt', b'This is not a PDF', 'text/plain')}
        response = requests.post("http://localhost:3000/generate-docx", files=files)
        
        if response.status_code == 400:
            print("   ✅ Properly rejected non-PDF file")
        else:
            print(f"   ❌ Unexpected response for non-PDF: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error testing non-PDF file: {str(e)}")
    
    # Test with no file
    print("   Testing with no file...")
    try:
        response = requests.post("http://localhost:3000/generate-docx")
        
        if response.status_code == 400:
            print("   ✅ Properly handled missing file")
        else:
            print(f"   ❌ Unexpected response for missing file: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error testing missing file: {str(e)}")

def main():
    """Main test function."""
    print("Enhanced PDF to DOCX API Test Suite")
    print("=" * 50)
    
    # Test health endpoint
    if not test_health_endpoint():
        print("❌ Server not available, exiting...")
        return
    
    # Test with sample PDFs
    test_files_dir = Path("testsprite_tests/test_files")
    if test_files_dir.exists():
        pdf_files = list(test_files_dir.glob("*.pdf"))
        
        if pdf_files:
            print(f"\nFound {len(pdf_files)} PDF files for testing")
            
            # Test with first 2 PDF files
            for i, pdf_file in enumerate(pdf_files[:2]):
                success = test_docx_generation(str(pdf_file))
                if not success:
                    print(f"❌ Failed to process {pdf_file.name}")
                    break
                
                # Add delay between tests
                if i < len(pdf_files[:2]) - 1:
                    print("   Waiting 2 seconds before next test...")
                    time.sleep(2)
        else:
            print("❌ No PDF files found in test directory")
    else:
        print("❌ Test files directory not found")
    
    # Test error handling
    test_error_handling()
    
    print("\n" + "=" * 50)
    print("Test suite completed!")

if __name__ == "__main__":
    main() 