# Enhanced PDF to DOCX Converter for Legal Documents

## Overview

This enhanced PDF to DOCX converter is specifically designed for legal documents (judgments, orders, court documents) and provides advanced processing capabilities while preserving document integrity and formatting.

## Features

### 🎯 Legal Document Optimization
- **Page Number Removal**: Automatically detects and removes page numbers from headers and footers
- **Watermark Removal**: Removes common watermarks (CONFIDENTIAL, DRAFT, COPY, etc.)
- **Scanner Artifact Cleanup**: Eliminates scanner artifacts and noise
- **Legal Structure Preservation**: Maintains legal document hierarchy and formatting

### 📝 Formatting Preservation
- **Font Preservation**: Maintains original font sizes and styles
- **Bold/Italic Detection**: Attempts to keep bold and italic styling
- **Alignment Preservation**: Preserves left, center, right, and justified alignment
- **Content Integrity**: Ensures no content loss during conversion
- **Paragraph Structure**: Maintains proper paragraph breaks and spacing

### 🔧 Advanced Processing
- **Smart Text Analysis**: Intelligent detection of document structure
- **Multi-page Support**: Handles documents of any length
- **Error Handling**: Robust error handling with detailed logging
- **Performance Optimization**: Efficient processing for large documents

## API Endpoint

### POST `/generate-docx`

Converts a legal PDF document to DOCX format with enhanced processing.

This endpoint now relies on the `font_preserving_pdf_to_docx.py`
converter which maps PDF text spans directly to DOCX runs. This
approach keeps the original fonts and alignment for a layout that
closely mirrors the source PDF.

**Request:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Body: PDF file with field name `pdf`

**Response:**
- Content-Type: `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
- File download with preserved formatting

**Example Usage:**
```bash
curl -X POST \
  http://localhost:3000/generate-docx \
  -H 'Content-Type: multipart/form-data' \
  -F 'pdf=@legal_document.pdf' \
  --output converted_document.docx
```

## Installation and Setup

### Prerequisites
- Python 3.8+
- Node.js 14+
- Tesseract OCR (optional, for scanned documents)

### Dependencies

Install Python dependencies:
```bash
pip install -r requirements_pdf_processing.txt
```

Install Node.js dependencies:
```bash
npm install
```

### Environment Setup

1. **Install spaCy model** (for enhanced text processing):
```bash
python -m spacy download en_core_web_sm
```

2. **Optional: Install Tesseract OCR** (for scanned documents):
   - Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
   - Linux: `sudo apt-get install tesseract-ocr`
   - macOS: `brew install tesseract`

## Usage

### Starting the Server

```bash
node server.js
```

The server will start on port 3000 by default.

### Testing the Converter

Run the test suite to validate functionality:

```bash
python test_enhanced_converter.py
```

## Technical Details

### Page Number Detection

The converter uses advanced pattern matching to identify page numbers:

```python
page_number_patterns = [
    r'\bpage\s*no\.?\s*\d+',
    r'\bpage\s*\d+',
    r'\d+\s*of\s*\d+',
    r'\(\d+\s*of\s*\d+\)',
    r'\[CW-\d+/\d+\]',
    r'^\d+$',  # Standalone page numbers
    r'Page\s*\d+',
    r'PAGE\s*\d+'
]
```

### Watermark Removal

Common legal document watermarks are automatically detected and removed:

```python
watermark_patterns = [
    r'CONFIDENTIAL',
    r'DRAFT',
    r'COPY',
    r'SCANNED',
    r'DIGITAL\s*COPY',
    r'ELECTRONIC\s*COPY',
    r'ORIGINAL',
    r'CERTIFIED\s*COPY',
    r'TRUE\s*COPY',
    r'OFFICIAL\s*COPY'
]
```

### Font Size Mapping

Legal documents use specific font size hierarchy:

```python
font_size_mapping = {
    'title': Pt(16),      # Document titles
    'heading': Pt(14),    # Section headings
    'subheading': Pt(12), # Subsection headings
    'body': Pt(11),       # Body text
    'small': Pt(10),      # Footnotes
    'footnote': Pt(9)     # Small text
}
```

### Alignment Detection

The converter intelligently detects text alignment based on block positioning:

- **Justified**: Blocks spanning most of page width
- **Centered**: Blocks within 50 points of page center
- **Right-aligned**: Blocks positioned right of center
- **Left-aligned**: Default alignment

## Error Handling

The converter includes comprehensive error handling:

- **File Validation**: Checks for valid PDF files
- **Size Limits**: Enforces 50MB file size limit
- **Processing Errors**: Handles conversion failures gracefully
- **Timeout Protection**: Prevents hanging on large files
- **Detailed Logging**: Provides detailed error information

## Performance Considerations

### Timeout Settings
- **Small files** (<5MB): 2 minutes timeout
- **Large files** (>5MB): 5 minutes timeout

### Memory Management
- Automatic cleanup of temporary files
- Efficient memory usage for large documents
- Streaming processing for better performance

## Testing

### Test Coverage

The enhanced converter includes comprehensive testing:

1. **Pattern Testing**: Validates page number and watermark detection
2. **Formatting Tests**: Ensures font and alignment preservation
3. **Content Tests**: Verifies content integrity
4. **Performance Tests**: Validates processing speed
5. **Error Tests**: Ensures proper error handling

### Running Tests

```bash
# Run converter tests
python test_enhanced_converter.py

# Run API tests
npm test
```

## Configuration

### Customization Options

You can customize the converter behavior by modifying:

- **Pattern matching**: Add custom page number or watermark patterns
- **Font sizes**: Adjust font size mapping for different document types
- **Timeout values**: Modify processing timeouts
- **File size limits**: Adjust maximum file size

### Environment Variables

```bash
PORT=3000                    # Server port
MAX_FILE_SIZE=52428800       # Maximum file size (50MB)
PROCESSING_TIMEOUT=300000    # Processing timeout (5 minutes)
```

## Troubleshooting

### Common Issues

1. **Conversion Fails**
   - Check if PDF is corrupted
   - Verify file size is within limits
   - Check server logs for detailed error

2. **Formatting Issues**
   - Ensure PDF has proper text layers
   - Check for scanned document quality
   - Verify OCR installation for scanned documents

3. **Performance Issues**
   - Monitor server resources
   - Check for large file processing
   - Verify timeout settings

### Debug Mode

Enable detailed logging by setting log level:

```python
logging.basicConfig(level=logging.DEBUG)
```

## API Documentation

### Health Check

```bash
GET /health
```

Returns server status and available endpoints.

### Error Responses

```json
{
  "success": false,
  "error": "Error description",
  "message": "Detailed error message",
  "fileInfo": {
    "originalName": "document.pdf",
    "fileSize": 1048576,
    "fileSizeMB": "1.00"
  }
}
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review server logs
3. Create an issue with detailed information
4. Include sample PDF for reproduction 