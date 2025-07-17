# Dynamic Metadata Extraction System

A flexible and configurable metadata extraction system designed for legal documents of various types.

## Features

- **Dynamic Field Extraction**: Automatically detects and extracts different types of fields based on field names
- **Document Type Detection**: Automatically identifies document types (Supreme Court, High Court, Contracts, etc.)
- **Configurable Patterns**: Load extraction patterns from JSON configuration files
- **Multiple Extraction Methods**: Supports regex, NLP, and contextual extraction
- **Extensible**: Easy to add custom patterns for new document types or fields
- **Robust Text Extraction**: Multiple PDF extraction methods (PyMuPDF, pdfplumber, OCR)

## Architecture

### Core Components

1. **ConfigurableMetadataExtractor**: Main extraction engine
2. **ExtractionPattern**: Data structure for defining extraction patterns
3. **Configuration System**: JSON-based pattern management
4. **Document Type Detection**: Automatic document classification

### Supported Document Types

- Supreme Court judgments
- High Court judgments  
- District Court orders
- Tribunal decisions
- Legal contracts
- Legislation/Acts
- General legal documents

## Usage

### Basic Usage

```python
from configurable_extractor import ConfigurableMetadataExtractor

# Initialize extractor
extractor = ConfigurableMetadataExtractor()

# Extract specific field
text = "Your document text here..."
result = extractor.extract_metadata(text, "judge")
print(result)

# Extract all fields
all_metadata = extractor.extract_all_fields(text)
print(all_metadata)
```

### Command Line Usage

```bash
# Extract specific field
python configurable_extractor.py document.pdf judge

# Extract all fields
python configurable_extractor.py document.pdf all

# Detect document type and extract relevant fields
python configurable_extractor.py document.pdf detect

# Use custom configuration
python configurable_extractor.py document.pdf all custom_config.json
```

### Using Configuration Files

```python
# Load custom configuration
extractor = ConfigurableMetadataExtractor("my_config.json")

# Extract with custom patterns
result = extractor.extract_metadata(text, "custom_field")
```

## Field Types

### Predefined Fields

- **citation_year**: Extract year from citation numbers
- **neutral_citation**: Extract full citation numbers
- **court_name**: Extract court/tribunal names
- **judge**: Extract judge/magistrate names
- **decision_date**: Extract decision dates
- **petitioner**: Extract petitioner/appellant information
- **respondent**: Extract respondent/defendant information
- **case_type**: Extract case types (Writ Petition, Civil Appeal, etc.)
- **subject_matter**: Extract subject matter

### Dynamic Fields

The system can automatically extract fields based on field names:

- **date**: Any date-related field
- **name/party**: Person or organization names
- **number/id**: Various number formats
- **amount/money**: Monetary amounts
- **address**: Geographic locations

### Custom Fields

Add custom extraction patterns:

```python
extractor.add_custom_pattern(
    field_name="custom_field",
    patterns=[
        r"Custom Field:\s*([^\n]+)",
        r"Special Value:\s*([^\n]+)"
    ],
    extraction_type="regex",
    description="Extract custom field values"
)
```

## Configuration File Format

```json
{
  "document_types": {
    "supreme_court": {
      "description": "Supreme Court judgments and orders",
      "patterns": {
        "citation_year": {
          "patterns": [
            "NEUTRAL CITATION NO\\.\\s*(\\d{4}):",
            "Citation No\\.\\s*(\\d{4})"
          ],
          "extraction_type": "regex",
          "description": "Extract year from citation numbers"
        }
      }
    }
  },
  "common_patterns": {
    "dates": {
      "patterns": [
        "(\\d{1,2}[\\/\\-]\\d{1,2}[\\/\\-]\\d{2,4})"
      ],
      "extraction_type": "regex",
      "description": "Common date patterns"
    }
  },
  "post_processing": {
    "clean": "Remove extra whitespace",
    "normalize": "Convert to uppercase",
    "validate": "Validate extracted data"
  }
}
```

## Extraction Methods

### 1. Regex Extraction
- Pattern-based text extraction
- Supports multiple patterns per field
- Case-insensitive matching

### 2. NLP Extraction
- Named Entity Recognition (NER)
- Person, Organization, Location detection
- Language-aware extraction

### 3. Contextual Extraction
- Field name-based pattern generation
- Automatic pattern creation from field names
- Fallback extraction method

### 4. Positional Extraction
- Position-based extraction (future enhancement)
- Layout-aware extraction
- Table and form field extraction

## Text Extraction Methods

### PDF Processing

1. **PyMuPDF (Primary)**: Fast and reliable text extraction
2. **pdfplumber**: Better handling of complex layouts
3. **OCR (Tesseract)**: For scanned documents and images

### Text Processing

- UTF-8 and Latin-1 encoding support
- Automatic encoding detection
- Error handling and logging

## Error Handling

- Graceful handling of invalid regex patterns
- Fallback extraction methods
- Comprehensive logging
- Exception handling for file operations

## Performance Optimization

- Pattern caching
- Efficient regex compilation
- Lazy loading of NLP models
- Memory-efficient text processing

## Extending the System

### Adding New Document Types

1. Define patterns in configuration file
2. Add document type detection logic
3. Test with sample documents

### Adding New Field Types

1. Implement extraction logic in `_extract_dynamically`
2. Add field type detection
3. Update documentation

### Custom Post-Processing

1. Implement post-processing logic in `_post_process`
2. Add validation rules
3. Configure in pattern definition

## Best Practices

1. **Use Specific Patterns**: Define specific patterns for known document types
2. **Fallback to Dynamic**: Use dynamic extraction for unknown fields
3. **Validate Results**: Implement validation for critical fields
4. **Log Extractions**: Enable logging for debugging
5. **Test Thoroughly**: Test with various document formats

## Troubleshooting

### Common Issues

1. **No Results**: Check if patterns match document format
2. **Encoding Errors**: Ensure proper file encoding
3. **Memory Issues**: Process large documents in chunks
4. **Performance**: Use specific patterns instead of dynamic extraction

### Debugging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable detailed logging
extractor = ConfigurableMetadataExtractor()
result = extractor.extract_metadata(text, field)
```

## Dependencies

- spacy (NLP processing)
- PyMuPDF (PDF text extraction)
- pdfplumber (Alternative PDF extraction)
- pytesseract (OCR)
- pdf2image (PDF to image conversion)

## Installation

```bash
pip install spacy PyMuPDF pdfplumber pytesseract pdf2image
python -m spacy download en_core_web_sm
```

## License

This system is designed for production use with proper error handling, logging, and extensibility features. 