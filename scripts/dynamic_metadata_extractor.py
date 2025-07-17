import sys
import re
import spacy
import os
import fitz  # PyMuPDF
import pdfplumber
import pytesseract
from pdf2image import convert_from_path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

nlp = spacy.load("en_core_web_sm")

@dataclass
class ExtractionPattern:
    """Represents a pattern for extracting specific metadata fields"""
    field_name: str
    patterns: List[str]
    extraction_type: str  # 'regex', 'nlp', 'positional', 'contextual'
    description: str
    post_process: Optional[str] = None  # 'clean', 'normalize', 'validate', etc.

class DynamicMetadataExtractor:
    """Dynamic metadata extractor for legal documents"""
    
    def __init__(self):
        self.patterns = self._initialize_patterns()
        self.context_keywords = {
            'court': ['court', 'tribunal', 'commission', 'board'],
            'judge': ['justice', 'judge', 'magistrate', 'presiding'],
            'case': ['case', 'matter', 'petition', 'appeal', 'suit'],
            'date': ['date', 'dated', 'on', 'filed', 'decided'],
            'citation': ['citation', 'reference', 'number', 'no.'],
            'party': ['petitioner', 'respondent', 'appellant', 'defendant', 'plaintiff']
        }
    
    def _initialize_patterns(self) -> Dict[str, ExtractionPattern]:
        """Initialize extraction patterns for various legal document fields"""
        return {
            # Citation patterns
            'citation_year': ExtractionPattern(
                field_name='citation_year',
                patterns=[
                    r'NEUTRAL CITATION NO\.\s*(\d{4}):',
                    r'Citation No\.\s*(\d{4})',
                    r'(\d{4})\s*[A-Z]+\s*\d+',
                    r'Case No\.\s*(\d{4})',
                    r'(\d{4})\s*[A-Z]+\s*[A-Z]+'
                ],
                extraction_type='regex',
                description='Extract year from citation numbers'
            ),
            
            'neutral_citation': ExtractionPattern(
                field_name='neutral_citation',
                patterns=[
                    r'NEUTRAL CITATION NO\.\s*([^\n]+)',
                    r'Citation No\.\s*([^\n]+)',
                    r'([A-Z]+\s*\d+\s*[A-Z]+\s*\d+)',
                    r'Case No\.\s*([^\n]+)'
                ],
                extraction_type='regex',
                description='Extract full citation number'
            ),
            
            # Court and judicial patterns
            'court_name': ExtractionPattern(
                field_name='court_name',
                patterns=[
                    r'([A-Z\s]+COURT[A-Z\s]*)',
                    r'([A-Z\s]+TRIBUNAL[A-Z\s]*)',
                    r'([A-Z\s]+COMMISSION[A-Z\s]*)',
                    r'([A-Z\s]+BOARD[A-Z\s]*)'
                ],
                extraction_type='regex',
                description='Extract court name'
            ),
            
            'judge': ExtractionPattern(
                field_name='judge',
                patterns=[
                    r'JUSTICE\s+([A-Z\s]+)',
                    r'HON\'BLE\s+JUSTICE\s+([A-Z\s]+)',
                    r'MR\.\s+JUSTICE\s+([A-Z\s]+)',
                    r'MRS\.\s+JUSTICE\s+([A-Z\s]+)',
                    r'JUDGE\s+([A-Z\s]+)',
                    r'MAGISTRATE\s+([A-Z\s]+)'
                ],
                extraction_type='regex',
                description='Extract judge names'
            ),
            
            # Date patterns
            'decision_date': ExtractionPattern(
                field_name='decision_date',
                patterns=[
                    r'Decided on\s*([^\n]+)',
                    r'Date\s*:\s*([^\n]+)',
                    r'(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})',
                    r'(\d{1,2}\s+[A-Z]+\s+\d{4})',
                    r'(\d{4}[\/\-]\d{1,2}[\/\-]\d{1,2})'
                ],
                extraction_type='regex',
                description='Extract decision date'
            ),
            
            # Party patterns
            'petitioner': ExtractionPattern(
                field_name='petitioner',
                patterns=[
                    r'Petitioner\s*:\s*([^\n]+)',
                    r'Appellant\s*:\s*([^\n]+)',
                    r'Plaintiff\s*:\s*([^\n]+)'
                ],
                extraction_type='regex',
                description='Extract petitioner/appellant information'
            ),
            
            'respondent': ExtractionPattern(
                field_name='respondent',
                patterns=[
                    r'Respondent\s*:\s*([^\n]+)',
                    r'Defendant\s*:\s*([^\n]+)',
                    r'Opposite Party\s*:\s*([^\n]+)'
                ],
                extraction_type='regex',
                description='Extract respondent/defendant information'
            ),
            
            # Case type patterns
            'case_type': ExtractionPattern(
                field_name='case_type',
                patterns=[
                    r'(Writ Petition|Civil Appeal|Criminal Appeal|Special Leave Petition|Public Interest Litigation)',
                    r'(Petition|Appeal|Suit|Complaint|Application)',
                    r'(Constitutional|Civil|Criminal|Administrative|Commercial)'
                ],
                extraction_type='regex',
                description='Extract case type'
            ),
            
            # Subject matter patterns
            'subject_matter': ExtractionPattern(
                field_name='subject_matter',
                patterns=[
                    r'Subject\s*:\s*([^\n]+)',
                    r'Regarding\s*:\s*([^\n]+)',
                    r'In the matter of\s*:\s*([^\n]+)'
                ],
                extraction_type='regex',
                description='Extract subject matter'
            )
        }
    
    def extract_metadata(self, text: str, field: str) -> str:
        """Extract metadata for a specific field using dynamic patterns"""
        field = field.lower().replace(' ', '_')
        
        # Check if we have a predefined pattern for this field
        if field in self.patterns:
            return self._extract_with_pattern(text, self.patterns[field])
        
        # Try dynamic extraction based on field name
        return self._extract_dynamically(text, field)
    
    def _extract_with_pattern(self, text: str, pattern: ExtractionPattern) -> str:
        """Extract using predefined patterns"""
        results = []
        
        for regex_pattern in pattern.patterns:
            matches = re.findall(regex_pattern, text, flags=re.IGNORECASE | re.MULTILINE)
            if matches:
                if isinstance(matches[0], tuple):
                    results.extend([match[0] for match in matches])
                else:
                    results.extend(matches)
        
        if results:
            result = "; ".join(set(results))  # Remove duplicates
            return self._post_process(result, pattern.post_process)
        
        return "Not found"
    
    def _extract_dynamically(self, text: str, field: str) -> str:
        """Dynamically extract field based on field name and context"""
        
        # Handle different field types
        if 'date' in field:
            return self._extract_dates(text)
        elif 'name' in field or 'party' in field:
            return self._extract_names(text)
        elif 'number' in field or 'id' in field:
            return self._extract_numbers(text)
        elif 'amount' in field or 'money' in field:
            return self._extract_amounts(text)
        elif 'address' in field:
            return self._extract_addresses(text)
        else:
            # Try contextual extraction
            return self._extract_contextual(text, field)
    
    def _extract_dates(self, text: str) -> str:
        """Extract various date formats"""
        date_patterns = [
            r'(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})',
            r'(\d{1,2}\s+[A-Z]+\s+\d{4})',
            r'(\d{4}[\/\-]\d{1,2}[\/\-]\d{1,2})',
            r'(\d{1,2}\.\d{1,2}\.\d{2,4})'
        ]
        
        dates = []
        for pattern in date_patterns:
            matches = re.findall(pattern, text)
            dates.extend(matches)
        
        return "; ".join(set(dates)) if dates else "Not found"
    
    def _extract_names(self, text: str) -> str:
        """Extract names using NLP"""
        doc = nlp(text)
        names = [ent.text for ent in doc.ents if ent.label_ in ("PERSON", "ORG")]
        return ", ".join(names[:10]) if names else "Not found"
    
    def _extract_numbers(self, text: str) -> str:
        """Extract various number formats"""
        number_patterns = [
            r'(\d{4,})',  # 4+ digit numbers
            r'([A-Z]+\s*\d+[A-Z]*\s*\d*)',  # Alphanumeric codes
            r'(Case\s+No\.\s*[^\n]+)',
            r'(File\s+No\.\s*[^\n]+)'
        ]
        
        numbers = []
        for pattern in number_patterns:
            matches = re.findall(pattern, text, flags=re.IGNORECASE)
            numbers.extend(matches)
        
        return "; ".join(set(numbers)) if numbers else "Not found"
    
    def _extract_amounts(self, text: str) -> str:
        """Extract monetary amounts"""
        amount_patterns = [
            r'(Rs\.\s*\d+[,\d]*)',
            r'(\$\s*\d+[,\d]*)',
            r'(\d+[,\d]*\s*(?:rupees|dollars))',
            r'(\d+[,\d]*\s*[A-Z]{3})'
        ]
        
        amounts = []
        for pattern in amount_patterns:
            matches = re.findall(pattern, text, flags=re.IGNORECASE)
            amounts.extend(matches)
        
        return "; ".join(set(amounts)) if amounts else "Not found"
    
    def _extract_addresses(self, text: str) -> str:
        """Extract addresses using NLP"""
        doc = nlp(text)
        addresses = [ent.text for ent in doc.ents if ent.label_ == "GPE"]
        return ", ".join(addresses[:5]) if addresses else "Not found"
    
    def _extract_contextual(self, text: str, field: str) -> str:
        """Extract based on field name context"""
        # Create a pattern based on the field name
        field_words = field.split('_')
        pattern = r'(' + r'|'.join(field_words) + r')\s*[:\-]\s*([^\n]+)'
        
        matches = re.findall(pattern, text, flags=re.IGNORECASE)
        if matches:
            return "; ".join([match[1].strip() for match in matches])
        
        return "Not found"
    
    def _post_process(self, result: str, post_process_type: Optional[str]) -> str:
        """Post-process extracted results"""
        if not post_process_type:
            return result
        
        if post_process_type == 'clean':
            return re.sub(r'\s+', ' ', result).strip()
        elif post_process_type == 'normalize':
            return result.upper()
        elif post_process_type == 'validate':
            # Add validation logic here
            return result if result else "Invalid"
        
        return result
    
    def extract_all_fields(self, text: str) -> Dict[str, str]:
        """Extract all available fields from the text"""
        results = {}
        
        for field_name, pattern in self.patterns.items():
            results[field_name] = self._extract_with_pattern(text, pattern)
        
        return results
    
    def add_custom_pattern(self, field_name: str, patterns: List[str], 
                          extraction_type: str = 'regex', description: str = "") -> None:
        """Add a custom extraction pattern"""
        self.patterns[field_name] = ExtractionPattern(
            field_name=field_name,
            patterns=patterns,
            extraction_type=extraction_type,
            description=description
        )

# Initialize the extractor
extractor = DynamicMetadataExtractor()

def extract_metadata(text, field):
    """Legacy function for backward compatibility"""
    return extractor.extract_metadata(text, field)

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF using PyMuPDF"""
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
    """Extract text from PDF using pdfplumber"""
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
    """Extract text from PDF using OCR"""
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
    """Extract all available metadata from a document"""
    # Extract text based on file type
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == ".pdf":
        # Try multiple extraction methods for better results
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
    
    # Extract all metadata
    metadata = extractor.extract_all_fields(text)
    
    # Add document info
    metadata['document_type'] = ext.upper().replace('.', '')
    metadata['extraction_timestamp'] = datetime.now().isoformat()
    metadata['text_length'] = len(text)
    
    return metadata

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python dynamic_metadata_extractor.py <file_path> [field_name]")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    if len(sys.argv) == 2:
        # Extract all metadata
        metadata = extract_all_metadata(file_path)
        print(json.dumps(metadata, indent=2))
    else:
        # Extract specific field
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