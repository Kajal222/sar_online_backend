# Dynamic Metadata Extraction API

REST API for extracting metadata from legal documents using the dynamic extraction system.

## 🚀 Quick Start

### Start the Server
```bash
python api_server.py
```

The server will start on `http://localhost:5000`

## 📋 API Endpoints

### 1. Health Check
**GET** `/health`

Check if the API is running.

```bash
curl -X GET http://localhost:5000/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00.123456",
  "service": "Dynamic Metadata Extraction API"
}
```

### 2. Extract Metadata from File Upload
**POST** `/extract`

Extract metadata from an uploaded file or text content.

#### Extract All Fields from File
```bash
curl -X POST http://localhost:5000/extract \
  -F "file=@/path/to/your/document.pdf"
```

#### Extract Specific Field from File
```bash
curl -X POST http://localhost:5000/extract \
  -F "file=@/path/to/your/document.pdf" \
  -F "field=judge"
```

#### Extract from Text Content
```bash
curl -X POST http://localhost:5000/extract \
  -F "text=IN THE SUPREME COURT OF INDIA... HON'BLE MR. JUSTICE JOHN DOE" \
  -F "field=judge"
```

#### Extract with Document Type
```bash
curl -X POST http://localhost:5000/extract \
  -F "file=@/path/to/your/document.pdf" \
  -F "document_type=supreme_court" \
  -F "field=citation_year"
```

#### Extract with Custom Configuration
```bash
curl -X POST http://localhost:5000/extract \
  -F "file=@/path/to/your/document.pdf" \
  -F "config_file=scripts/extraction_config.json"
```

**Response (All Fields):**
```json
{
  "metadata": {
    "citation_year": "2024",
    "neutral_citation": "2024:INSC:123",
    "judge": "HON'BLE MR. JUSTICE JOHN DOE",
    "court_name": "SUPREME COURT OF INDIA",
    "decision_date": "15.03.2024",
    "petitioner": "ABC Corporation Ltd.",
    "respondent": "XYZ Government",
    "detected_document_type": "supreme_court"
  },
  "document_type": "supreme_court",
  "timestamp": "2024-01-15T10:30:00.123456",
  "text_length": 15420
}
```

**Response (Specific Field):**
```json
{
  "field": "judge",
  "value": "HON'BLE MR. JUSTICE JOHN DOE",
  "document_type": "supreme_court",
  "timestamp": "2024-01-15T10:30:00.123456"
}
```

### 3. Extract from File Path
**POST** `/extract/file`

Extract metadata from a file path (for server-side files).

```bash
curl -X POST http://localhost:5000/extract/file \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "/path/to/server/document.pdf",
    "field": "judge"
  }'
```

**Extract All Fields:**
```bash
curl -X POST http://localhost:5000/extract/file \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "/path/to/server/document.pdf"
  }'
```

**With Document Type:**
```bash
curl -X POST http://localhost:5000/extract/file \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "/path/to/server/document.pdf",
    "document_type": "high_court",
    "field": "case_number"
  }'
```

### 4. Detect Document Type
**POST** `/detect`

Detect the type of document from file or text.

#### Detect from File
```bash
curl -X POST http://localhost:5000/detect \
  -F "file=@/path/to/your/document.pdf"
```

#### Detect from Text
```bash
curl -X POST http://localhost:5000/detect \
  -F "text=IN THE HIGH COURT OF DELHI... W.P.(C) 1234/2024"
```

**Response:**
```json
{
  "document_type": "high_court",
  "text_length": 15420,
  "timestamp": "2024-01-15T10:30:00.123456"
}
```

### 5. Get Available Patterns
**GET** `/patterns`

Get all available extraction patterns and fields.

```bash
curl -X GET http://localhost:5000/patterns
```

**Response:**
```json
{
  "patterns": {
    "common_patterns": [
      "dates",
      "amounts",
      "names"
    ],
    "document_types": {
      "supreme_court": [
        "citation_year",
        "neutral_citation",
        "judge"
      ],
      "high_court": [
        "case_number",
        "judge",
        "decision_date"
      ]
    }
  },
  "timestamp": "2024-01-15T10:30:00.123456"
}
```

### 6. Add Custom Pattern
**POST** `/patterns`

Add a custom extraction pattern.

```bash
curl -X POST http://localhost:5000/patterns \
  -H "Content-Type: application/json" \
  -d '{
    "field_name": "custom_field",
    "patterns": [
      "Custom Field:\\s*([^\\n]+)",
      "Special Value:\\s*([^\\n]+)"
    ],
    "extraction_type": "regex",
    "description": "Extract custom field values",
    "document_type": "custom_document"
  }'
```

**Response:**
```json
{
  "message": "Custom pattern added for field: custom_field",
  "field_name": "custom_field",
  "document_type": "custom_document",
  "timestamp": "2024-01-15T10:30:00.123456"
}
```

## 🎯 Real-World Examples

### Example 1: Extract Judge Name from Supreme Court Judgment
```bash
curl -X POST http://localhost:5000/extract \
  -F "file=@supreme_court_judgment.pdf" \
  -F "field=judge"
```

### Example 2: Extract All Metadata from High Court Order
```bash
curl -X POST http://localhost:5000/extract \
  -F "file=@high_court_order.pdf" \
  -F "document_type=high_court"
```

### Example 3: Extract Contract Information
```bash
curl -X POST http://localhost:5000/extract \
  -F "file=@contract.pdf" \
  -F "field=parties"
```

### Example 4: Extract Any Custom Field
```bash
curl -X POST http://localhost:5000/extract \
  -F "file=@document.pdf" \
  -F "field=any_custom_field_name"
```

### Example 5: Detect Document Type First, Then Extract
```bash
# Step 1: Detect document type
DOC_TYPE=$(curl -s -X POST http://localhost:5000/detect \
  -F "file=@document.pdf" | jq -r '.document_type')

# Step 2: Extract relevant fields
curl -X POST http://localhost:5000/extract \
  -F "file=@document.pdf" \
  -F "document_type=$DOC_TYPE"
```

## 🔧 Advanced Usage

### Using Custom Configuration
```bash
# Create custom config
cat > custom_config.json << EOF
{
  "document_types": {
    "my_document": {
      "patterns": {
        "my_field": {
          "patterns": ["My Field:\\s*([^\\n]+)"],
          "extraction_type": "regex"
        }
      }
    }
  }
}
EOF

# Use custom config
curl -X POST http://localhost:5000/extract \
  -F "file=@document.pdf" \
  -F "config_file=custom_config.json" \
  -F "field=my_field"
```

### Batch Processing
```bash
# Process multiple files
for file in *.pdf; do
  echo "Processing $file..."
  curl -X POST http://localhost:5000/extract \
    -F "file=@$file" > "output_${file%.pdf}.json"
done
```

### Error Handling
```bash
# Check for errors
curl -X POST http://localhost:5000/extract \
  -F "file=@document.pdf" \
  -w "\nHTTP Status: %{http_code}\n"
```

## 📊 Response Format

### Success Response
```json
{
  "metadata": {
    "field1": "value1",
    "field2": "value2"
  },
  "document_type": "detected_type",
  "timestamp": "2024-01-15T10:30:00.123456",
  "text_length": 15420
}
```

### Error Response
```json
{
  "error": "Error description"
}
```

## 🚨 Error Codes

- `400` - Bad Request (missing parameters, invalid file type)
- `404` - File not found (for file path extraction)
- `413` - File too large (max 50MB)
- `500` - Internal server error

## 🔒 Security Notes

- File uploads are limited to 50MB
- Only allowed file types: PDF, TXT, DOC, DOCX
- Files are automatically cleaned up after processing
- CORS is enabled for cross-origin requests

## 🛠️ Installation & Setup

1. **Install Dependencies:**
```bash
pip install flask flask-cors spacy PyMuPDF pdfplumber pytesseract pdf2image
python -m spacy download en_core_web_sm
```

2. **Start Server:**
```bash
python api_server.py
```

3. **Test API:**
```bash
curl -X GET http://localhost:5000/health
```

## 📝 Notes

- The API automatically detects document types
- Supports any field name for dynamic extraction
- Multiple PDF extraction methods with fallback
- Comprehensive error handling and logging
- Production-ready with proper security measures 