#!/usr/bin/env python3
"""
Test script for Enhanced PDF to DOCX Converter
==============================================

This script tests the enhanced PDF to DOCX converter with various legal documents
to ensure proper functionality.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add scripts directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))

from enhanced_pdf_to_docx import LegalDocumentConverter

def test_converter():
    """Test the enhanced PDF to DOCX converter."""
    print("Testing Enhanced PDF to DOCX Converter")
    print("=" * 50)
    
    # Initialize converter
    converter = LegalDocumentConverter()
    
    # Test patterns
    print("\n1. Testing page number detection:")
    test_page_numbers = [
        "Page 1", "page 2", "PAGE 3", "1", "2", "3",
        "Page No. 1", "page no. 2", "1 of 5", "(1 of 5)",
        "[CW-123/2023]", "Page 1 of 10"
    ]
    
    for text in test_page_numbers:
        is_page = converter.is_page_number(text)
        print(f"  '{text}' -> {'Page Number' if is_page else 'Not Page Number'}")
    
    print("\n2. Testing watermark detection:")
    test_watermarks = [
        "CONFIDENTIAL", "DRAFT", "COPY", "SCANNED",
        "DIGITAL COPY", "ORIGINAL", "CERTIFIED COPY",
        "Regular text", "Judgment", "Order"
    ]
    
    for text in test_watermarks:
        is_watermark = converter.is_watermark(text)
        print(f"  '{text}' -> {'Watermark' if is_watermark else 'Not Watermark'}")
    
    print("\n3. Testing text cleaning:")
    test_texts = [
        "  Multiple    spaces   ",
        "Line1\n\n\nLine2",
        "Text with\x00control\x01chars",
        "Normal text"
    ]
    
    for text in test_texts:
        cleaned = converter.clean_text(text)
        print(f"  '{text}' -> '{cleaned}'")
    
    print("\n4. Testing font size detection:")
    test_font_texts = [
        "IN THE HIGH COURT OF DELHI",  # Should be title
        "CRIMINAL APPEAL NO. 123 OF 2023",  # Should be heading
        "Regular paragraph text that goes on for a while",  # Should be body
        "1. First point",  # Should be body
        "Date: 15th December 2023"  # Should be subheading
    ]
    
    for text in test_font_texts:
        font_size = converter.detect_font_size([0, 0, 100, 20, text])  # Mock block
        print(f"  '{text[:30]}...' -> {font_size}")
    
    print("\n5. Testing bold detection:")
    for text in test_font_texts:
        should_bold = converter.should_bold(text)
        print(f"  '{text[:30]}...' -> {'Bold' if should_bold else 'Normal'}")
    
    print("\n✅ All pattern tests completed successfully!")

def test_with_sample_pdf():
    """Test the converter with a sample PDF if available."""
    print("\n" + "=" * 50)
    print("Testing with sample PDF files...")
    
    # Look for test PDFs in the test_files directory
    test_files_dir = Path("testsprite_tests/test_files")
    if not test_files_dir.exists():
        print("❌ Test files directory not found")
        return
    
    pdf_files = list(test_files_dir.glob("*.pdf"))
    if not pdf_files:
        print("❌ No PDF files found in test directory")
        return
    
    converter = LegalDocumentConverter()
    
    for pdf_file in pdf_files[:2]:  # Test first 2 files
        print(f"\nTesting with: {pdf_file.name}")
        
        try:
            # Create temporary output file
            with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp_file:
                output_path = tmp_file.name
            
            # Convert PDF to DOCX
            success = converter.convert_pdf_to_docx(str(pdf_file), output_path)
            
            if success:
                # Check if output file was created and has content
                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    print(f"  ✅ Successfully converted to {os.path.basename(output_path)}")
                    print(f"  📄 Output size: {os.path.getsize(output_path)} bytes")
                else:
                    print(f"  ❌ Output file is empty or not created")
            else:
                print(f"  ❌ Conversion failed")
                
        except Exception as e:
            print(f"  ❌ Error during conversion: {str(e)}")
        finally:
            # Clean up temporary file
            if 'output_path' in locals() and os.path.exists(output_path):
                os.unlink(output_path)

def main():
    """Main test function."""
    print("Enhanced PDF to DOCX Converter Test Suite")
    print("=" * 60)
    
    # Test converter patterns and logic
    test_converter()
    
    # Test with actual PDF files
    test_with_sample_pdf()
    
    print("\n" + "=" * 60)
    print("Test suite completed!")

if __name__ == "__main__":
    main() 