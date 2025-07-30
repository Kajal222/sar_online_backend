#!/usr/bin/env python3
"""
Test script to verify the API is working with the improved converter.
"""

import requests
import os
import time

def test_api():
    """Test the API with the improved converter."""
    
    # API endpoint
    url = "http://localhost:3000/generate-docx"
    
    # Test file
    pdf_file = "testsprite_tests/test_files/anita_yuvraj_test.pdf"
    
    if not os.path.exists(pdf_file):
        print(f"❌ Test file not found: {pdf_file}")
        return False
    
    print(f"🧪 Testing API with file: {pdf_file}")
    print(f"📡 Sending request to: {url}")
    
    try:
        # Prepare the file for upload
        with open(pdf_file, 'rb') as f:
            files = {'pdf': (os.path.basename(pdf_file), f, 'application/pdf')}
            
            print("⏳ Sending request...")
            start_time = time.time()
            
            # Send the request
            response = requests.post(url, files=files, timeout=300)
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            print(f"⏱️  Processing time: {processing_time:.2f} seconds")
            
            if response.status_code == 200:
                # Save the response
                output_file = "test_api_output.docx"
                with open(output_file, 'wb') as f:
                    f.write(response.content)
                
                print(f"✅ API test successful!")
                print(f"📄 Output saved to: {output_file}")
                print(f"📊 File size: {len(response.content)} bytes")
                
                return True
            else:
                print(f"❌ API test failed!")
                print(f"📊 Status code: {response.status_code}")
                print(f"📝 Response: {response.text}")
                return False
                
    except requests.exceptions.Timeout:
        print("❌ Request timed out!")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Connection error! Make sure the server is running.")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def main():
    """Main function."""
    print("🚀 Testing Enhanced PDF to DOCX API")
    print("=" * 50)
    
    # Wait a moment for server to start
    print("⏳ Waiting for server to be ready...")
    time.sleep(2)
    
    # Test the API
    success = test_api()
    
    if success:
        print("\n🎉 API test completed successfully!")
        print("✅ The improved converter is working correctly.")
    else:
        print("\n💥 API test failed!")
        print("❌ Please check the server logs for errors.")

if __name__ == "__main__":
    main() 