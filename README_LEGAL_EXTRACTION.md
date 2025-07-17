# Legal Document Metadata Extraction

This system provides specialized extraction of legal document metadata in a specific format required for legal document management systems.

## Features

- **Structured Output**: Extracts metadata in the exact JSON format you specified
- **Multiple Input Methods**: Supports PDF uploads, text input, and file uploads
- **Comprehensive Field Extraction**: Extracts all required fields including:
  - Appellant and Respondent information
  - Judge names and court details
  - Citation information
  - Case history and dates
  - Advocate details
  - Judgment type and results

## API Endpoints

### Extract Legal Document Metadata

**Endpoint**: `POST /extract/legal`

**Description**: Extracts legal document metadata in the required format

**Request Methods**:
1. **File Upload** (Form Data):
   ```
   POST /extract/legal
   Content-Type: multipart/form-data
   
   file: [PDF file]
   ```

2. **Text Input** (Form Data):
   ```
   POST /extract/legal
   Content-Type: application/x-www-form-urlencoded
   
   text: [document text]
   ```

3. **JSON Input**:
   ```
   POST /extract/legal
   Content-Type: application/json
   
   {
     "text": "document text content"
   }
   ```

**Response Format**:
```json
{
  "metadata": {
    "docId": 1152110,
    "appellant": "Appellant",
    "remarkable": "none",
    "respondent": "Respondents",
    "judgeName": "none",
    "judgementOrder": "",
    "judgementType": "Judgement",
    "caseResult": "This is result",
    "doubleCouncilDetailRequest": {
      "advocateForRespondent": "none",
      "advocateForAppellant": "none",
      "extraCouncilDetails": "none"
    },
    "singleCouncilDetailRequest": null,
    "courtDetailRequest": {
      "allJudges": "none",
      "courtBenchId": 2,
      "courtBranchId": "34",
      "courtId": 1
    },
    "citationRequest": {
      "citationCategoryId": 4,
      "journalId": 2,
      "otherCitation": "Other Citations",
      "neutralCitation": "Neutral Citations",
      "pageNumber": "1",
      "year": 2025,
      "volume": "none",
      "secondaryCitationCategoryId": 5,
      "secondaryJournalId": 5,
      "secondaryPageNumber": "",
      "secondaryYear": "0",
      "secondaryVolume": "",
      "thirdCitationCategoryId": 5,
      "thirdJournalId": 5,
      "thirdPageNumber": "none",
      "thirdYear": "0",
      "thirdVolume": "none",
      "fourthCitationCategoryId": 5,
      "fourthJournalId": 5,
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
    "caseTopics": []
  },
  "text_length": 1234,
  "timestamp": "2025-01-15T10:30:00"
}
```

## Usage Examples

### 1. Using Python Script

```python
from scripts.legal_document_extractor import LegalDocumentExtractor

# Initialize extractor
extractor = LegalDocumentExtractor()

# Extract from text
text = """
IN THE HIGH COURT OF DELHI
HON'BLE MR. JUSTICE JOHN DOE
Case No. WP(C) 1234/2024
BETWEEN
ABC Corporation Ltd.
Appellant
AND
State of Delhi
Respondent
"""

result = extractor.extract_to_json(text)
print(result)
```

### 2. Using API with cURL

```bash
# Upload PDF file
curl -X POST http://localhost:5000/extract/legal \
  -F "file=@document.pdf"

# Send text content
curl -X POST http://localhost:5000/extract/legal \
  -H "Content-Type: application/json" \
  -d '{"text": "IN THE HIGH COURT OF DELHI..."}'
```

### 3. Using JavaScript/Fetch

```javascript
// Upload file
const formData = new FormData();
formData.append('file', fileInput.files[0]);

fetch('/extract/legal', {
  method: 'POST',
  body: formData
})
.then(response => response.json())
.then(data => console.log(data));

// Send text
fetch('/extract/legal', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    text: 'IN THE HIGH COURT OF DELHI...'
  })
})
.then(response => response.json())
.then(data => console.log(data));
```

## Extracted Fields

The system extracts the following fields from legal documents:

### Basic Information
- **docId**: Document ID (default: 1152110)
- **appellant**: Appellant/petitioner information
- **respondent**: Respondent/defendant information
- **judgeName**: Judge/magistrate names
- **judgementType**: Type of judgment (Judgment, Order, etc.)
- **caseResult**: Case outcome/result

### Court Details
- **courtDetailRequest**: Court information including:
  - **allJudges**: All judge names
  - **courtBenchId**: Court bench ID
  - **courtBranchId**: Court branch ID
  - **courtId**: Court ID

### Citation Information
- **citationRequest**: Citation details including:
  - **neutralCitation**: Neutral citation number
  - **year**: Citation year
  - **pageNumber**: Page number
  - **volume**: Volume information
  - Multiple secondary, tertiary, and quaternary citations

### Advocate Information
- **doubleCouncilDetailRequest**: Advocate details including:
  - **advocateForAppellant**: Appellant's advocate
  - **advocateForRespondent**: Respondent's advocate
  - **extraCouncilDetails**: Additional counsel details

### Case History
- **caseHistoryRequest**: Case history including:
  - **caseNumber**: Case number
  - **decidedDay/Month/Year**: Decision date
  - **notes**: Additional notes
  - **year**: Case year

## Installation and Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements_ai.txt
   ```

2. **Start the API Server**:
   ```bash
   python api_server.py
   ```

3. **Test the System**:
   ```bash
   python test_legal.py
   ```

## Supported Document Types

The system can extract metadata from various legal documents:
- Supreme Court judgments
- High Court judgments
- District Court orders
- Tribunal decisions
- Legal contracts
- Legislation and rules

## Error Handling

The system includes comprehensive error handling:
- Invalid file formats
- Missing text content
- Extraction failures
- Network errors

All errors are returned with appropriate HTTP status codes and error messages.

## Performance

- **Fast Processing**: Optimized regex patterns for quick extraction
- **Memory Efficient**: Processes documents without loading entire files into memory
- **Scalable**: Can handle multiple concurrent requests
- **Robust**: Multiple fallback methods for text extraction

## Customization

You can customize the extraction patterns by modifying the `scripts/legal_document_extractor.py` file:

1. **Add New Patterns**: Add regex patterns to the `_initialize_patterns()` method
2. **Modify Field Extraction**: Update the `extract_metadata()` method
3. **Add New Fields**: Extend the `LegalDocumentMetadata` dataclass

## Troubleshooting

### Common Issues

1. **"No text content found"**: Ensure the PDF contains extractable text
2. **"File type not allowed"**: Only PDF, TXT, DOC, DOCX files are supported
3. **"Extraction failed"**: Check if the document follows standard legal format

### Debug Mode

Enable debug logging by setting the log level:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review the API documentation
3. Test with the provided sample scripts
4. Check server logs for detailed error information 