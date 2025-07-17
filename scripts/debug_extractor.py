#!/usr/bin/env python3
"""
DEBUG VERSION - Legal Document Metadata Extractor
This version shows what text is actually extracted from the PDF
"""

import sys
import json
import re
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_extract_legal_metadata(text):
    """Debug version that shows what's happening"""
    
    print("=" * 60, file=sys.stderr)
    print("DEBUG: TEXT EXTRACTION ANALYSIS", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print(f"Text length: {len(text)}", file=sys.stderr)
    print(f"First 500 characters:", file=sys.stderr)
    print(repr(text[:500]), file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    
    # Check for key patterns
    patterns_to_check = [
        ("Petitioner pattern", r'\.\.\.Petitioner'),
        ("Versus pattern", r'Versus'),
        ("Mrs/Mr pattern", r'(?:Mrs?\.|Mr\.|Ms\.|Dr\.)'),
        ("State pattern", r'State\s+of\s+[A-Z][a-z]+'),
        ("High Court pattern", r'HIGH\s+COURT'),
        ("Case number pattern", r'(?:WRIT\s+PETITION|W\.?P\.?).*?(?:NO\.|Number).*?\d+.*?(?:OF|of).*?\d{4}')
    ]
    
    print("PATTERN MATCHING RESULTS:", file=sys.stderr)
    for desc, pattern in patterns_to_check:
        matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
        print(f"{desc}: {matches}", file=sys.stderr)
    
    print("=" * 60, file=sys.stderr)
    
    # Try to extract appellant with detailed debugging
    print("APPELLANT EXTRACTION DEBUG:", file=sys.stderr)
    appellant_patterns = [
        r'^((?:Mrs?\.|Mr\.|Ms\.|Dr\.)\s+[A-Z][A-Za-z\s]+)\s*\n',
        r'((?:Mrs?\.|Mr\.|Ms\.|Dr\.)\s+[A-Z][A-Za-z\s\.&,()-]*?)\s*\n[\s\S]*?\.\.\.Petitioner',
        r'([A-Z][A-Za-z\s\.&,()-]+?)\s*(?:…|\.\.\.)\s*(?:Petitioner|Appellant)',
    ]
    
    appellant_found = None
    for i, pattern in enumerate(appellant_patterns):
        matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
        print(f"Appellant pattern {i+1}: {matches}", file=sys.stderr)
        if matches and not appellant_found:
            appellant_found = matches[0]
    
    # Try to extract respondent
    print("RESPONDENT EXTRACTION DEBUG:", file=sys.stderr)
    respondent_patterns = [
        r'(State\s+of\s+[A-Z][a-z]+)',
        r'(?:VERSUS|vs\.?|Versus)\s*\n\s*(?:\d+\.\s*)?([A-Z][A-Za-z\s\.&,()-]+?)(?=\s*(?:\n|Through|$))',
    ]
    
    respondent_found = None
    for i, pattern in enumerate(respondent_patterns):
        matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
        print(f"Respondent pattern {i+1}: {matches}", file=sys.stderr)
        if matches and not respondent_found:
            respondent_found = matches[0]
    
    # Extract case number
    print("CASE NUMBER EXTRACTION DEBUG:", file=sys.stderr)
    case_patterns = [
        r'(WRIT\s+PETITION\s+NO\.\s*\d+\s+OF\s+\d{4})',
        r'(W\.?P\.?\s*(?:\([A-Z]\))?\s*(?:No\.?)?\s*\d+\s*of\s*\d{4})',
    ]
    
    case_found = None
    for i, pattern in enumerate(case_patterns):
        matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
        print(f"Case number pattern {i+1}: {matches}", file=sys.stderr)
        if matches and not case_found:
            case_found = matches[0]
    
    print("=" * 60, file=sys.stderr)
    print("FINAL EXTRACTED VALUES:", file=sys.stderr)
    print(f"Appellant: {appellant_found}", file=sys.stderr)
    print(f"Respondent: {respondent_found}", file=sys.stderr)
    print(f"Case Number: {case_found}", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    
    # Return the result with debug info
    result = {
        "docId": 0,
        "appellant": appellant_found if appellant_found else "Appellant",
        "remarkable": "none",
        "respondent": respondent_found if respondent_found else "Respondents",
        "judgeName": "none",
        "judgementOrder": "",
        "judgementType": "Judgement",
        "caseResult": "This is result",
        "doubleCouncilDetailRequest": {
            "advocateForRespondent": "none",
            "advocateForAppellant": "none",
            "extraCouncilDetails": "none"
        },
        "singleCouncilDetailRequest": None,
        "courtDetailRequest": {
            "allJudges": "none",
            "courtBenchId": 2,
            "courtBranchId": "34",
            "courtId": 19
        },
        "citationRequest": {
            "citationCategoryId": 0,
            "journalId": 0,
            "otherCitation": "",
            "neutralCitation": "",
            "pageNumber": "1",
            "year": 2025,
            "volume": "none",
            "secondaryCitationCategoryId": 0,
            "secondaryJournalId": 0,
            "secondaryPageNumber": "",
            "secondaryYear": "0",
            "secondaryVolume": "",
            "thirdCitationCategoryId": 0,
            "thirdJournalId": 0,
            "thirdPageNumber": "none",
            "thirdYear": "0",
            "thirdVolume": "none",
            "fourthCitationCategoryId": 0,
            "fourthJournalId": 0,
            "fourthPageNumber": "none",
            "fourthYear": "0",
            "fourthVolume": "none"
        },
        "additionalAppellantRespondentRequestList": [],
        "caseHistoryRequest": {
            "caseNumber": case_found if case_found else "1",
            "decidedDay": "1",
            "decidedMonth": "1",
            "decidedYear": 2025,
            "notes": "none",
            "year": 2025
        },
        "casesReferredRequestList": [],
        "headNoteRequestList": [],
        "caseTopics": [],
        "debug_info": {
            "text_length": len(text),
            "text_preview": text[:200],
            "patterns_found": {
                "petitioner": bool(re.search(r'\.\.\.Petitioner', text, re.IGNORECASE)),
                "versus": bool(re.search(r'Versus', text, re.IGNORECASE)),
                "titles": bool(re.search(r'(?:Mrs?\.|Mr\.|Ms\.|Dr\.)', text, re.IGNORECASE)),
                "state": bool(re.search(r'State\s+of', text, re.IGNORECASE)),
                "high_court": bool(re.search(r'HIGH\s+COURT', text, re.IGNORECASE)),
            }
        }
    }
    
    return result

def extract_from_pdf_debug(pdf_path):
    """Debug version of PDF extraction"""
    try:
        print(f"DEBUG: Attempting to process PDF: {pdf_path}", file=sys.stderr)
        
        # Try to import PyMuPDF
        try:
            import fitz
            print("DEBUG: PyMuPDF imported successfully", file=sys.stderr)
        except ImportError as e:
            print(f"DEBUG: PyMuPDF import failed: {e}", file=sys.stderr)
            return debug_extract_legal_metadata("")
        
        # Try to open PDF
        try:
            doc = fitz.open(pdf_path)
            print(f"DEBUG: PDF opened successfully, {len(doc)} pages", file=sys.stderr)
        except Exception as e:
            print(f"DEBUG: Failed to open PDF: {e}", file=sys.stderr)
            return debug_extract_legal_metadata("")
        
        # Extract text from all pages
        text = ""
        for page_num in range(len(doc)):
            try:
                page = doc[page_num]
                page_text = page.get_text()
                text += page_text + "\n"
                print(f"DEBUG: Page {page_num + 1} extracted {len(page_text)} characters", file=sys.stderr)
            except Exception as e:
                print(f"DEBUG: Error extracting page {page_num + 1}: {e}", file=sys.stderr)
        
        doc.close()
        print(f"DEBUG: Total extracted text length: {len(text)}", file=sys.stderr)
        
        if not text.strip():
            print("DEBUG: No text found, trying OCR...", file=sys.stderr)
            # Try OCR
            try:
                import pytesseract
                from PIL import Image
                import io
                
                doc = fitz.open(pdf_path)
                text = ""
                for page_num in range(len(doc)):
                    page = doc[page_num]
                    pix = page.get_pixmap()
                    img_data = pix.tobytes("png")
                    img = Image.open(io.BytesIO(img_data))
                    page_text = pytesseract.image_to_string(img)
                    text += page_text + "\n"
                    print(f"DEBUG: OCR Page {page_num + 1} extracted {len(page_text)} characters", file=sys.stderr)
                doc.close()
                print(f"DEBUG: OCR total extracted text length: {len(text)}", file=sys.stderr)
            except ImportError:
                print("DEBUG: OCR libraries not available", file=sys.stderr)
        
        return debug_extract_legal_metadata(text)
        
    except Exception as e:
        print(f"DEBUG: Unexpected error in PDF processing: {e}", file=sys.stderr)
        return debug_extract_legal_metadata("")

def main():
    """Main function with debug output"""
    try:
        print("DEBUG: Script started", file=sys.stderr)
        print(f"DEBUG: Arguments: {sys.argv}", file=sys.stderr)
        
        if '--pdf' in sys.argv:
            pdf_index = sys.argv.index('--pdf')
            if pdf_index + 1 < len(sys.argv):
                pdf_path = sys.argv[pdf_index + 1]
                print(f"DEBUG: Processing PDF: {pdf_path}", file=sys.stderr)
                
                if not os.path.exists(pdf_path):
                    raise FileNotFoundError(f"PDF file not found: {pdf_path}")
                
                result = extract_from_pdf_debug(pdf_path)
            else:
                raise ValueError("No PDF path provided after --pdf flag")
        
        elif '--text' in sys.argv:
            text_index = sys.argv.index('--text')
            if text_index + 1 < len(sys.argv):
                text = sys.argv[text_index + 1]
                print(f"DEBUG: Processing text of length: {len(text)}", file=sys.stderr)
                result = debug_extract_legal_metadata(text)
            else:
                raise ValueError("No text provided after --text flag")
        
        elif '--help' in sys.argv:
            print("Debug Legal Document Metadata Extractor")
            print("Usage:")
            print("  python debug_extractor.py --pdf <file.pdf>")
            print("  python debug_extractor.py --text <text_content>")
            sys.exit(0)
        
        else:
            # Test with your sample text
            test_text = """IN THE HIGH COURT OF BOMBAY AT GOA

WRIT PETITION NO.2955 OF 2024(F)

Mrs. Anita Yuvraj Naik
Age 59,
Section Officer, Goa Legislature
Secretariat,
Assembly Complex, Porvorim Goa,
Resident of House No. 646/1,
Kadamba Depot Road,
Bardez Goa.                                    ...Petitioner

Versus

1. State of Goa,
Through its Chief Secretary,
Secretariat, Porvorim, Goa."""
            print("DEBUG: Using test text", file=sys.stderr)
            result = debug_extract_legal_metadata(test_text)
        
        # Output result
        print(json.dumps(result, ensure_ascii=False))
        
    except Exception as e:
        print(f"DEBUG: Script error: {e}", file=sys.stderr)
        error_result = {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "debug": True
        }
        print(json.dumps(error_result))
        sys.exit(1)

if __name__ == "__main__":
    main()