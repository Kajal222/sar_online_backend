#!/usr/bin/env python3
"""
Final AI-Powered Legal Document Extractor
Handles PDFs, Images, Scanned documents with OCR
Uses OpenAI for accurate extraction of all legal metadata
"""

import sys
import json
import re
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional
import base64

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# AI Integration
try:
    from openai import OpenAI
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    logger.warning("OpenAI not available")

# Document processing libraries
try:
    import fitz  # PyMuPDF
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    logger.warning("PyMuPDF not available")

try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    logger.warning("OCR libraries not available")

class AILegalDocumentExtractor:
    def __init__(self, api_key: str = None, model: str = "gpt-4o"):
        self.api_key = api_key or os.environ.get('OPENAI_API_KEY') or self._load_api_key_from_config()
        self.model = model
        logger.info(f"api_key: {self.api_key}") 
        if self.api_key and AI_AVAILABLE:
            # openai.api_key = self.api_key # This line is no longer needed as OpenAI is imported directly
            logger.info("OpenAI initialized successfully")
        else:
            logger.warning("OpenAI not available - will use fallback methods")

    def _load_api_key_from_config(self) -> Optional[str]:
        """Load OpenAI API key from scripts/ai_config.json config file"""
        config_path = os.path.join(os.path.dirname(__file__), 'ai_config.json')
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            api_key = config.get('openai_api_key')
            if api_key and api_key.startswith('sk-'):
                return api_key
            logger.warning("No valid OpenAI API key found in config file")
        except Exception as e:
            logger.warning(f"Could not load OpenAI API key from config: {e}")
        return None

    def extract_from_file(self, file_path: str) -> Dict:
        """Extract from any supported file type"""
        
        if not os.path.exists(file_path):
            return self._create_error_result(f"File not found: {file_path}")
        
        file_ext = os.path.splitext(file_path)[1].lower()
        
        try:
            if file_ext == '.pdf':
                return self._extract_from_pdf(file_path)
            elif file_ext in ['.jpg', '.jpeg', '.png', '.tiff', '.bmp']:
                return self._extract_from_image(file_path)
            else:
                # Try to read as text file
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
                return self.extract_from_text(text)
                
        except Exception as e:
            logger.error(f"File extraction failed: {e}")
            return self._create_error_result(f"File extraction failed: {str(e)}")

    def _extract_from_pdf(self, pdf_path: str) -> Dict:
        """Extract text from PDF with OCR fallback"""
        
        if not PDF_AVAILABLE:
            return self._create_error_result("PDF processing not available - install PyMuPDF")
        
        try:
            doc = fitz.open(pdf_path)
            text = ""
            images_processed = 0
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # Try direct text extraction first
                page_text = page.get_text()
                
                # If no text found, try OCR on page image
                if not page_text.strip() and OCR_AVAILABLE:
                    logger.info(f"No text found on page {page_num + 1}, using OCR")
                    pix = page.get_pixmap()
                    img_data = pix.tobytes("png")
                    img = Image.open(io.BytesIO(img_data))
                    page_text = pytesseract.image_to_string(img, config='--psm 6')
                    images_processed += 1
                
                text += page_text + "\n"
            
            logger.info(f"PDF processed: {len(doc)} pages, {images_processed} pages with OCR")
            doc.close()
            
            if not text.strip():
                return self._create_error_result("No text content found in PDF")
            
            return self.extract_from_text(text)
            
        except Exception as e:
            logger.error(f"PDF extraction failed: {e}")
            return self._create_error_result(f"PDF extraction failed: {str(e)}")

    def _extract_from_image(self, image_path: str) -> Dict:
        """Extract text from image using OCR"""
        
        if not OCR_AVAILABLE:
            return self._create_error_result("OCR not available - install pytesseract and PIL")
        
        try:
            # Open image
            img = Image.open(image_path)
            
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Extract text using OCR
            text = pytesseract.image_to_string(img, config='--psm 6')
            
            logger.info(f"OCR extracted {len(text)} characters from image")
            
            if not text.strip():
                return self._create_error_result("No text found in image")
            
            return self.extract_from_text(text)
            
        except Exception as e:
            logger.error(f"Image OCR failed: {e}")
            return self._create_error_result(f"Image OCR failed: {str(e)}")

    def extract_from_text(self, text: str) -> Dict:
        """Extract all legal metadata using AI"""
        
        if not text or not text.strip():
            return self._create_error_result("No text content provided")
        
        # Clean and prepare text
        text = self._clean_text(text)
        
        logger.info(f"Processing text of length: {len(text)}")
        
        # Use AI for extraction
        if self.api_key and AI_AVAILABLE:
            ai_result = self._extract_with_openai(text)
            if ai_result and ai_result.get('success', False):
                return ai_result
        
        # Fallback to regex if AI fails
        logger.warning("Using fallback regex extraction")
        return self._extract_with_regex(text)

    def _extract_with_openai(self, text: str) -> Dict:
        """Use OpenAI GPT-4 for comprehensive legal metadata extraction"""
        try:
            # Create comprehensive prompt
            prompt = self._create_comprehensive_prompt(text)
            logger.info(f"self.api_key: {self.api_key}")
            # Instantiate OpenAI client
            client = OpenAI(api_key=self.api_key) if self.api_key else OpenAI()

            # Call OpenAI API using new v1.x syntax
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert legal document analyzer with deep knowledge of Indian legal document formats, court structures, and legal terminology. Extract information with 100% accuracy and return only valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=2000
            )

            result_text = response.choices[0].message.content.strip()

            # Extract JSON from response
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                result_text = json_match.group(0)

            # Parse and validate result
            ai_data = json.loads(result_text)

            # Convert to required format
            formatted_result = self._format_ai_result(ai_data)

            logger.info("OpenAI extraction successful")
            logger.info(f"Extracted - Appellant: {formatted_result['appellant']}")
            logger.info(f"Extracted - Respondent: {formatted_result['respondent']}")
            logger.info(f"Extracted - Judge: {formatted_result['judgeName']}")

            return formatted_result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OpenAI JSON: {e}")
            logger.error(f"Raw response: {result_text[:500]}")
            return None

        except Exception as e:
            logger.error(f"OpenAI extraction failed: {e}")
            return None

    def _create_comprehensive_prompt(self, text: str) -> str:
        """Create a comprehensive prompt for all legal metadata extraction"""
        
        # Limit text to avoid token limits
        text_sample = text[:4000] if len(text) > 4000 else text
        
        return f"""
Analyze this Indian legal document and extract ALL the following information with 100% accuracy.

DOCUMENT TEXT:
{text_sample}

Extract the following fields and return ONLY valid JSON with these exact keys:

1. "appellants": Look for words like "Appellant", "Petitioner", or "Petitioners" — these are mostly found on the first page. There can be multiple names, so return them in an array format. Extract only the main entity names (e.g., remove address, “through Secretary”, etc.).

2. "respondents": Look for words like "Respondent" or "Respondents", also typically on the first page. Extract all respondent names in an array. Same as appellants, extract only the main names.

3. "judge_name": Check for presence of "Judgment" or "Order" in the document. Judge names are often mentioned in dedicated paragraphs or at the end of the document like “(ANIL KSHETARPAL) JUDGE”. Extract the full name of the judge, excluding prefixes like "Justice", "Hon’ble", etc.

4. "case_number" and "case_year": Extract from lines such as:
   - "WRIT C No. 2373 of 2024"
   - "Case :- APPEAL UNDER SECTION 37... DEFECTIVE No. - 9 of 2025"
   - "MATA No. 272 of 2023"
   - "CR-3041 of 2025(O&M)"
   Use natural language understanding to identify the number and year. These are mostly on the first page.

5. "court_name" and "court_location": Try to find exact court name and location using your knowledge. This info often appears on the first or last page. Examples:
   - "SUPREME COURT OF INDIA"
   - "HIGH COURT OF JUDICATURE AT BOMBAY, NAGPUR BENCH"
6. "judgment_type": Understand whether the document contains a "Judgment" or an "Order". Sometimes it is titled clearly (e.g., "JUDGMENT") or inferred from judge's written decision. Use your reasoning to classify correctly.

7. "case_result": If there's a heading like "JUDGMENT" or "ORDER", extract the paragraph(s) directly under it. If not, summarize the final decision from the document (e.g., “Petition dismissed”).

8. "appellant_advocate": Search for lines like:
   - "For the Petitioners:"
   - "Counsel for Appellant"
   - "Mr. S.D. Lotlikar, Senior Advocate"
   - "Mr. G.S. Gill-AAG with Mr. S.P.S. Rajawa"
   Extract advocate name(s) representing the appellant.

9. "respondent_advocate": Search for lines like:
   - "For the Respondents:"
   - "Counsel for Respondent"
   - "Mr. Karambir Singh Randhawa, Advocate"
   Extract advocate name(s) representing the respondent.

10. "citation": Look for citations in the form of:
   - "2023:BHC-NAG:12345"
   - "Neutral Citation No. - 2025:AHC-LKO:26557-D"
   - "2025:MHC:1515"
   - "2025:HHC:20744"
   Return full citation string if found.

11. "case_type": Use keywords like "Writ Petition", "Civil Appeal", "Criminal Appeal", etc., mentioned with case number.

12. "decided_date": Date when judgment/order was delivered (typically found near judge's name or end of document).

13. "bench_strength": Number of judges on the bench. Infer from number of judges mentioned (e.g., single judge or division bench).

14. "case_status": Final status like "Dismissed", "Allowed", "Pending", "Disposed", etc.

EXTRACTION RULES:
- For appellants/respondents: Extract ONLY the main entity name (remove "having office at", "through its Secretary", addresses, ages, occupations)
- For judges: Extract full name without titles like "Hon'ble", "Justice", "J."
- For advocates: Extract lawyer names without designations like "Senior Advocate", "Additional Government Advocate"
- Handle numbered lists properly (1. Name, 2. Name, etc.)
- Multiple parties should be in arrays, single parties as strings
- Return "none" for fields not found
- Be extremely careful with Indian legal terminology and court hierarchy

EXAMPLES:
- "1. Ankush Shikshan Sanstha, having office at CRPF Gate, through Secretary" → "Ankush Shikshan Sanstha"
- "Hon'ble Mr. Justice Nivedita P. Mehta" → "Nivedita P. Mehta"  
- "HIGH COURT OF JUDICATURE AT BOMBAY, NAGPUR BENCH" → "High Court of Judicature at Bombay"

Return this exact JSON structure:
{{
    "appellants": ["name1", "name2"],
    "respondents": ["name1", "name2"],
    "judge_name": "Judge Full Name",
    "case_number": "2134",
    "case_year": 2022,
    "court_name": "High Court of Judicature at Bombay",
    "court_location": "Nagpur",
    "judgment_type": "Judgment",
    "case_result": "Petition dismissed",
    "appellant_advocate": "Advocate Name",
    "respondent_advocate": "Government Advocate Name",
    "case_type": "Writ Petition",
    "decided_date": "2023-01-15",
    "citation": "2023:BHC-NAG:12345",
    "bench_strength": 1,
    "case_status": "Dismissed"
}}
"""

    def _format_ai_result(self, ai_data: Dict) -> Dict:
        """Format AI result into required structure"""
        
        # Process appellants
        appellants = ai_data.get('appellants', [])
        if isinstance(appellants, list):
            appellant_str = ', '.join(appellants) if appellants else "Appellant"
        else:
            appellant_str = str(appellants) if appellants else "Appellant"
        
        # Process respondents
        respondents = ai_data.get('respondents', [])
        if isinstance(respondents, list):
            respondent_str = ', '.join(respondents) if respondents else "Respondents"
        else:
            respondent_str = str(respondents) if respondents else "Respondents"
        
        # Extract dates
        case_year = ai_data.get('case_year', 2025)
        decided_date = ai_data.get('decided_date', 'none')
        decided_day = "1"
        decided_month = "1"
        decided_year = case_year
        
        if decided_date and decided_date != 'none':
            try:
                from datetime import datetime
                date_obj = datetime.strptime(decided_date, '%Y-%m-%d')
                decided_day = str(date_obj.day)
                decided_month = str(date_obj.month)
                decided_year = date_obj.year
            except:
                pass
        
        # Map court information
        court_info = self._map_court_info(ai_data.get('court_name', ''), ai_data.get('court_location', ''))
        court_info['allJudges'] = ai_data.get('judge_name', 'none')
        
        # Format complete result
        return {
            "docId": 0,
            "appellant": appellant_str,
            "remarkable": "none",
            "respondent": respondent_str,
            "judgeName": ai_data.get('judge_name', 'none'),
            "judgementOrder": "",
            "judgementType": ai_data.get('judgment_type', 'Judgement'),
            "caseResult": ai_data.get('case_result', 'Case outcome to be determined'),
            "doubleCouncilDetailRequest": {
                "advocateForRespondent": ai_data.get('respondent_advocate', 'none'),
                "advocateForAppellant": ai_data.get('appellant_advocate', 'none'),
                "extraCouncilDetails": "none"
            },
            "singleCouncilDetailRequest": None,
            "courtDetailRequest": court_info,
            "citationRequest": {
                "citationCategoryId": 0,
                "journalId": 0,
                "otherCitation": ai_data.get('citation', ''),
                "neutralCitation": ai_data.get('citation', ''),
                "pageNumber": "1",
                "year": case_year,
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
                "caseNumber": str(ai_data.get('case_number', '1')),
                "decidedDay": decided_day,
                "decidedMonth": decided_month,
                "decidedYear": decided_year,
                "notes": "none",
                "year": case_year
            },
            "casesReferredRequestList": [],
            "headNoteRequestList": [],
            "caseTopics": [],
            "success": True,
            "extraction_method": "OpenAI GPT-4",
            "ai_metadata": {
                "case_type": ai_data.get('case_type', 'none'),
                "case_status": ai_data.get('case_status', 'none'),
                "bench_strength": ai_data.get('bench_strength', 1),
                "court_location": ai_data.get('court_location', 'none')
            }
        }

    def _map_court_info(self, court_name: str, location: str) -> Dict:
        """Map court name and location to court IDs"""
        
        court_name_lower = court_name.lower() if court_name else ""
        location_lower = location.lower() if location else ""
        
        # Court mapping based on Indian court hierarchy
        court_mappings = [
            # Supreme Court
            (r'supreme\s+court', {'courtId': 1, 'courtBenchId': 1, 'courtBranchId': '1'}),
            
            # High Courts
            (r'bombay.*high.*court', {'courtId': 19, 'courtBenchId': 3, 'courtBranchId': '43'}),
            (r'delhi.*high.*court', {'courtId': 2, 'courtBenchId': 1, 'courtBranchId': '2'}),
            (r'calcutta.*high.*court', {'courtId': 3, 'courtBenchId': 1, 'courtBranchId': '3'}),
            (r'madras.*high.*court', {'courtId': 4, 'courtBenchId': 1, 'courtBranchId': '4'}),
            (r'gujarat.*high.*court', {'courtId': 5, 'courtBenchId': 1, 'courtBranchId': '5'}),
            (r'punjab.*high.*court', {'courtId': 6, 'courtBenchId': 1, 'courtBranchId': '6'}),
            (r'rajasthan.*high.*court', {'courtId': 7, 'courtBenchId': 1, 'courtBranchId': '7'}),
            (r'kerala.*high.*court', {'courtId': 8, 'courtBenchId': 1, 'courtBranchId': '8'}),
            (r'karnataka.*high.*court', {'courtId': 9, 'courtBenchId': 1, 'courtBranchId': '9'}),
            (r'andhra.*pradesh.*high.*court', {'courtId': 10, 'courtBenchId': 1, 'courtBranchId': '10'}),
            (r'telangana.*high.*court', {'courtId': 11, 'courtBenchId': 1, 'courtBranchId': '11'}),
            (r'orissa.*high.*court', {'courtId': 12, 'courtBenchId': 1, 'courtBranchId': '12'}),
            (r'jharkhand.*high.*court', {'courtId': 13, 'courtBenchId': 1, 'courtBranchId': '13'}),
            (r'chhattisgarh.*high.*court', {'courtId': 14, 'courtBenchId': 1, 'courtBranchId': '14'}),
            (r'uttarakhand.*high.*court', {'courtId': 15, 'courtBenchId': 1, 'courtBranchId': '15'}),
            (r'himachal.*pradesh.*high.*court', {'courtId': 16, 'courtBenchId': 1, 'courtBranchId': '16'}),
            (r'jammu.*kashmir.*high.*court', {'courtId': 17, 'courtBenchId': 1, 'courtBranchId': '17'}),
            (r'guwahati.*high.*court', {'courtId': 18, 'courtBenchId': 1, 'courtBranchId': '18'}),
            
            # Default High Court
            (r'high.*court', {'courtId': 19, 'courtBenchId': 2, 'courtBranchId': '34'}),
        ]
        
        # Default court info
        default_court = {
            "allJudges": "none",
            "courtBenchId": 2,
            "courtBranchId": "34", 
            "courtId": 19
        }
        
        # Find matching court
        for pattern, court_data in court_mappings:
            if re.search(pattern, court_name_lower):
                default_court.update(court_data)
                break
        
        return default_court

    def _extract_with_regex(self, text: str) -> Dict:
        """Fallback regex extraction method"""
        
        logger.info("Using regex fallback extraction")
        
        # Basic regex patterns for fallback
        appellant = self._extract_appellant_regex(text)
        respondent = self._extract_respondent_regex(text)
        judge = self._extract_judge_regex(text)
        case_info = self._extract_case_info_regex(text)
        
        return {
            "docId": 0,
            "appellant": appellant,
            "remarkable": "none",
            "respondent": respondent,
            "judgeName": judge,
            "judgementOrder": "",
            "judgementType": "Judgement",
            "caseResult": "Case outcome to be determined",
            "doubleCouncilDetailRequest": {
                "advocateForRespondent": "none",
                "advocateForAppellant": "none",
                "extraCouncilDetails": "none"
            },
            "singleCouncilDetailRequest": None,
            "courtDetailRequest": {
                "allJudges": judge,
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
                "year": case_info['year'],
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
            "caseHistoryRequest": case_info,
            "casesReferredRequestList": [],
            "headNoteRequestList": [],
            "caseTopics": [],
            "success": True,
            "extraction_method": "Regex fallback"
        }

    def _extract_appellant_regex(self, text: str) -> str:
        """Basic regex appellant extraction"""
        patterns = [
            r'Petitioners?\s*:\s*([A-Z][A-Za-z\s\.&,()-]+?)(?:\n|$)',
            r'([A-Z][A-Za-z\s\.&,()-]+?)\s*\.{3,}\s*Petitioners?',
            r'^\s*\d+\.\s+([A-Z][A-Za-z\s\.&,()-]+?)(?:,\s*(?:having|through|aged))',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return "Appellant"

    def _extract_respondent_regex(self, text: str) -> str:
        """Basic regex respondent extraction"""
        patterns = [
            r'Respondents?\s*:\s*([A-Z][A-Za-z\s\.&,()-]+?)(?:\n|$)',
            r'([A-Z][A-Za-z\s\.&,()-]+?)\s*\.{3,}\s*Respondents?',
            r'[Vv]ersus\s*\n\s*([A-Z][A-Za-z\s\.&,()-]+?)(?=\s*(?:\n|through|$))',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return "Respondents"

    def _extract_judge_regex(self, text: str) -> str:
        """Basic regex judge extraction"""
        patterns = [
            r'HON\'?BLE\s+(?:MR\.|MRS\.|MS\.)?\s*JUSTICE\s+([A-Z][A-Za-z\s\.]+?)(?:\s*,?\s*J\.)?(?:[,\n]|$)',
            r'CORAM\s*:\s*([A-Z][A-Za-z\s\.]+?)(?:\s*,?\s*J\.)?(?:[,\n]|$)',
            r'Before\s*:\s*([A-Z][A-Za-z\s\.]+?)(?:\s*,?\s*J\.)?(?:[,\n]|$)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                judge = match.group(1).strip()
                judge = re.sub(r'(?:HONBLE|HON\'BLE|MR\.|MRS\.|MS\.|JUSTICE)\s*', '', judge, flags=re.IGNORECASE)
                return judge.strip().rstrip(',.')
        
        return "none"

    def _extract_case_info_regex(self, text: str) -> Dict:
        """Basic regex case info extraction"""
        case_info = {
            "caseNumber": "1",
            "decidedDay": "1",
            "decidedMonth": "1", 
            "decidedYear": 2025,
            "notes": "none",
            "year": 2025
        }
        
        # Extract case number and year
        patterns = [
            r'Writ\s+Petition\s+No\.?\s*(\d+)\s*/\s*(\d{4})',
            r'Civil\s+Appeal\s+No\.?\s*(\d+)\s*/\s*(\d{4})',
            r'Criminal\s+Appeal\s+No\.?\s*(\d+)\s*/\s*(\d{4})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                case_number = match.group(1)
                year = int(match.group(2))
                case_info.update({
                    "caseNumber": case_number,
                    "decidedYear": year,
                    "year": year
                })
                break
        
        return case_info

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Fix common Unicode issues
        text = text.replace('\u00a0', ' ')
        text = text.replace('\u2019', "'")
        text = text.replace('\u201c', '"')
        text = text.replace('\u201d', '"')
        text = text.replace('\u2013', '-')
        text = text.replace('\u2014', '-')
        
        return text.strip()

    def _create_error_result(self, error_msg: str) -> Dict:
        """Create error result structure"""
        return {
            "docId": 0,
            "appellant": "Appellant",
            "remarkable": "none", 
            "respondent": "Respondents",
            "judgeName": "none",
            "judgementOrder": "",
            "judgementType": "Judgement",
            "caseResult": "Extraction failed",
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
                "caseNumber": "1",
                "decidedDay": "1",
                "decidedMonth": "1",
                "decidedYear": 2025,
                "notes": "none",
                "year": 2025
            },
            "casesReferredRequestList": [],
            "headNoteRequestList": [],
            "caseTopics": [],
            "success": False,
            "error": error_msg,
            "extraction_method": "Error"
        }

def main():
    """Main function"""
    try:
        # Parse command line arguments
        if '--help' in sys.argv:
            print("Final AI-Powered Legal Document Extractor")
            print("Usage:")
            print("  python final_ai_extractor.py --pdf <file.pdf>")
            print("  python final_ai_extractor.py --image <file.jpg>")
            print("  python final_ai_extractor.py --text <text_content>")
            print("  python final_ai_extractor.py --file <any_file>")
            print("\nEnvironment:")
            print("  Set OPENAI_API_KEY=your_api_key")
            print("\nDependencies:")
            print("  pip install openai PyMuPDF pytesseract pillow")
            sys.exit(0)
        
        # Initialize extractor
        extractor = AILegalDocumentExtractor()
        
        if '--pdf' in sys.argv or '--file' in sys.argv:
            file_index = sys.argv.index('--pdf') if '--pdf' in sys.argv else sys.argv.index('--file')
            if file_index + 1 < len(sys.argv):
                file_path = sys.argv[file_index + 1]
                result = extractor.extract_from_file(file_path)
            else:
                result = extractor._create_error_result("No file path provided")
        
        elif '--image' in sys.argv:
            image_index = sys.argv.index('--image')
            if image_index + 1 < len(sys.argv):
                image_path = sys.argv[image_index + 1]
                result = extractor._extract_from_image(image_path)
            else:
                result = extractor._create_error_result("No image path provided")
        
        elif '--text' in sys.argv:
            text_index = sys.argv.index('--text')
            if text_index + 1 < len(sys.argv):
                text = sys.argv[text_index + 1]
                result = extractor.extract_from_text(text)
            else:
                result = extractor._create_error_result("No text provided")
        
        else:
            # Test with sample
            test_text = """IN THE HIGH COURT OF JUDICATURE AT BOMBAY
NAGPUR BENCH : NAGPUR

Writ Petition No.2134/2022

1. Ankush Shikshan Sanstha, having its office at
   CRPF Gate No.3, Hingna Road, Digdoh Hills,
   Nagpur 440016, through its Secretary.

2. G.H. Raisoni College of Engineering CRPF Gate No.3,
   Hingna Road, Digdoh Hills, Nagpur 440016,
   through its Principal.                          .... Petitioners.

                    - Versus -

1. Rashtrasant Tukdoji Maharaj Nagpur University, Nagpur,
   through its Registrar, Ravindranath Tagore Marg,
   Civil Lines, Nagpur.

2. The Grievance Committee constituted under
   Rashtrasant Tukdoji Maharaj Nagpur University,
   through its Chairman.                           .... Respondents.

CORAM: HON'BLE MR. JUSTICE NIVEDITA P. MEHTA

For Petitioners: Mr. S.D. Lotlikar, Senior Advocate
For Respondents: Ms. Maria Correira, Additional Government Advocate

JUDGMENT: (Per Nivedita P. Mehta, J.)

The petition is dismissed."""
            
            print("Running test with sample legal document", file=sys.stderr)
            result = extractor.extract_from_text(test_text)
        
        # Output result as JSON
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
    except Exception as e:
        error_result = {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "arguments": sys.argv
        }
        print(json.dumps(error_result, ensure_ascii=False))
        sys.exit(1)

if __name__ == "__main__":
    main()