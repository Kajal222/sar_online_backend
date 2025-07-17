import sys
import os
import fitz  # PyMuPDF
import pdfplumber
import pytesseract
from pdf2image import convert_from_path
from typing import Dict, List, Optional, Any
import json
import logging
from datetime import datetime
import requests
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import AI extractor for OpenAI-only approach
try:
    from ai_extractor import AIExtractor
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("AI extractor not available. Cannot proceed with OpenAI-only extraction.")

class OpenAIOnlyMetadataExtractor:
    """
    OpenAI-only metadata extractor for legal documents.
    All field extraction is performed via OpenAI LLM prompts.
    """
    def __init__(self, enable_ai: bool = True):
        self.enable_ai = enable_ai and AI_AVAILABLE
        self.ai_extractor = None
        if self.enable_ai:
            try:
                self.ai_extractor = AIExtractor()
                logger.info("AI extractor initialized for OpenAI-only extraction")
            except Exception as e:
                logger.warning(f"Failed to initialize AI extractor: {e}")
                self.enable_ai = False
        self.available_fields = [
            'citation_year', 'neutral_citation', 'court_category', 'court_name',
            'judge', 'decision_date', 'petitioner', 'respondent', 'case_type',
            'subject_matter', 'case_number', 'case_title', 'bench_composition',
            'judgment_date', 'jurisdiction', 'advocates', 'disposition',
            'cases_referred', 'judge_name'
        ]

    def extract_metadata(self, text: str, field: str) -> str:
        """
        Extract metadata for a specific field using OpenAI only.
        This is the main method that performs the actual extraction.
        """
        field = field.lower().replace(' ', '_')
        if not self.enable_ai or not self.ai_extractor:
            logger.error("AI extractor not available")
            return "Not found"
        try:
            ai_result = self._extract_with_openai(text, field)
            if ai_result:
                logger.info(f"OpenAI extraction successful for {field}: {ai_result}")
                return ai_result
            else:
                logger.info(f"OpenAI extraction failed for {field}")
                return "Not found"
        except Exception as e:
            logger.error(f"Error in OpenAI extraction for {field}: {e}")
            return "Not found"

    def _sanitize_error_message(self, message: str) -> str:
        """
        Sanitize error messages to remove any API keys or sensitive information.
        """
        if not message:
            return message
        
        # Remove API key patterns
        sanitized = re.sub(r'sk-[a-zA-Z0-9]{20,}', '[API_KEY_HIDDEN]', message)
        sanitized = re.sub(r'Bearer [a-zA-Z0-9]{20,}', '[AUTH_HIDDEN]', sanitized)
        
        return sanitized

    def _extract_with_openai(self, text: str, field: str) -> Optional[str]:
        """
        Extract using OpenAI for any field.
        """
        if not self.ai_extractor:
            return None
        try:
            prompt = self._create_prompt_for_field(text, field)
            print(self.ai_extractor.openai_api_key, "self.ai_extractor.openai_api_key")
            headers = {
                "Authorization": f"Bearer {self.ai_extractor.openai_api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": "gpt-4o",
                "messages": [
                    {"role": "system", "content": "You are a legal document parser. Extract information accurately and concisely. Return only the requested information, no other text."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1,
                "max_tokens": 500
            }
            
            # Debug: Print the prompt being sent (without API key)
            logger.info(f"Sending prompt for {field}: {prompt[:200]}...")
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            
            # Debug: Print response status
            logger.info(f"OpenAI response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content'].strip()
                
                # Debug: Print the raw response
                logger.info(f"OpenAI raw response: {content}")
                
                if content and content.lower() != "not found":
                    if content.startswith('[') or content.startswith('{'):
                        try:
                            parsed = json.loads(content)
                            if isinstance(parsed, list):
                                content = "; ".join([str(item) for item in parsed])
                            elif isinstance(parsed, dict):
                                content = str(parsed)
                        except Exception:
                            pass
                    return content
            elif response.status_code == 429:
                logger.error("OpenAI API quota exceeded. Please check your billing and usage limits.")
                return "API quota exceeded"
            else:
                # Debug: Print error response (sanitized)
                error_text = self._sanitize_error_message(response.text)
                logger.error(f"OpenAI API error: {response.status_code} - {error_text}")
            
            return None
        except Exception as e:
            # Sanitize any error messages that might contain API keys
            error_msg = self._sanitize_error_message(str(e))
            logger.error(f"Error in OpenAI extraction for {field}: {error_msg}")
            return None

    def _create_prompt_for_field(self, text: str, field: str) -> str:
        """
        Create appropriate prompt for each field type.
        """
        
        if field == 'advocates':
            return f"""
            Extract all advocate names and their roles from this legal document text.
            
            Instructions:
            1. Look for advocate names like "Shri [Name]", "Mr. [Name]", "Ms. [Name]"
            2. Include their roles like "Advocate for Petitioner", "Advocate for Respondent", etc.
            3. Return only the advocate names and their roles, not other text
            4. Format as: "Shri [Name], Advocate for [Role]"
            5. If multiple advocates, separate with semicolons
            
            Text: {text[:4000]}
            
            Return only the advocate information, no other text.
            """
        
        elif field == 'court_name':
            return f"""
            Extract the complete court name from this legal document text.
            
            Instructions:
            1. Look for court names like "HIGH COURT OF [STATE]", "SUPREME COURT OF INDIA", "DISTRICT COURT", etc.
            2. Include the location if mentioned (e.g., "AT JABALPUR", "AT SRINAGAR")
            3. Include state names with special characters like "JAMMU & KASHMIR AND LADAKH"
            4. Return only the court name, not other text like "BEFORE", "JUSTICE", or judge names
            5. Format as: "HIGH COURT OF [STATE] AT [LOCATION]" or "SUPREME COURT OF INDIA" or "DISTRICT COURT OF [PLACE]"
            6. Remove any line breaks, extra spaces, or irrelevant text
            7. Preserve the exact court name as it appears in the document
            
            Text: {text[:4000]}
            
            Return only the court name, no other text. If no court name is found, return "Not found".
            """
        
        elif field == 'judge':
            return f"""
            Extract judge names from this legal document text.
            
            Instructions:
            1. Look for judge names like "HON'BLE SHRI JUSTICE [Name]", "JUSTICE [Name]", "MR. JUSTICE [Name]"
            2. Include titles like "HON'BLE", "SHRI", "JUSTICE" if they appear with the name
            3. Return only the judge names, not other text
            4. If multiple judges, separate with semicolons
            5. Format as: "HON'BLE SHRI JUSTICE [Name]" or "JUSTICE [Name]"
            
            Text: {text[:4000]}
            
            Return only the judge names, no other text. If no judge names found, return "Not found".
            """
        
        elif field == 'judge_name':
            return f"""
            Extract the judge who gave the judgment from this legal document text.
            
            Instructions:
            1. Look for judge names like "Delivered by: [Name]", "Judgment by: [Name]", "Per: [Name]"
            2. Include the judge's full name and title if mentioned
            3. Return only the judge name, not other text
            4. If multiple judges found, return the one who delivered the judgment
            5. Also look for patterns like "HON'BLE SHRI JUSTICE [Name]", "JUSTICE [Name]" if no specific delivery mention
            6. Focus on the judge who authored or delivered the judgment
            7. Look for "Per: Justice [Name]" or "Per: [Name]" patterns
            8. Handle OCR issues where letters might be separated by spaces
            9. If you see "Per: Justice Sanjeev Sachdeva", return "Justice Sanjeev Sachdeva"
            10. If you see "BEFORE SHRI JUSTICE [Name]", that's the presiding judge
            
            Text: {text[:4000]}
            
            Return only the judge name, no other text. If no judge found, return "Not found".
            """
        
        elif field == 'citation_year':
            return f"""
            Extract the citation year from this legal document text.
            
            Instructions:
            1. Look for citation numbers like "2025:MPHC-JBP:24371", "Citation No. 2024", "Case No. 2023"
            2. Extract only the year part (4-digit year)
            3. Return only the year as a number, not other text
            4. If multiple years found, return the most recent one
            5. Ensure the year is between 1900 and 2030
            
            Text: {text[:4000]}
            
            Return only the year number, no other text. If no year found, return "Not found".
            """
        
        elif field == 'neutral_citation':
            return f"""
            Extract the neutral citation number from this legal document text.
            
            Instructions:
            1. Look for citation numbers like "NEUTRAL CITATION NO. 2025:MPHC-JBP:24371"
            2. Include the full citation format
            3. Return only the citation number, not other text
            4. If multiple citations found, return the first one
            
            Text: {text[:4000]}
            
            Return only the citation number, no other text. If no citation found, return "Not found".
            """
        
        elif field == 'court_category':
            return f"""
            Extract the court category from this legal document text.
            
            Instructions:
            1. Look for court categories like "HIGH COURT", "SUPREME COURT", "DISTRICT COURT", "TRIBUNAL"
            2. Return only the court category, not other text
            3. If multiple categories found, return the highest level court
            
            Text: {text[:4000]}
            
            Return only the court category, no other text. If no category found, return "Not found".
            """
        
        elif field in ['decision_date', 'judgment_date']:
            return f"""
            Extract the {field.replace('_', ' ')} from this legal document text.
            
            Instructions:
            1. Look for dates in formats like "Decided on [date]", "Date: [date]", "Judgment delivered on [date]"
            2. Include various date formats: DD/MM/YYYY, DD-MM-YYYY, DD Month YYYY
            3. Return only the date, not other text
            4. If multiple dates found, return the most relevant one for {field.replace('_', ' ')}
            
            Text: {text[:4000]}
            
            Return only the date, no other text. If no date found, return "Not found".
            """
        
        elif field in ['petitioner', 'respondent']:
            return f"""
            Extract the {field} information from this legal document text.
            
            Instructions:
            1. Look for {field} information like "{field.title()}: [Name/Details]"
            2. Include the full {field} details as mentioned in the document
            3. Return only the {field} information, not other text
            4. If multiple {field}s found, separate with semicolons
            
            Text: {text[:4000]}
            
            Return only the {field} information, no other text. If no {field} found, return "Not found".
            """
        
        elif field == 'case_type':
            return f"""
            Extract the case type from this legal document text.
            
            Instructions:
            1. Look for case types like "Writ Petition", "Civil Appeal", "Criminal Appeal", "Special Leave Petition"
            2. Include specific case types like "Public Interest Litigation", "Constitutional Petition"
            3. Return only the case type, not other text
            4. If multiple case types found, return the most specific one
            
            Text: {text[:4000]}
            
            Return only the case type, no other text. If no case type found, return "Not found".
            """
        
        elif field == 'subject_matter':
            return f"""
            Extract the subject matter from this legal document text.
            
            Instructions:
            1. Look for subject matter like "Subject: [description]", "Regarding: [description]", "In the matter of: [description]"
            2. Include the full subject matter description
            3. Return only the subject matter, not other text
            
            Text: {text[:4000]}
            
            Return only the subject matter, no other text. If no subject matter found, return "Not found".
            """
        
        elif field == 'case_number':
            return f"""
            Extract the case number from this legal document text.
            
            Instructions:
            1. Look for case numbers like "Case No. [number]", "Diary No. [number]", "M.P. No. [number]"
            2. Include the full case number format as mentioned
            3. Return only the case number, not other text
            4. If multiple case numbers found, return the first one
            
            Text: {text[:4000]}
            
            Return only the case number, no other text. If no case number found, return "Not found".
            """
        
        elif field == 'case_title':
            return f"""
            Extract the case title from this legal document text.
            
            Instructions:
            1. Look for case titles like "Petitioner vs Respondent", "Appellant vs Respondent"
            2. Include the full case title with party names
            3. Return only the case title, not other text
            4. If multiple titles found, return the most complete one
            
            Text: {text[:4000]}
            
            Return only the case title, no other text. If no case title found, return "Not found".
            """
        
        elif field == 'bench_composition':
            return f"""
            Extract the bench composition from this legal document text.
            
            Instructions:
            1. Look for bench composition like "BEFORE HON'BLE SHRI JUSTICE [Name]", "CORAM: [judges]"
            2. Include the full bench composition as mentioned
            3. Return only the bench composition, not other text
            4. If multiple compositions found, return the first one
            
            Text: {text[:4000]}
            
            Return only the bench composition, no other text. If no bench composition found, return "Not found".
            """
        
        elif field == 'jurisdiction':
            return f"""
            Extract the jurisdiction type from this legal document text.
            
            Instructions:
            1. Look for jurisdiction types like "Civil Jurisdiction", "Criminal Jurisdiction", "Writ Jurisdiction"
            2. Include specific jurisdiction types like "Original Jurisdiction", "Appellate Jurisdiction"
            3. Return only the jurisdiction type, not other text
            4. If multiple jurisdictions found, return the most specific one
            
            Text: {text[:4000]}
            
            Return only the jurisdiction type, no other text. If no jurisdiction found, return "Not found".
            """
        
        elif field == 'disposition':
            return f"""
            Extract the disposition/outcome from this legal document text.
            
            Instructions:
            1. Look for disposition like "Allowed", "Dismissed", "Partly Allowed", "Remanded"
            2. Include specific outcomes like "Set aside", "Quashed", "Upheld", "Affirmed"
            3. Return only the disposition, not other text
            4. If multiple dispositions found, return the final outcome
            
            Text: {text[:4000]}
            
            Return only the disposition, no other text. If no disposition found, return "Not found".
            """
        
        elif field == 'cases_referred':
            return f"""
            Extract the cases referred/cited from this legal document text.
            
            Instructions:
            1. Look for case references like "Relied on: [cases]", "Referred to: [cases]", "Following: [cases]"
            2. Include citation formats like "AIR 2020 SC 123", "2020 SCC 123"
            3. Return only the case references, not other text
            4. If multiple references found, separate with semicolons
            
            Text: {text[:4000]}
            
            Return only the case references, no other text. If no cases referred found, return "Not found".
            """
        
        else:
            # Generic prompt for any other field
            return f"""
            Extract the {field.replace('_', ' ')} from this legal document text.
            
            Instructions:
            1. Look for {field.replace('_', ' ')} information in the document
            2. Return only the {field.replace('_', ' ')}, not other text
            3. If multiple instances found, return the most relevant one
            
            Text: {text[:4000]}
            
            Return only the {field.replace('_', ' ')}, no other text. If no {field.replace('_', ' ')} found, return "Not found".
            """

    def extract_all_fields(self, text: str) -> Dict[str, str]:
        """
        Extract all available fields from the text using OpenAI only.
        """
        results = {}
        for field_name in self.available_fields:
            results[field_name] = self.extract_metadata(text, field_name)
        return results

# Initialize the extractor
extractor = OpenAIOnlyMetadataExtractor()

def extract_metadata_legacy(text, field):
    """
    Legacy function for backward compatibility.
    This function delegates to the OpenAIOnlyMetadataExtractor instance.
    """
    return extractor.extract_metadata(text, field)

# Alias for backward compatibility
extract_metadata = extract_metadata_legacy

def extract_text_from_pdf(pdf_path):
    """
    Extract text from PDF using PyMuPDF.
    """
    try:
        doc = fitz.open(pdf_path)
        full_text = ""
        for page in doc:
            full_text += page.get_text()
        return full_text
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {e}")
        return ""

def extract_text_from_pdf_with_pdfplumber(pdf_path):
    """
    Extract text from PDF using pdfplumber.
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            all_text = ""
            for page in pdf.pages:
                text = page.extract_text(x_tolerance=2, y_tolerance=2)
                if text:
                    all_text += text + "\n\n"
        return all_text
    except Exception as e:
        logger.error(f"Error extracting text with pdfplumber: {e}")
        return ""

def extract_text_from_pdf_with_ocr(pdf_path):
    """
    Extract text from PDF using OCR.
    """
    try:
        pages = convert_from_path(pdf_path)
        all_text = ""
        for page in pages:
            text = pytesseract.image_to_string(page, lang='eng')
            all_text += text + "\n\n"
        return all_text
    except Exception as e:
        logger.error(f"Error extracting text with OCR: {e}")
        return ""

def extract_all_metadata(file_path: str) -> Dict[str, Any]:
    """
    Extract all available metadata from a document using OpenAI only.
    """
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        text = extract_text_from_pdf(file_path)
        if not text.strip():
            text = extract_text_from_pdf_with_pdfplumber(file_path)
        if not text.strip():
            text = extract_text_from_pdf_with_ocr(file_path)
    elif ext == ".txt":
        try:
            with open(file_path, encoding="utf-8") as f:
                text = f.read()
        except UnicodeDecodeError:
            with open(file_path, encoding="latin-1") as f:
                text = f.read()
    else:
        try:
            with open(file_path, encoding="utf-8") as f:
                text = f.read()
        except UnicodeDecodeError:
            with open(file_path, encoding="latin-1") as f:
                text = f.read()
    metadata = extractor.extract_all_fields(text)
    metadata['document_type'] = ext.upper().replace('.', '')
    metadata['extraction_timestamp'] = datetime.now().isoformat()
    metadata['text_length'] = len(text)
    metadata['extraction_method'] = 'openai_only'
    return metadata

def debug_extract_text(file_path: str) -> str:
    """
    Debug function to extract and print text from PDF for analysis.
    """
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == ".pdf":
        text = extract_text_from_pdf(file_path)
        if not text.strip():
            text = extract_text_from_pdf_with_pdfplumber(file_path)
        if not text.strip():
            text = extract_text_from_pdf_with_ocr(file_path)
    else:
        try:
            with open(file_path, encoding="utf-8") as f:
                text = f.read()
        except UnicodeDecodeError:
            with open(file_path, encoding="latin-1") as f:
                text = f.read()
    
    print("=" * 80)
    print("EXTRACTED TEXT (first 4000 characters):")
    print("=" * 80)
    print(text[:4000])
    print("=" * 80)
    print(f"Total text length: {len(text)} characters")
    print("=" * 80)
    
    return text

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python metadata_extractor.py <file_path> [field_name]")
        print("Available fields:")
        print("  Basic: citation_year, neutral_citation, judge, court_name, court_category")
        print("  Dates: decision_date, judgment_date")
        print("  Parties: petitioner, respondent, case_title")
        print("  Case Info: case_number, case_type, subject_matter, jurisdiction")
        print("  Court Info: bench_composition, advocates")
        print("  Outcome: disposition, cases_referred, judge_name")
        print("Or use 'all' to extract all fields")
        print("\nNote: This version uses OpenAI only for all extractions.")
        sys.exit(1)
    file_path = sys.argv[1]
    if len(sys.argv) == 2 or (len(sys.argv) == 3 and sys.argv[2].lower() == 'all'):
        metadata = extract_all_metadata(file_path)
        print(json.dumps(metadata, indent=2))
    else:
        field_name = sys.argv[2]
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".pdf":
            text = extract_text_from_pdf(file_path)
        elif ext == ".txt":
            try:
                with open(file_path, encoding="utf-8") as f:
                    text = f.read()
            except UnicodeDecodeError:
                with open(file_path, encoding="latin-1") as f:
                    text = f.read()
        else:
            try:
                with open(file_path, encoding="utf-8") as f:
                    text = f.read()
            except UnicodeDecodeError:
                with open(file_path, encoding="latin-1") as f:
                    text = f.read()
        result = extract_metadata(text, field_name)
        print(result) 