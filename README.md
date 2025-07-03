# SAR Online Backend

A Node.js backend service for processing PDF documents and extracting metadata like court names, citations, and other legal information.

## Features

- PDF file upload with validation
- Metadata extraction (court name, citation year, judge, parties, etc.)
- Paragraph detection
- DOCX generation
- CORS enabled for frontend integration

## Setup

### Prerequisites

1. **Node.js** (v14 or higher)
2. **Python** (3.7 or higher) with required packages
3. **Python Dependencies** (install in your Python environment):
   ```bash
   pip install spacy fitz pdfplumber pytesseract pdf2image
   python -m spacy download en_core_web_sm
   ```

### Installation

1. Clone the repository
2. Install Node.js dependencies:
   ```bash
   npm install
   ```
3. Configure environment variables (create `.env` file):
   ```env
   PORT=3000
   PYTHON_PATH=C:\\path\\to\\your\\python.exe
   ```
4. Start the server:
   ```bash
   npm start
   ```

## API Endpoints

### 1. Upload PDF File

**POST** `/upload`

Upload a PDF file for processing.

**Request:**
- Content-Type: `multipart/form-data`
- Body: Form data with field name `pdf` containing the PDF file

**Response:**
```json
{
  "fileId": "pdf-1234567890-123456789.pdf",
  "originalName": "document.pdf",
  "size": 1024000,
  "message": "File uploaded successfully"
}
```

**Error Responses:**
- `400`: No file uploaded, invalid file type, file too large
- `500`: Internal server error

### 2. Extract Metadata

**POST** `/extract-metadata`

Extract specific metadata from an uploaded PDF file.

**Request:**
```json
{
  "fileId": "pdf-1234567890-123456789.pdf",
  "field": "courtname"
}
```

**Supported Fields:**
- `courtname`: Extract court name
- `citationyear`: Extract citation year
- `neutralcitation`: Extract neutral citation number
- `judge`: Extract judge names
- `party`: Extract party names

**Response:**
```json
{
  "field": "courtname",
  "value": "SUPREME COURT OF INDIA",
  "success": true
}
```

**Error Responses:**
- `400`: Missing parameters, invalid field, file not found
- `404`: File not found
- `500`: Extraction failed

### 3. Detect Paragraphs

**POST** `/detect-paragraphs`

Detect and extract paragraphs from text.

**Request:**
```json
{
  "text": "Your text content here..."
}
```

### 4. Generate DOCX

**POST** `/generate-docx`

Generate a DOCX file from metadata and paragraphs.

**Request:**
```json
{
  "metadata": { /* metadata object */ },
  "paragraphs": [ /* paragraphs array */ ]
}
```

## File Structure

```
├── server.js              # Main server file
├── scripts/
│   ├── pdf_parser.py      # PDF text extraction
│   ├── metadata_extractor.py  # Metadata extraction
│   ├── paragraph_detector.py  # Paragraph detection
│   └── docx_generator.py  # DOCX generation
├── uploads/               # Uploaded files
├── generated/             # Generated DOCX files
└── temp/                  # Temporary files
```

## Error Handling

The API includes comprehensive error handling:

- File validation (type, size)
- Parameter validation
- Python process timeout (30 seconds)
- Automatic file cleanup
- Detailed error messages

## Security Features

- File type validation (PDF only)
- File size limits (10MB)
- Unique filename generation
- Automatic file cleanup
- Input sanitization

## Development

Run in development mode with auto-restart:
```bash
npm run start:dev
```

## Production Deployment

1. Set environment variables
2. Ensure Python dependencies are installed
3. Configure proper file permissions
4. Set up reverse proxy (nginx recommended)
5. Use PM2 or similar process manager

## Troubleshooting

### Common Issues

1. **Python path not found**: Update `PYTHON_PATH` in environment variables
2. **Missing Python packages**: Install required packages in your Python environment
3. **File upload fails**: Check file size and type restrictions
4. **Metadata extraction fails**: Ensure PDF is readable and contains text

### Logs

Check server logs for detailed error information. The server logs:
- File upload details
- Metadata extraction results
- Python process errors
- General server errors 