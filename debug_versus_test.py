#!/usr/bin/env python3
"""
Debug script for VERSUS pattern extraction
"""

import re
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))

from legal_document_extractor_simple import SimpleLegalDocumentExtractor

def test_versus_extraction():
    """Test VERSUS pattern extraction with exact text"""
    
    # Your exact text format
    test_text = """
    IN THE HIGH COURT OF DELHI
    
    UNION OF INDIA AND ANOTHER
    Versus
    NIRMALA RAJPU
    
    Case No. WP(C) 1234/2024
    
    HON'BLE JUSTICE JOHN DOE
    
    Advocate for Appellant: Mr. Smith
    Advocate for Respondent: Ms. Johnson
    
    JUDGMENT
    
    This case is allowed.
    """
    
    print("=== DEBUGGING VERSUS EXTRACTION ===")
    print(f"Input text:\n{repr(test_text)}")
    print()
    
    # Test the line-by-line logic manually
    header_text = test_text[:1000]
    lines = [line.strip() for line in header_text.splitlines()]
    print("Lines in header:")
    for i, line in enumerate(lines):
        print(f"  {i}: '{line}'")
    
    print("\nLooking for VERSUS pattern...")
    for i, line in enumerate(lines):
        if re.fullmatch(r'(?:VERSUS|Versus|VS|vs)', line, flags=re.IGNORECASE):
            print(f"Found VERSUS at line {i}: '{line}'")
            # Find previous non-empty line
            prev = next((lines[j] for j in range(i-1, -1, -1) if lines[j]), None)
            # Find next non-empty line
            next_ = next((lines[j] for j in range(i+1, len(lines)) if lines[j]), None)
            print(f"Previous line: '{prev}'")
            print(f"Next line: '{next_}'")
            break
    else:
        print("No VERSUS pattern found!")
    
    print("\n=== EXTRACTOR TEST ===")
    extractor = SimpleLegalDocumentExtractor()
    result = extractor.extract_to_json(test_text)
    
    print(f"Appellant: {result['appellant']}")
    print(f"Respondent: {result['respondent']}")

if __name__ == "__main__":
    test_versus_extraction() 