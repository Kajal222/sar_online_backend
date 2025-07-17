#!/usr/bin/env python3
"""
Test script for enhanced legal document metadata extraction
"""

import sys
import json
from scripts.enhanced_extractor import extract_legal_metadata

def test_extraction():
    """Test the extraction with various scenarios"""
    
    test_cases = [
        {
            "name": "Standard Case Format",
            "text": """
            IN THE HIGH COURT OF DELHI
            HON'BLE JUSTICE RAJESH KUMAR
            W.P.(C) 1234/2024
            ABC Corporation Ltd. ... Petitioner
            vs
            State of Delhi ... Respondent
            Through: Mr. John Smith
            Advocate for Petitioner: Mr. David Wilson
            Advocate for Respondent: Mr. Robert Brown
            Decided on 15/01/2025
            NEUTRAL CITATION NO. 2025:DLH:1234
            JUDGMENT
            The petition is allowed.
            """
        },
        {
            "name": "Government vs Private Party",
            "text": """
            IN THE SUPREME COURT OF INDIA
            HON'BLE MR. JUSTICE AMIT KUMAR
            C.A. 5678/2024
            Union of India ... Appellant
            vs
            XYZ Private Limited ... Respondent
            Through: Mr. Advocate General
            Advocate for Appellant: Mr. Attorney General
            Advocate for Respondent: Mr. Senior Counsel
            Decided on 20/02/2025
            NEUTRAL CITATION NO. 2025:SCI:5678
            JUDGMENT
            The appeal is dismissed.
            """
        },
        {
            "name": "Problematic Case (like the original issue)",
            "text": """
            IN THE HIGH COURT OF UTTAR PRADESH
            HON'BLE JUSTICE SHARMA
            W.P. 9999/2024
            Others Counsel for ... Petitioner
            vs
            State Of Up ... Respondent
            Through: Mr. Legal Expert
            Advocate for Petitioner: Mr. Defense Counsel
            Advocate for Respondent: Mr. State Advocate
            Decided on 10/03/2025
            NEUTRAL CITATION NO. 2025:UPH:9999
            JUDGMENT
            The petition is disposed of.
            """
        }
    ]
    
    print("Testing Enhanced Legal Document Metadata Extraction")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}: {test_case['name']}")
        print("-" * 40)
        
        result = extract_legal_metadata(test_case['text'])
        
        # Print key fields
        print(f"Appellant: {result['appellant']}")
        print(f"Respondent: {result['respondent']}")
        print(f"Judge: {result['judgeName']}")
        print(f"Case Result: {result['caseResult']}")
        print(f"Appellant Advocate: {result['doubleCouncilDetailRequest']['advocateForAppellant']}")
        print(f"Respondent Advocate: {result['doubleCouncilDetailRequest']['advocateForRespondent']}")
        print(f"Citation: {result['citationRequest']['neutralCitation']}")
        print(f"Date: {result['caseHistoryRequest']['decidedDay']}/{result['caseHistoryRequest']['decidedMonth']}/{result['caseHistoryRequest']['decidedYear']}")
        
        # Check for problematic extractions
        issues = []
        if len(result['appellant']) > 50:
            issues.append("Appellant name too long")
        if len(result['respondent']) > 50:
            issues.append("Respondent name too long")
        if len(result['doubleCouncilDetailRequest']['advocateForAppellant']) > 50:
            issues.append("Appellant advocate name too long")
        if len(result['doubleCouncilDetailRequest']['advocateForRespondent']) > 50:
            issues.append("Respondent advocate name too long")
        
        if issues:
            print(f"⚠️  Issues found: {', '.join(issues)}")
        else:
            print("✅ No extraction issues detected")
    
    print("\n" + "=" * 60)
    print("Test completed!")

if __name__ == "__main__":
    test_extraction() 