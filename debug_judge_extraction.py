#!/usr/bin/env python3
"""Debug script for judge name extraction"""

import re
from scripts.legal_document_extractor import LegalDocumentExtractor

def debug_judge_extraction():
    """Debug judge name extraction"""
    print("Debugging judge name extraction...")
    
    # Test with the problematic text
    test_text = """
    IN THE HIGH COURT OF DELHI
    
    ORDER
    
    Bench of this Court has taken the view that HON'BLE MR. JUSTICE JAVED IQBAL WANI, JUDGE the Tribunal.
    the Tribunal and that as per the said record the said the Court, there the the Tribunal it had not been able to do so, the Registry
    
    Case No. WP(C) 1234/2024
    """
    
    # Initialize extractor
    extractor = LegalDocumentExtractor()
    
    # Test the raw extraction
    raw_judge = extractor._extract_field(test_text, 'judge')
    print("Raw judge extraction:", repr(raw_judge))
    
    # Test the cleaning function
    cleaned_judge = extractor._clean_judge_name(raw_judge)
    print("Cleaned judge name:", repr(cleaned_judge))
    
    # Test individual patterns
    patterns = [
        r'HON\'BLE\s+MR\.\s+JUSTICE\s+([A-Z][a-zA-Z\s\.]+?)(?=\s|$|,|AND|OR)',
        r'HON\'BLE\s+MRS\.\s+JUSTICE\s+([A-Z][a-zA-Z\s\.]+?)(?=\s|$|,|AND|OR)',
        r'HON\'BLE\s+JUSTICE\s+([A-Z][a-zA-Z\s\.]+?)(?=\s|$|,|AND|OR)',
        r'MR\.\s+JUSTICE\s+([A-Z][a-zA-Z\s\.]+?)(?=\s|$|,|AND|OR)',
        r'MRS\.\s+JUSTICE\s+([A-Z][a-zA-Z\s\.]+?)(?=\s|$|,|AND|OR)',
        r'JUSTICE\s+([A-Z][a-zA-Z\s\.]+?)(?=\s|$|,|AND|OR)',
        r'JUDGE\s+([A-Z][a-zA-Z\s\.]+?)(?=\s|$|,|AND|OR)',
        r'MAGISTRATE\s+([A-Z][a-zA-Z\s\.]+?)(?=\s|$|,|AND|OR)',
        r'PRESIDING OFFICER\s+([A-Z][a-zA-Z\s\.]+?)(?=\s|$|,|AND|OR)'
    ]
    
    print("\nTesting individual patterns:")
    for i, pattern in enumerate(patterns):
        matches = re.findall(pattern, test_text, re.IGNORECASE)
        print(f"Pattern {i+1}: {matches}")
    
    # Test a simpler pattern
    simple_pattern = r'HON\'BLE\s+MR\.\s+JUSTICE\s+([A-Z][a-zA-Z\s\.]+)'
    matches = re.findall(simple_pattern, test_text, re.IGNORECASE)
    print(f"\nSimple pattern matches: {matches}")

if __name__ == "__main__":
    debug_judge_extraction() 