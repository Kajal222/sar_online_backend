#!/usr/bin/env python3
"""
AI/NLP-based metadata extraction for legal documents.
Hybrid approach combining regex patterns with AI/LLM capabilities.
"""

import json
import re
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
import requests
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AIExtractionResult:
    """Result from AI-based extraction"""
    field_name: str
    value: str
    confidence: float
    method: str

class AIExtractor:
    """AI-based metadata extraction using multiple approaches"""
    
    def __init__(self):
        # Load API key from environment variable or config file
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        if not self.openai_api_key:
            # Try to load from config file
            try:
                config_path = os.path.join(os.path.dirname(__file__), 'ai_config.json')
                if os.path.exists(config_path):
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                        self.openai_api_key = config.get('openai_api_key', '')
            except Exception as e:
                logger.warning(f"Could not load API key from config: {e}")
        
        # Remove the hardcoded API key for security
        # self.openai_api_key = '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'
        # self.huggingface_api_key = os.getenv('HUGGINGFACE_API_KEY')
    def extract_advocates_ai(self, text: str) -> List[AIExtractionResult]:
        """Extract advocates using AI/LLM approach"""
        results = []
        
        # Method 1: Enhanced regex patterns for the specific format
        enhanced_patterns = [
            r'(Shri\s+[A-Z][a-z\s]+[^.]*?Advocate[^.]*?)',
            r'(Shri\s+[A-Z][a-z\s]+[^.]*?for\s+[^.]*?Respondent[^.]*?)',
            r'(Shri\s+[A-Z][a-z\s]+[^.]*?for\s+[^.]*?Petitioner[^.]*?)',
            r'(Shri\s+[A-Z][a-z\s]+[^.]*?M\.P\.\s+No\.\s*\d+[^.]*?)',
            r'(Mr\.\s+[A-Z][a-z\s]+[^.]*?Advocate[^.]*?)',
            r'(Ms\.\s+[A-Z][a-z\s]+[^.]*?Advocate[^.]*?)'
        ]
        
        for pattern in enhanced_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                value = match.group(1).strip()
                # Clean up the extracted text
                value = re.sub(r'\s+', ' ', value)  # Normalize whitespace
                value = re.sub(r'[^\w\s,\.\-\(\)]', '', value)  # Remove special chars except basic punctuation
                
                results.append(AIExtractionResult(
                    field_name='advocates',
                    value=value,
                    confidence=0.85,
                    method='enhanced_regex'
                ))
        
        # Method 2: LLM extraction if API key is available
        if self.openai_api_key:
            llm_results = self._extract_with_llm(text, 'advocates')
            results.extend(llm_results)
        
        return results
    
    def extract_judge_ai(self, text: str) -> List[AIExtractionResult]:
        """Extract judge names using AI patterns"""
        results = []
        
        judge_patterns = [
            r'HON\'BLE\s+(?:SHRI|SMT\.|MR\.|MS\.)\s+JUSTICE\s+([A-Z][a-z\s]+)',
            r'JUSTICE\s+([A-Z][a-z\s]+)',
            r'BEFORE\s+(?:HON\'BLE\s+)?(?:SHRI|SMT\.|MR\.|MS\.)\s+JUSTICE\s+([A-Z][a-z\s]+)'
        ]
        
        for pattern in judge_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                judge_name = match.group(1).strip()
                results.append(AIExtractionResult(
                    field_name='judge',
                    value=judge_name,
                    confidence=0.9,
                    method='ai_pattern'
                ))

        if self.openai_api_key:
            llm_results = self._extract_with_llm(text, 'judge')
            results.extend(llm_results)
        
        return results
    
    def extract_court_ai(self, text: str) -> List[AIExtractionResult]:
        """Extract court names using AI LLM first, fallback to regex patterns"""
        
        # Fallback to regex patterns if LLM is not available or fails
        results = []
        court_patterns = [
            # Comprehensive patterns for full court names
            r'(HIGH\s+COURT\s+OF\s+[A-Z\s&]+(?:AND\s+[A-Z\s]+)?\s+AT\s+[A-Z\s]+)',
            r'(HIGH\s+COURT\s+OF\s+[A-Z\s&]+(?:AND\s+[A-Z\s]+)?)',
            r'(SUPREME\s+COURT\s+OF\s+[A-Z\s]+)',
            r'(SUPREME\s+COURT)',
            r'([A-Z\s&]+(?:AND\s+[A-Z\s]+)?\s+HIGH\s+COURT\s+AT\s+[A-Z\s]+)',
            r'([A-Z\s&]+(?:AND\s+[A-Z\s]+)?\s+HIGH\s+COURT)',
            r'(DISTRICT\s+COURT\s+OF\s+[A-Z\s]+)',
            r'([A-Z\s]+COURT\s+OF\s+[A-Z\s]+)',
            r'(COURT\s+OF\s+[A-Z\s]+)'
        ]
        
        for pattern in court_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                court_name = match.group(1).strip()
                # Clean up the extracted text
                court_name = re.sub(r'\s+', ' ', court_name)  # Normalize whitespace
                court_name = re.sub(r'[\r\n]+', ' ', court_name)  # Remove line breaks
                
                # Remove text after certain keywords
                court_name = re.split(r'\bBEFORE\b|\bSHRI\s+JUSTICE\b|\bJUSTICE\b|\bHON\'BLE\b', court_name, flags=re.IGNORECASE)[0].strip()
                
                if len(court_name) > 5:  # Only add if meaningful
                    results.append(AIExtractionResult(
                        field_name='court_name',
                        value=court_name,
                        confidence=0.8,
                        method='ai_pattern'
                    ))
        
        if self.openai_api_key:
            llm_results = self._extract_with_llm(text, 'court_name')
            results.extend(llm_results)
        
        return results
    
    def extract_citation_year_ai(self, text: str) -> List[AIExtractionResult]:
        """Extract citation years using AI patterns"""
        results = []
        
        year_patterns = [
            r'(\d{4}):[A-Z]+-[A-Z]+:\d+',
            r'CITATION\s+NO\.\s+(\d{4})',
            r'(\d{4})\s*[-&]\s*\d{4}',
            r'(\d{4})\s+of\s+\d{4}'
        ]
        
        for pattern in year_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                year = match.group(1) if match.groups() else match.group(0)
                try:
                    year_int = int(year)
                    if 1900 <= year_int <= 2030:
                        results.append(AIExtractionResult(
                            field_name='citation_year',
                            value=str(year_int),
                            confidence=0.9,
                            method='ai_pattern'
                        ))
                except ValueError:
                    continue
        
        return results
    
    def _extract_with_llm(self, text: str, field_name: str) -> List[AIExtractionResult]:
        """Extract using OpenAI LLM API"""
        if not self.openai_api_key:
            return []
        
        try:
            if field_name == 'advocates':
                prompt = f"""
                Extract all advocate names and their roles from this legal document text.
                
                Instructions:
                1. Look for advocate names like "Shri [Name]", "Mr. [Name]", "Ms. [Name]"
                2. Include their roles like "Advocate for Petitioner", "Advocate for Respondent", etc.
                3. Return only the advocate names and their roles, not other text
                4. Format as: "Shri [Name], Advocate for [Role]"
                5. If multiple advocates, separate with semicolons
                
                Example output: "Shri Gopi ndeep Shukla, Advocate for Respondent; Shri [Name], Advocate for Petitioner"
                
                Text: {text[:4000]}
                
                Return only the advocate information, no other text.
                """
            elif field_name == 'court_name':
                prompt = f"""
                Extract the complete court name from this legal document text.
                
                Instructions:
                1. Look for court names like "HIGH COURT OF [STATE]", "SUPREME COURT OF INDIA", "DISTRICT COURT", etc.
                2. Include the location if mentioned (e.g., "AT JABALPUR", "AT SRINAGAR")
                3. Include state names with special characters like "JAMMU & KASHMIR AND LADAKH"
                4. Return only the court name, not other text like "BEFORE", "JUSTICE", or judge names
                5. Format as: "HIGH COURT OF [STATE] AT [LOCATION]" or "SUPREME COURT OF INDIA" or "DISTRICT COURT OF [PLACE]"
                6. Remove any line breaks, extra spaces, or irrelevant text
                7. Preserve the exact court name as it appears in the document
                
                Examples:
                - "HIGH COURT OF MADHYA PRADESH AT JABALPUR"
                - "HIGH COURT OF JAMMU & KASHMIR AND LADAKH AT SRINAGAR"
                - "SUPREME COURT OF INDIA"
                - "DISTRICT COURT OF DELHI"
                
                Text: {text[:4000]}
                
                Return only the court name, no other text. If no court name is found, return "Not found".
                """
            else:
                return []
            
            headers = {
                "Authorization": f"Bearer {self.openai_api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "gpt-4o",
                "messages": [
                    {"role": "system", "content": "You are a legal document parser. Extract information accurately and concisely."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1,
                "max_tokens": 500
            }
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content'].strip()
                
                # Clean up the response
                if content and content != "Not found":
                    # Remove any JSON formatting if present
                    if content.startswith('[') or content.startswith('{'):
                        try:
                            parsed = json.loads(content)
                            if isinstance(parsed, list):
                                content = "; ".join([str(item) for item in parsed])
                            elif isinstance(parsed, dict):
                                content = str(parsed)
                        except:
                            pass
                    
                    return [AIExtractionResult(
                        field_name=field_name,
                        value=content,
                        confidence=0.95,
                        method='openai_llm'
                    )]
            
            return []
            
        except Exception as e:
            logger.error(f"Error in LLM extraction for {field_name}: {e}")
            return []

def test_ai_extractor():
    """Test the AI extractor with sample text"""
    test_text = """
    NEUTRAL CITATION NO. 2025:MPHC-JBP:24371
    IN THE HIGH COURT OF MADHYA PRADESH AT JABALPUR
    BEFORE HON'BLE SHRI JUSTICE SANJEEV SACHDEVA & HON'BLE SHRI JUSTICE VINAY SARAF
    M.P. No. 3192 of 2022
    Shri Utkarsh Kumar Sonkar of 2023. 
    Shri Deepak Sahu, Advocate for the Respondent in M.P. No. 31
    Shri Deepak Sahu, Advocate for the Respondent in M.P. No. 3192 of 2022.
    """
    
    extractor = AIExtractor()
    
    print("Testing AI Extraction...")
    print("=" * 50)
    
    for field in ['advocates', 'judge', 'court_name', 'citation_year']:
        if field == 'advocates':
            results = extractor.extract_advocates_ai(test_text)
        elif field == 'judge':
            results = extractor.extract_judge_ai(test_text)
        elif field == 'court_name':
            results = extractor.extract_court_ai(test_text)
        elif field == 'citation_year':
            results = extractor.extract_citation_year_ai(test_text)
        
        print(f"\n{field.upper()}:")
        for result in results:
            print(f"  - {result.value} (confidence: {result.confidence}, method: {result.method})")

if __name__ == "__main__":
    test_ai_extractor()
