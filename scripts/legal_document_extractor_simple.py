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
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import base64

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# AI Integration
try:
    from openai import OpenAI
    from openai import RateLimitError, APIError, APITimeoutError
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

# Helper for robust high court pattern
import re

def make_high_court_pattern(state):
    # Accepts state as lower-case, e.g. 'patna', 'madhya pradesh'
    # Matches: 'high court ... state' or 'state ... high court', allowing any words/spaces/commas/dashes in between
    return rf'high court\b[^\n]*?{state}\b|{state}\b[^\n]*?high court\b'

class AILegalDocumentExtractor:
    def __init__(self, api_key: str = None, model: str = "gpt-4-0613", max_retries: int = 3):
        self.api_key = api_key or os.environ.get('OPENAI_API_KEY') or self._load_api_key_from_config()
        self.model = model
        self.max_retries = max_retries
        self.rate_limit_reset_time = None
        self.last_api_call_time = None
        self.min_delay_between_calls = 1.0  # Minimum 1 second between calls
        logger.info(f"api_key: {self.api_key[:10]}..." if self.api_key else "No API key")
        if self.api_key and AI_AVAILABLE:
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

    def _wait_for_rate_limit_reset(self):
        """Wait until rate limit reset time if we're currently rate limited"""
        if self.rate_limit_reset_time and datetime.now() < self.rate_limit_reset_time:
            wait_seconds = (self.rate_limit_reset_time - datetime.now()).total_seconds()
            if wait_seconds > 0:
                logger.info(f"Waiting {wait_seconds:.1f} seconds for rate limit reset...")
                time.sleep(wait_seconds)
                self.rate_limit_reset_time = None

    def _enforce_min_delay(self):
        """Enforce minimum delay between API calls"""
        if self.last_api_call_time:
            elapsed = (datetime.now() - self.last_api_call_time).total_seconds()
            if elapsed < self.min_delay_between_calls:
                sleep_time = self.min_delay_between_calls - elapsed
                logger.debug(f"Enforcing minimum delay: {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
        self.last_api_call_time = datetime.now()

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

            # --- Find caseResult from last paragraphs/lines ---
            last_case_result = None
            # Canonical mapping for result phrases
            result_map = [
                ("dismissed", "Petition dismissed"),
                ("allowed", "Petition allowed"),
                ("disposed of", "Disposed of"),
                ("order accordingly", "Order accordingly")
            ]
            import re
            # Split into paragraphs (by double newlines or by period)
            paragraphs = [p.strip() for p in re.split(r'\n\s*\n|(?<=\.)\s*\n', text) if p.strip()]
            # Also check last 5 lines for extra robustness
            lines = [l.strip() for l in text.split('\n') if l.strip()]
            # Check last 5 paragraphs, then last 5 lines
            search_blocks = (paragraphs[-5:] if len(paragraphs) >= 5 else paragraphs) + (lines[-5:] if len(lines) >= 5 else lines)
            found = False
            for block in search_blocks[::-1]:  # Search from last to first
                block_lower = block.lower()
                for key, canonical in result_map:
                    if key in block_lower:
                        last_case_result = canonical
                        found = True
                        break
                if found:
                    break
            # Extract as usual
            result = self.extract_from_text(text)
            # Strictly enforce allowed caseResult values
            if last_case_result:
                result["caseResult"] = last_case_result
            else:
                result["caseResult"] = "none"
            return result
            
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

    def extract_from_text(self, text: str, use_ai: bool = True) -> Dict:
        """Extract all legal metadata using AI or regex"""
        
        if not text or not text.strip():
            logger.error("No text content provided to extract_from_text")
            return self._create_error_result("No text content provided")
        
        # Clean and prepare text
        text = self._clean_text(text)
        
        logger.info(f"Processing text of length: {len(text)}")
        
        # Try to extract referred cases with AI if available
        case_referred = []
        if use_ai and self.api_key and AI_AVAILABLE:
            logger.info("Trying to extract referred cases with AI...")
            case_referred = self._extract_referred_cases_with_ai(text)
            logger.info(f"AI case_referred: {case_referred}")
        if not case_referred:
            logger.info("Falling back to regex for case_referred...")
            case_referred = self._extract_case_referred(text)
            logger.info(f"Regex case_referred: {case_referred}")
        
        # Try to extract judge name with AI if available
        judge_name = None
        if use_ai and self.api_key and AI_AVAILABLE:
            logger.info("Trying to extract judge name with AI...")
            judge_name = self._extract_judge_name_with_ai(text)
            logger.info(f"AI judge_name: {judge_name}")
        if not judge_name or judge_name == "none":
            logger.info("Falling back to regex for judge_name...")
            judge_name = self._extract_judge_regex(text)
            logger.info(f"Regex judge_name: {judge_name}")
        
        # Check if we should avoid AI due to recent rate limiting
        if use_ai and self.api_key and AI_AVAILABLE:
            # Wait for rate limit reset if needed
            self._wait_for_rate_limit_reset()
            
            # Check API status first to avoid unnecessary calls
            api_status = self.check_api_status()
            logger.info(f"API status: {api_status}")
            if api_status.get('status') == 'rate_limited':
                logger.warning("API is currently rate limited, using regex extraction")
                use_ai = False
            else:
                logger.info("Calling _extract_with_openai...")
                ai_result = self._extract_with_openai(text)
                logger.info(f"AI extraction result: {ai_result}")
                if ai_result and ai_result.get('success', False):
                    ai_result['caseReferred'] = case_referred
                    ai_result['judge_name'] = judge_name
                    logger.info("Returning AI extraction result.")
                    return ai_result
                else:
                    logger.warning("AI extraction did not return a usable result, falling back to regex.")
        
        # Use regex extraction
        logger.info("Using regex extraction")
        result = self._extract_with_regex(text)
        result['caseReferred'] = case_referred
        result['judge_name'] = judge_name
        logger.info(f"Regex extraction result: {result}")
        return result

    def _chat_with_retry(self, messages: List[Dict], max_retries: int = None) -> Dict:
        """Execute OpenAI chat completion with improved exponential backoff retry logic"""
        max_retries = max_retries or self.max_retries
        
        # Enforce minimum delay between calls
        self._enforce_min_delay()
        
        for attempt in range(max_retries + 1):  # +1 to include initial attempt
            try:
                # Instantiate OpenAI client with retry disabled to avoid conflicts
                client = OpenAI(
                    api_key=self.api_key,
                    max_retries=0  # Disable OpenAI's built-in retries
                ) if self.api_key else OpenAI(max_retries=0)
                
                logger.info(f"OpenAI API call attempt {attempt + 1}/{max_retries + 1}")
                
                # Call OpenAI API using new v1.x syntax
                response = client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.1,
                    max_tokens=2000  # Increased for better responses
                )
                
                return response
                
            except RateLimitError as e:
                # Extract retry-after header if available
                retry_after = getattr(e, 'retry_after', None)
                if retry_after:
                    wait_time = int(retry_after)
                    logger.warning(f"Rate limit hit with retry-after header: {wait_time} seconds")
                    # Set rate limit reset time
                    self.rate_limit_reset_time = datetime.now() + timedelta(seconds=wait_time)
                else:
                    wait_time = self._get_retry_delay(attempt, "rate_limit")
                    logger.warning(f"Rate limit hit (attempt {attempt + 1}/{max_retries + 1}). Retrying in {wait_time} seconds...")
                    # Set rate limit reset time based on exponential backoff
                    self.rate_limit_reset_time = datetime.now() + timedelta(seconds=wait_time)
                
                if attempt < max_retries:
                    time.sleep(wait_time)
                else:
                    logger.error("Max retries exceeded for rate limiting")
                    raise e
                
            except (APIError, APITimeoutError) as e:
                wait_time = self._get_retry_delay(attempt, "api_error")
                logger.warning(f"API error (attempt {attempt + 1}/{max_retries + 1}): {e}. Retrying in {wait_time} seconds...")
                
                if attempt < max_retries:
                    time.sleep(wait_time)
                else:
                    logger.error("Max retries exceeded for API errors")
                    raise e
                
            except (ConnectionError, TimeoutError) as e:
                wait_time = self._get_retry_delay(attempt, "timeout")
                logger.warning(f"Connection/Timeout error (attempt {attempt + 1}/{max_retries + 1}): {e}. Retrying in {wait_time} seconds...")
                
                if attempt < max_retries:
                    time.sleep(wait_time)
                else:
                    logger.error("Max retries exceeded for connection errors")
                    raise e
                
            except Exception as e:
                logger.error(f"Unexpected error in OpenAI call (attempt {attempt + 1}/{max_retries + 1}): {e}")
                if not self._should_retry_error(e) or attempt == max_retries:
                    raise e
                wait_time = self._get_retry_delay(attempt, "general")
                time.sleep(wait_time)
        
        raise Exception(f"Max retries ({max_retries}) exceeded due to rate limiting or API errors.")

    def _should_retry_error(self, error: Exception) -> bool:
        """Determine if an error should trigger a retry"""
        retryable_errors = (
            RateLimitError,
            APIError,
            APITimeoutError,
            ConnectionError,
            TimeoutError
        )
        return isinstance(error, retryable_errors)

    def _get_retry_delay(self, attempt: int, error_type: str = "general") -> int:
        """Calculate retry delay with exponential backoff and caps"""
        base_delay = 2 ** attempt
        
        # Different caps for different error types
        caps = {
            "rate_limit": 120,  # Increased cap for rate limits
            "api_error": 60,    # Increased cap for API errors
            "timeout": 30,      # Increased cap for timeouts
            "general": 15       # Increased cap for general errors
        }
        
        cap = caps.get(error_type, caps["general"])
        delay = min(base_delay, cap)
        
        # Add jitter to prevent thundering herd
        import random
        jitter = random.uniform(0.8, 1.2)
        return int(delay * jitter)

    def check_api_status(self) -> Dict:
        """Check current API status and usage limits"""
        try:
            # Don't check if we're currently rate limited
            if self.rate_limit_reset_time and datetime.now() < self.rate_limit_reset_time:
                return {
                    "status": "rate_limited",
                    "retry_after": (self.rate_limit_reset_time - datetime.now()).total_seconds(),
                    "message": "Rate limit active"
                }
            
            client = OpenAI(api_key=self.api_key, max_retries=0)
            
            # Try a simple API call to check status
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            
            return {
                "status": "available",
                "model": "gpt-3.5-turbo",
                "response": "API is working"
            }
            
        except RateLimitError as e:
            retry_after = getattr(e, 'retry_after', None)
            if retry_after:
                self.rate_limit_reset_time = datetime.now() + timedelta(seconds=int(retry_after))
            return {
                "status": "rate_limited",
                "retry_after": retry_after,
                "error": str(e)
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def extract_batch(self, texts: List[str], delay_between_requests: float = 2.0) -> List[Dict]:
        """Extract from multiple texts with improved rate limiting considerations"""
        results = []
        
        for i, text in enumerate(texts):
            logger.info(f"Processing document {i + 1}/{len(texts)}")
            
            try:
                # Wait for rate limit reset if needed
                self._wait_for_rate_limit_reset()
                
                result = self.extract_from_text(text)
                results.append(result)
                
                # Add delay between requests to avoid rate limiting
                if i < len(texts) - 1: # Don't delay after the last request
                    logger.info(f"Waiting {delay_between_requests} seconds before next request...")
                    time.sleep(delay_between_requests)
                    
            except Exception as e:
                logger.error(f"Failed to process document {i + 1}: {e}")
                error_result = self._create_error_result(f"Batch processing failed: {str(e)}")
                results.append(error_result)
        
        return results

    def _extract_with_openai(self, text: str) -> Dict:
        """Use OpenAI GPT-4 for comprehensive legal metadata extraction"""
        try:
            logger.info("Preparing OpenAI prompt and messages...")
            # Create comprehensive prompt
            prompt = self._create_comprehensive_prompt(text)
            
            # Prepare messages for OpenAI
            messages = [
                {
                    "role": "system",
                    "content": "You are an expert legal document analyzer with deep knowledge of Indian legal document formats, court structures, and legal terminology. Extract information with 100% accuracy and return only valid JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            # Call OpenAI with retry logic
            response = self._chat_with_retry(messages)
            result_text = response.choices[0].message.content.strip()
            logger.info(f"Raw OpenAI response: {result_text}")
            print(f"[OpenAI RAW RESPONSE] {result_text}", file=sys.stderr)

            # Extract JSON from response
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                result_text = json_match.group(0)

            # Parse and validate result
            ai_data = json.loads(result_text)
            logger.info(f"Parsed OpenAI JSON: {ai_data}")

            # Convert to required format
            formatted_result = self._format_ai_result(ai_data)
            logger.info(f"Formatted OpenAI extraction result: {formatted_result}")

            logger.info("OpenAI extraction successful")
            logger.info(f"Extracted - Appellant: {formatted_result['appellant']}")
            logger.info(f"Extracted - Respondent: {formatted_result['respondent']}")
            logger.info(f"Extracted - Judge: {formatted_result['judgeName']}")

            return formatted_result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OpenAI JSON: {e}")
            logger.error(f"Raw response: {result_text[:500]}")
            return None

        except RateLimitError as e:
            logger.error(f"Rate limit exceeded after all retries: {e}")
            logger.error("Suggestions:")
            logger.error("1. Wait a few minutes before trying again")
            logger.error("2. Check your OpenAI API usage at https://platform.openai.com/usage")
            logger.error("3. Consider upgrading your plan if you're hitting limits frequently")
            logger.error("4. Use --check-api to verify current API status")
            return None

        except (APIError, APITimeoutError) as e:
            logger.error(f"OpenAI API error after all retries: {e}")
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

1. "appellants": Look for words like "Appellant", "Petitioner", or "Petitioners" or "Applicants" — these are mostly found on the first page. There can be multiple names, so return them in an array format. Extract only the main entity names (e.g., remove address, "through Secretary", etc.).

2. "respondents": Look for words like "Respondent" or "Respondents", also typically on the first page. Extract all respondent names in an array. Same as appellants, extract only the main names.

3. "judge_name": Check for presence of "Judgment" or "Order" in the document. Judge names are often mentioned in dedicated paragraphs or at the end of the document like "(ANIL KSHETARPAL) JUDGE". Extract the full name of the judge, excluding prefixes like "Justice", "Hon'ble", etc.

4. "case_number", "case_year", "notes": Extract from lines such as:
   - "WRIT C No. 2373 of 2024"
   - "Case :- APPEAL UNDER SECTION 37... DEFECTIVE No. - 9 of 2025"
   - "MATA No. 272 of 2023"
   - "CR-3041 of 2025(O&M)"
   Use natural language understanding to identify the number and year. These are mostly on the first page. If not found, return "none" for both. Return these lines as "notes".

5. "court_name": Try to find the exact court name using your knowledge. This info often appears on the first or last page. Examples:
   - "SUPREME COURT OF INDIA"
   - "HIGH COURT OF JUDICATURE AT BOMBAY, NAGPUR BENCH"
   - "IN THE HIGH COURT OF JUDICATURE AT PATNA"
   - "IN THE HIGH COURT AT CALCUTTA"
6. "judgment_type": Understand whether the document contains a "Judgment" or an "Order". Sometimes it is titled clearly (e.g., "JUDGMENT") or inferred from judge's written decision. Use your reasoning to classify correctly.

7. "case_result": If there's a heading like "JUDGMENT" or "ORDER", extract the paragraph(s) directly under it. If not, summarize the final decision from the document (e.g., "Petition dismissed or dismissed").

8. "appellant_advocate": Search for lines like:
   - "For the Petitioners:"
   - "Counsel for Appellant"
   - "For the applicants:"
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

15. "caseReferred": Extract all references like '<partyName>, reported in <caseNo>' from text, and add as array of {{caseNo, partyName}} objects to output.

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
- "IN THE HIGH COURT OF JUDICATURE AT BOMBAY BENCH AT AURANGABAD" → "High Court of Judicature at Bombay"
- "Ravinder Kaur & another\nState of Uttarakhand & another\nPresence:\n...Applicants\nVersus\n...Respondents" → "appellants": ["Ravinder Kaur & another"], "respondents": ["State of Uttarakhand & another"]

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
    "case_status": "Dismissed",
    "caseReferred": [{{"caseNo": "2023:BHC-NAG:12345", "partyName": "Ankush Shikshan Sanstha"}}]
}}
"""

    def _format_ai_result(self, ai_data: Dict) -> Dict:
        """Format AI result into required structure"""
        
        # Process appellants
        appellants = ai_data.get('appellants') or ai_data.get('appellant') or []
        if isinstance(appellants, list):
            appellant_str = ', '.join(appellants) if appellants else "Appellant"
        else:
            appellant_str = str(appellants) if appellants else "Appellant"
        
        # Process respondents
        respondents = ai_data.get('respondents') or ai_data.get('respondent') or []
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
        
        # --- Judge formatting logic ---
        raw_judge = ai_data.get('judge_name', 'none')
        # Split by comma for multiple judges, strip whitespace
        judge_names = [j.strip() for j in raw_judge.split(',') if j.strip()] if raw_judge and raw_judge != 'none' else []
        
        if len(judge_names) > 1:
            # Multiple judges
            formatted_all_judges = ', '.join([f"Hon'ble {j}" for j in judge_names]) + " JJ."
            formatted_judge_name = f"Hon'ble {judge_names[0]} J."
        elif len(judge_names) == 1:
            formatted_all_judges = f"Hon'ble {judge_names[0]} J."
            formatted_judge_name = f"Hon'ble {judge_names[0]} J."
        else:
            formatted_all_judges = 'none'
            formatted_judge_name = 'none'
        
        # Map court information
        court_info = self._map_court_info(ai_data.get('court_name', ''), None)
        court_info['allJudges'] = formatted_all_judges

        # Extract caseReferred from ai_data if present, else fallback to regex
        case_referred = ai_data.get('caseReferred')
        if not case_referred:
            case_referred = []
        # Defensive: ensure each item is a dict with 'caseNo' and 'partyName'
        validated_case_referred = []
        for item in case_referred:
            try:
                if isinstance(item, dict):
                    if 'caseNo' not in item:
                        print(f"[format_ai_result] MISSING 'caseNo' in item: {item}", file=sys.stderr)
                    print(f"[format_ai_result] item.get('caseNo'): {item.get('caseNo', '')}", file=sys.stderr)
                    validated_case_referred.append({
                        'caseNo': item.get('caseNo', ''),
                        'partyName': item.get('partyName', '')
                    })
                else:
                    print(f"[format_ai_result] item (not dict): {item}", file=sys.stderr)
                    validated_case_referred.append({'caseNo': '', 'partyName': str(item)})
            except Exception as err:
                print(f"[format_ai_result] Exception processing item: {item}, error: {err}", file=sys.stderr)
                continue
        citation = ai_data.get('citation', '')
        # Format complete result
        return {
            "docId": 0,
            "appellant": appellant_str,
            "remarkable": "none",
            "respondent": respondent_str,
            "judgeName": formatted_judge_name,
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
                "otherCitation": citation,
                "neutralCitation": citation,
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
                "notes": ai_data.get('notes', 'none'),
                "year": case_year
            },
            "headNoteRequestList": [],
            "caseTopics": [],
            "success": True,
            "extraction_method": "OpenAI GPT-4",
            "ai_metadata": {
                "case_type": ai_data.get('case_type', 'none'),
                "case_status": ai_data.get('case_status', 'none'),
                "bench_strength": ai_data.get('bench_strength', 1)
            },
            "caseReferred": validated_case_referred
        }

    def _map_court_info(self, court_name: str, location: str) -> Dict:
        """Map court name and location to court IDs"""
        
        court_name_lower = court_name.lower() if court_name else ""
        location_lower = location.lower() if location else ""
        
        # Court mapping based on Indian court hierarchy
        court_mappings = [
            (make_high_court_pattern('madhya pradesh'), {'courtId': 19, 'courtBenchId': 1, 'courtBranchId': '54', 'citationCategory': 'MP'}),
            (make_high_court_pattern('bombay'), {'courtId': 19, 'courtBenchId': 1, 'courtBranchId': '43', 'citationCategory': 'Bom'}),
            (make_high_court_pattern('delhi'), {'courtId': 19, 'courtBenchId': 1, 'courtBranchId': '46', 'citationCategory': 'Del'}),
            (make_high_court_pattern('calcutta'), {'courtId': 19, 'courtBenchId': 1, 'courtBranchId': '44', 'citationCategory': 'Cal'}),
            (make_high_court_pattern('andhra pradesh'), {'courtId': 19, 'courtBenchId': 1, 'courtBranchId': '42', 'citationCategory': 'AP'}),
            (make_high_court_pattern('gauhati'), {'courtId': 19, 'courtBenchId': 1, 'courtBranchId': '47', 'citationCategory': 'Gau'}),
            (make_high_court_pattern('guwahati'), {'courtId': 19, 'courtBenchId': 1, 'courtBranchId': '47', 'citationCategory': 'Gau'}),
            (make_high_court_pattern('uttarakhand'), {'courtId': 19, 'courtBenchId': 1, 'courtBranchId': '65', 'citationCategory': 'Utt'}),
            (make_high_court_pattern('sikkim'), {'courtId': 19, 'courtBenchId': 1, 'courtBranchId': '62', 'citationCategory': 'Sikk'}),
            (make_high_court_pattern('tripura'), {'courtId': 19, 'courtBenchId': 1, 'courtBranchId': '64', 'citationCategory': 'Tri'}),
            (make_high_court_pattern('patna'), {'courtId': 19, 'courtBenchId': 1, 'courtBranchId': '59', 'citationCategory': 'Pat'}),
            (make_high_court_pattern('manipur'), {'courtId': 19, 'courtBenchId': 1, 'courtBranchId': '56', 'citationCategory': 'Mani'}),
            (make_high_court_pattern('punjab'), {'courtId': 19, 'courtBenchId': 1, 'courtBranchId': '60', 'citationCategory': 'P&H'}),
            (make_high_court_pattern('haryana'), {'courtId': 19, 'courtBenchId': 1, 'courtBranchId': '60', 'citationCategory': 'P&H'}),
            (make_high_court_pattern('madras'), {'courtId': 19, 'courtBenchId': 1, 'courtBranchId': '55', 'citationCategory': 'Mad'}),
            (make_high_court_pattern('jammu'), {'courtId': 19, 'courtBenchId': 1, 'courtBranchId': '50', 'citationCategory': 'J&K'}),
            (make_high_court_pattern('kashmir'), {'courtId': 19, 'courtBenchId': 1, 'courtBranchId': '50', 'citationCategory': 'J&K'}),
            (make_high_court_pattern('jharkhand'), {'courtId': 19, 'courtBenchId': 1, 'courtBranchId': '51', 'citationCategory': 'Jhar'}),
            (make_high_court_pattern('himachal pradesh'), {'courtId': 19, 'courtBenchId': 1, 'courtBranchId': '49', 'citationCategory': 'HP'}),
            (make_high_court_pattern('karnataka'), {'courtId': 19, 'courtBenchId': 1, 'courtBranchId': '52', 'citationCategory': 'Kar'}),
            (make_high_court_pattern('chhattisgarh'), {'courtId': 19, 'courtBenchId': 1, 'courtBranchId': '45', 'citationCategory': 'Chh'}),
            (make_high_court_pattern('kerala'), {'courtId': 19, 'courtBenchId': 1, 'courtBranchId': '53', 'citationCategory': 'Ker'}),
            (make_high_court_pattern('rajasthan'), {'courtId': 19, 'courtBenchId': 1, 'courtBranchId': '61', 'citationCategory': 'Raj'}),
            (make_high_court_pattern('orissa'), {'courtId': 19, 'courtBenchId': 1, 'courtBranchId': '58', 'citationCategory': 'Ori'}),
            (make_high_court_pattern('telangana'), {'courtId': 19, 'courtBenchId': 1, 'courtBranchId': '63', 'citationCategory': 'Tel'}),
            (make_high_court_pattern('meghalaya'), {'courtId': 19, 'courtBenchId': 1, 'courtBranchId': '57', 'citationCategory': 'Megh'}),
            (make_high_court_pattern('gujarat'), {'courtId': 19, 'courtBenchId': 1, 'courtBranchId': '48', 'citationCategory': 'Guj'}),
            (make_high_court_pattern('allahabad'), {'courtId': 19, 'courtBenchId': 1, 'courtBranchId': '41', 'citationCategory': 'All'}),
            # Supreme Court
            (r'supreme court.*of india|supreme court of india', {'courtId': 1, 'courtBenchId': 1, 'courtBranchId': '34', 'citationCategory': 'SC'}),
        ]
        
        # Default court info
        default_court = {
            "allJudges": "none",
            "courtBenchId": 1,
            "courtBranchId": "34", 
            "courtId": 1,
            "citationCategory": ""
        }
        print(f"[map_court_info] court_name_lower: {court_name_lower}", file=sys.stderr)
        print(f"[map_court_info] location_lower: {location_lower}", file=sys.stderr)
        # Special handling for Bombay High Court, Aurangabad Bench
        if 'bombay' in court_name_lower and 'bench at aurangabad' in court_name_lower:
            default_court.update({'courtId': 19, 'courtBenchId': 1, 'courtBranchId': '43', 'citationCategory': 'Bom'})
            return default_court
        
        # Find matching court
        for pattern, court_data in court_mappings:
            if re.search(pattern, court_name_lower, re.IGNORECASE):
                default_court.update(court_data)
                break
        print(f"[map_court_info] default_court: {default_court}", file=sys.stderr)
        return default_court

    def _extract_with_regex(self, text: str) -> Dict:
        """Fallback regex extraction method"""
        
        logger.info("Using regex fallback extraction")
        
        # Basic regex patterns for fallback
        appellant = self._extract_appellant_regex(text)
        respondent = self._extract_respondent_regex(text)
        judge = self._extract_judge_regex(text)
        case_info = self._extract_case_info_regex(text)
        case_referred = self._extract_case_referred(text)
        
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
                "courtBenchId": 1,
                "courtBranchId": "34",
                "courtId": 1,
                "citationCategory": ""
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
            "headNoteRequestList": [],
            "caseTopics": [],
            "success": True,
            "extraction_method": "Regex fallback",
            "caseReferred": case_referred
        }

    def _extract_appellant_regex(self, text: str) -> str:
        """Robust regex appellant extraction supporting Versus and traditional patterns"""
        # Try all patterns in order, return first match
        patterns = [
            # Versus pattern (party before Versus)
            r'^([A-Z][A-Za-z &.]+?)\s*\n.*?Versus',
            # Traditional patterns
            r'Petitioners?\s*:\s*([A-Z][A-Za-z\s\.&(),-]+?)(?:\n|$)',
            r'([A-Z][A-Za-z\s\.&(),-]+?)\s*\.{3,}\s*Petitioners?',
            r'Applicants?\s*:\s*([A-Z][A-Za-z\s\.&(),-]+?)(?:\n|$)',
            r'([A-Z][A-Za-z\s\.&(),-]+?)\s*\.{3,}\s*Applicants?',
            r'^\s*\d+\.\s+([A-Z][A-Za-z\s\.&(),-]+?)(?:,\s*(?:having|through|aged))',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()
        return "Appellant"

    def _extract_respondent_regex(self, text: str) -> str:
        """Robust regex respondent extraction supporting Versus and traditional patterns"""
        # Try all patterns in order, return first match
        patterns = [
            # Versus pattern (party after Versus)
            r'Versus\s*\n([A-Z][A-Za-z &.]+)',
            # Traditional patterns
            r'Respondents?\s*:\s*([A-Z][A-Za-z\s\.&(),-]+?)(?:\n|$)',
            r'([A-Z][A-Za-z\s\.&(),-]+?)\s*\.{3,}\s*Respondents?',
            r'[Vv]ersus\s*\n\s*([A-Z][A-Za-z\s\.&(),-]+?)(?=\s*(?:\n|through|$))',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE | re.DOTALL)
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
        import re
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                judge = match.group(1).strip()
                judge = re.sub(r'(?:HONBLE|HON\'BLE|MR\.|MRS\.|MS\.|JUSTICE)\s*', '', judge, flags=re.IGNORECASE)
                # Remove trailing ', J.', ', J. (Oral)', ', J. (...)', etc.
                judge = re.sub(r',?\s*J\.?(\s*\([^)]*\))?$', '', judge, flags=re.IGNORECASE)
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
            r'(Writ\s+Petition\s+No\.?\s*\d+\s*/\s*\d{4}[^\n]*)',
            r'(Civil\s+Appeal\s+No\.?\s*\d+\s*/\s*\d{4}[^\n]*)',
            r'(Criminal\s+Appeal\s+No\.?\s*\d+\s*/\s*\d{4}[^\n]*)',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                full_sentence = match.group(1).strip()
                # Try to extract number and year from the matched sentence
                num_year_match = re.search(r'(\d+)\s*/\s*(\d{4})', full_sentence)
                if num_year_match:
                    case_number = num_year_match.group(1)
                    year = int(num_year_match.group(2))
                    case_info.update({
                        "caseNumber": case_number,
                        "decidedYear": year,
                        "year": year,
                        "notes": full_sentence
                    })
                else:
                    case_info["notes"] = full_sentence
                break
        
        return case_info

    def _extract_case_referred(self, text: str) -> list:
        """Extract case references for Indian legal citations: partyName, (caseNo) with or without extra text after the citation."""
        # Pattern: Party names (up to comma), (caseNo) [accepts extra text after citation, but only captures citation]
        pattern = re.compile(
            r'([A-Z][A-Za-z0-9\s\-\.\(\)]+?\b(?:v\.?|vs\.?|Vs\.?|VS\.?|\-vs\-)[A-Z][A-Za-z0-9\s\-\.\(\)]+?)\s*,\s*\(([^)]*)\)',
            re.IGNORECASE
        )
        results = []
        for match in pattern.findall(text):
            if isinstance(match, tuple) and len(match) == 2:
                party, case_no = match
            else:
                party, case_no = match, ''
            # Clean up partyName and case_no
            party = party.strip(' .,:;\n\t')
            case_no = case_no.strip(' .,:;\n\t')
            # Add parentheses back to case_no
            case_no_val = f'({case_no})' if case_no else ''
            print(f"[extract_case_referred] case_no: {case_no_val}", file=sys.stderr)
            results.append({
                "caseNo": case_no_val if case_no_val else '',
                "partyName": party if party else ''
            })
        # Deduplicate by (caseNo, partyName)
        seen = set()
        unique_results = []
        for item in results:
            print(f"[extract_case_referred] item['caseNo']: {item['caseNo']}", file=sys.stderr)
            key = (item["caseNo"].lower(), item["partyName"].lower())
            if key not in seen:
                unique_results.append(item)
                seen.add(key)
        return unique_results

    def _extract_referred_cases_with_ai(self, text: str) -> list:
        """Use OpenAI to extract all referred cases as a list of {partyName, caseNo}"""
        if not (self.api_key and AI_AVAILABLE):
            return []
        prompt = (
            "Extract all the cases referred to by the judge in the following Indian court order. For each referred case, return an object with:\n"
            "- 'partyName': the full party names (e.g., 'Union of India and others vs Tarsem Singh')\n"
            "- 'caseNo': the citation (e.g., '(2008) 8 SCC 648' or '2023 SCC Online SC 521')\n"
            "Return a JSON array. If no referred cases, return an empty array.\n"
            "Examples:\n"
            "- 'Union of India and others vs Tarsem Singh, reported in (2008) 8 SCC 648'\n"
            "  → { 'partyName': 'Union of India and others vs Tarsem Singh', 'caseNo': '(2008) 8 SCC 648' }\n"
            "- 'Ameer Minhaj v. Dierdre Elizabeth (Wright) Issar, (2018) 7 SCC 639'\n"
            "  → { 'partyName': 'Ameer Minhaj v. Dierdre Elizabeth (Wright) Issar', 'caseNo': '(2018) 7 SCC 639' }\n"
            "- 'Ramisetty Venkatanna and another vs. Nasyam Jamal Saheb and ors. 2023 SCC Online SC 521'\n"
            "  → { 'partyName': 'Ramisetty Venkatanna and another vs. Nasyam Jamal Saheb and ors.', 'caseNo': '2023 SCC Online SC 521' }\n"
            "- 'the case of Neeharika, Limited Vs. State of Maharashtra and others reported in (2021) 19 SCC 401'\n"
            "  → { 'partyName': 'Neeharika, Limited Vs. State of Maharashtra and others', 'caseNo': '(2021) 19 SCC 401' }\n"
            "- 'Jugraj Singh -vs- Labh Singh, reported in (1995) 2 SCC 31'\n"
            "  → { 'partyName': 'Jugraj Singh -vs- Labh Singh', 'caseNo': '(1995) 2 SCC 31' }\n"
            "- 'Internet and Mobile Association of India Vs. Reserve Bank of India, (2020) 10 SCC 274'\n"
            "  → { 'partyName': 'Internet and Mobile Association of India Vs. Reserve Bank of India', 'caseNo': '(2020) 10 SCC 274' }\n"
            "\nTEXT:\n" + text + "\n\nReturn only the JSON array."
        )
        messages = [
            {"role": "system", "content": "You are an expert legal document analyzer."},
            {"role": "user", "content": prompt}
        ]
        try:
            response = self._chat_with_retry(messages)
            result_text = response.choices[0].message.content.strip()
            # Extract JSON array from response
            import json
            json_match = re.search(r'\[.*\]', result_text, re.DOTALL)
            if json_match:
                result_text = json_match.group(0)
            cases = json.loads(result_text)
            # Validate structure
            valid_cases = []
            if isinstance(cases, list):
                for c in cases:
                    if not isinstance(c, dict):
                        logger.error(f"[extract_referred_cases_with_ai] NOT A DICT: {c}")
                        continue
                    case_no = c.get('caseNo', '')
                    party_name = c.get('partyName', '')
                    if not case_no:
                        logger.error(f"[extract_referred_cases_with_ai] MISSING 'caseNo': {c}")
                    if not party_name:
                        logger.error(f"[extract_referred_cases_with_ai] MISSING 'partyName': {c}")
                    valid_cases.append({'caseNo': case_no, 'partyName': party_name})
                return valid_cases
            return []
        except Exception as e:
            logger.error(f"OpenAI referred cases extraction failed: {e}")
            return []

    def _extract_judge_name_with_ai(self, text: str) -> str:
        """Use OpenAI to extract the full judge name as it appears in the order, e.g., 'Hon'ble Pankaj Purohit, J. (Oral)'"""
        if not (self.api_key and AI_AVAILABLE):
            return "none"
        prompt = (
            "Extract the full name of the judge who authored or delivered the order or judgment in the following Indian court document. "
            "Return the name exactly as it appears in the order, including any honorifics and suffixes (e.g., ', J.' or ', J. (Oral)'). "
            "If there are multiple judges, return all names as a comma-separated string, as they appear in the document. "
            "If no judge name is found, return 'none'.\n\n"
            "Examples:\n"
            "- 'Hon'ble Pankaj Purohit, J. (Oral)'\n"
            "- 'Hon'ble Nivedita P. Mehta, J.'\n"
            "- 'Hon'ble A. B. Smith, J.'\n"
            "- 'Hon'ble S. K. Kaul and Hon'ble M. M. Sundresh, JJ.'\n"
            "\nTEXT:\n" + text + "\n\nReturn only the judge name string."
        )
        messages = [
            {"role": "system", "content": "You are an expert legal document analyzer."},
            {"role": "user", "content": prompt}
        ]
        try:
            response = self._chat_with_retry(messages)
            result_text = response.choices[0].message.content.strip()
            # Only return the first line (in case of extra explanation)
            return result_text.split('\n')[0].strip() if result_text else "none"
        except Exception as e:
            logger.error(f"OpenAI judge name extraction failed: {e}")
            return "none"

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
                "courtBenchId": 1,
                "courtBranchId": "34",
                "courtId": 1,
                "citationCategory": ""
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
            print("  python legal_document_extractor_simple.py --pdf <file.pdf>")
            print("  python legal_document_extractor_simple.py --image <file.jpg>")
            print("  python legal_document_extractor_simple.py --text <text_content>")
            print("  python legal_document_extractor_simple.py --file <any_file>")
            print("  python legal_document_extractor_simple.py --check-api")
            print("  python legal_document_extractor_simple.py --regex-only <file>")
            print("  python legal_document_extractor_simple.py --no-ai <file>")
            print("\nEnvironment:")
            print("  Set OPENAI_API_KEY=your_api_key")
            print("\nDependencies:")
            print("  pip install openai PyMuPDF pytesseract pillow")
            print("\nFeatures:")
            print("  - Automatic retry with exponential backoff for rate limiting")
            print("  - Handles API errors, timeouts, and connection issues")
            print("  - Configurable retry attempts (default: 5)")
            print("  - Batch processing with rate limiting considerations")
            print("  - API status checking")
            print("  - Regex-only mode to avoid API calls")
            print("  - Smart rate limit detection")
            sys.exit(0)
        
        # Initialize extractor with custom retry settings
        extractor = AILegalDocumentExtractor(max_retries=2)
        
        # Check API status if requested
        if '--check-api' in sys.argv:
            print("Checking OpenAI API status...")
            status = extractor.check_api_status()
            print(json.dumps(status, indent=2))
            sys.exit(0)
        
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
        
        elif '--regex-only' in sys.argv:
            regex_index = sys.argv.index('--regex-only')
            if regex_index + 1 < len(sys.argv):
                file_path = sys.argv[regex_index + 1]
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        text = f.read()
                    result = extractor.extract_from_text(text, use_ai=False)
                else:
                    result = extractor._create_error_result(f"File not found: {file_path}")
            else:
                result = extractor._create_error_result("No file path provided for regex-only mode")
        
        elif '--no-ai' in sys.argv:
            no_ai_index = sys.argv.index('--no-ai')
            if no_ai_index + 1 < len(sys.argv):
                file_path = sys.argv[no_ai_index + 1]
                result = extractor.extract_from_file(file_path)
                # Force regex mode by modifying the result if it used AI
                if result.get('extraction_method') == 'OpenAI GPT-4':
                    logger.info("Forcing regex extraction due to --no-ai flag")
                    with open(file_path, 'r', encoding='utf-8') as f:
                        text = f.read()
                    result = extractor.extract_from_text(text, use_ai=False)
            else:
                result = extractor._create_error_result("No file path provided for no-ai mode")
        
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
            
            print("Running test with sample legal document (regex-only mode)", file=sys.stderr)
            result = extractor.extract_from_text(test_text, use_ai=False)
        
        # Output result as JSON
        try:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        except Exception as json_err:
            print(f"JSON output error: {json_err}", file=sys.stderr)
            sys.exit(1)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
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