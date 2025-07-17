#!/usr/bin/env python3
"""
Test script for OpenAI-enhanced legal document extractor
"""

import json
import sys
import os

# Add the scripts directory to the path
sys.path.append('scripts')

from legal_document_extractor_simple import SimpleLegalDocumentExtractor, extract_legal_metadata

def test_extraction():
    """Test the OpenAI-enhanced extraction"""
    
    # Sample legal document text
    test_text = """
    IN THE HIGH COURT OF DELHI AT NEW DELHI
    
    HON'BLE MR. JUSTICE JOHN DOE
    HON'BLE MRS. JUSTICE JANE SMITH
    
    Case No. WP(C) 1234/2024
    
    BETWEEN
    ABC Corporation Ltd.
    ...Petitioner(s)
    
    AND
    
    State of Delhi & Ors.
    ...Respondent(s)
    
    Through: Mr. Rajesh Kumar, Advocate for Petitioner
    Through: Ms. Priya Sharma, Advocate for Respondent
    
    Decided on 15/01/2025
    
    NEUTRAL CITATION NO. 2025:DLH:1234
    
    JUDGMENT
    
    This case is allowed in part. The petitioner's claim is upheld but the relief is modified as follows...
    
    For the Court
    (JOHN DOE)
    JUDGE
    """
    
    print("Testing OpenAI-enhanced Legal Document Extractor")
    print("=" * 60)
    
    # Initialize the extractor
    extractor = SimpleLegalDocumentExtractor()
    
    if extractor.use_openai:
        print("✅ OpenAI API key found - using AI-powered extraction")
    else:
        print("⚠️  OpenAI API key not found - using regex-based extraction only")
        print("   To enable OpenAI extraction, set your API key in:")
        print("   - Environment variable: OPENAI_API_KEY")
        print("   - Config file: scripts/ai_config.json")
    
    print("\nExtracting metadata...")
    
    # Extract metadata
    metadata = extractor.extract_metadata(test_text)
    
    # Convert to JSON for display
    result = extractor.extract_to_json(test_text)
    
    print("\nExtraction Results:")
    print("=" * 60)
    
    # Display key fields
    key_fields = {
        'Appellant': result.get('appellant', 'Not found'),
        'Respondent': result.get('respondent', 'Not found'),
        'Judge Name': result.get('judgeName', 'Not found'),
        'All Judges': result.get('courtDetailRequest', {}).get('allJudges', 'Not found'),
        'Court Name': result.get('courtDetailRequest', {}).get('courtId', 'Not found'),
        'Neutral Citation': result.get('citationRequest', {}).get('neutralCitation', 'Not found'),
        'Citation Year': result.get('citationRequest', {}).get('year', 'Not found'),
        'Case Number': result.get('caseHistoryRequest', {}).get('caseNumber', 'Not found'),
        'Decision Date': f"{result.get('caseHistoryRequest', {}).get('decidedDay', '1')}/{result.get('caseHistoryRequest', {}).get('decidedMonth', '1')}/{result.get('caseHistoryRequest', {}).get('decidedYear', '2025')}",
        'Case Result': result.get('caseResult', 'Not found'),
        'Advocate for Appellant': result.get('doubleCouncilDetailRequest', {}).get('advocateForAppellant', 'Not found'),
        'Advocate for Respondent': result.get('doubleCouncilDetailRequest', {}).get('advocateForRespondent', 'Not found')
    }
    
    for field, value in key_fields.items():
        print(f"{field:<25}: {value}")
    
    print("\n" + "=" * 60)
    print("Full JSON Output:")
    print(json.dumps(result, indent=2))
    
    return result

def test_with_file(file_path):
    """Test extraction with a file"""
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return None
    
    print(f"Testing extraction with file: {file_path}")
    print("=" * 60)
    
    try:
        # Read the file
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # Extract metadata
        result = extract_legal_metadata(text)
        
        print("\nExtraction Results:")
        print("=" * 60)
        
        # Display key fields
        key_fields = {
            'Appellant': result.get('appellant', 'Not found'),
            'Respondent': result.get('respondent', 'Not found'),
            'Judge Name': result.get('judgeName', 'Not found'),
            'All Judges': result.get('courtDetailRequest', {}).get('allJudges', 'Not found'),
            'Court Name': result.get('courtDetailRequest', {}).get('courtId', 'Not found'),
            'Neutral Citation': result.get('citationRequest', {}).get('neutralCitation', 'Not found'),
            'Citation Year': result.get('citationRequest', {}).get('year', 'Not found'),
            'Case Number': result.get('caseHistoryRequest', {}).get('caseNumber', 'Not found'),
            'Decision Date': f"{result.get('caseHistoryRequest', {}).get('decidedDay', '1')}/{result.get('caseHistoryRequest', {}).get('decidedMonth', '1')}/{result.get('caseHistoryRequest', {}).get('decidedYear', '2025')}",
            'Case Result': result.get('caseResult', 'Not found'),
            'Advocate for Appellant': result.get('doubleCouncilDetailRequest', {}).get('advocateForAppellant', 'Not found'),
            'Advocate for Respondent': result.get('doubleCouncilDetailRequest', {}).get('advocateForRespondent', 'Not found')
        }
        
        for field, value in key_fields.items():
            print(f"{field:<25}: {value}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error processing file: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Test with provided file
        file_path = sys.argv[1]
        test_with_file(file_path)
    else:
        # Test with sample text
        test_extraction() 