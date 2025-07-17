#!/usr/bin/env python3
"""
REST API Server for Dynamic Metadata Extraction System

This server provides HTTP endpoints for extracting metadata from legal documents.
Supports file uploads and text-based extraction with various configuration options.
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import tempfile
import json
import logging
from datetime import datetime
from werkzeug.utils import secure_filename
import traceback

# Import our extraction system
from scripts.configurable_extractor import ConfigurableMetadataExtractor, extract_all_metadata
from scripts.metadata_extractor import extract_text_from_pdf, extract_text_from_pdf_with_pdfplumber, extract_text_from_pdf_with_ocr
from scripts.legal_document_extractor import LegalDocumentExtractor, extract_legal_metadata

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'txt', 'doc', 'docx'}
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max file size

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize extractors
extractor = ConfigurableMetadataExtractor()
legal_extractor = LegalDocumentExtractor()

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_file(file_path):
    """Extract text from various file types"""
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == '.pdf':
        # Try multiple extraction methods
        text = extract_text_from_pdf(file_path)
        if not text.strip():
            text = extract_text_from_pdf_with_pdfplumber(file_path)
        if not text.strip():
            text = extract_text_from_pdf_with_ocr(file_path)
        return text
    elif ext == '.txt':
        try:
            with open(file_path, encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            with open(file_path, encoding='latin-1') as f:
                return f.read()
    else:
        # For other file types, try text extraction
        try:
            with open(file_path, encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            with open(file_path, encoding='latin-1') as f:
                return f.read()

# @app.route('/extract/legal', methods=['POST'])
# def extract_legal_document():
#     """
#     Extract legal document metadata in the specific format required
    
#     Request (Form Data):
#     - file: Uploaded PDF document file (optional)
#     - text: Text content (optional, if no file)
    
#     Request (JSON):
#     - text: Text content
    
#     Returns:
#     - JSON with extracted legal document metadata in the required format
#     """
#     try:
#         text = None
        
#         # Handle both form data and JSON requests
#         if request.is_json:
#             # JSON request
#             data = request.get_json()
#             if not data:
#                 return jsonify({'error': 'No JSON data provided'}), 400
            
#             text = data.get('text')
#             if not text:
#                 return jsonify({'error': 'No text provided in JSON'}), 400
                
#         else:
#             # Form data request
#             # Check if file was uploaded
#             if 'file' in request.files:
#                 file = request.files['file']
#                 if file.filename == '':
#                     return jsonify({'error': 'No file selected'}), 400
                
#                 if not allowed_file(file.filename):
#                     return jsonify({'error': 'File type not allowed'}), 400
                
#                 # Save uploaded file
#                 filename = secure_filename(file.filename)
#                 timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
#                 filename = f"{timestamp}_{filename}"
#                 file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
#                 file.save(file_path)
                
#                 # Extract text from file
#                 text = extract_text_from_file(file_path)
                
#                 # Clean up uploaded file
#                 os.remove(file_path)
                
#             elif 'text' in request.form:
#                 text = request.form['text']
#             else:
#                 return jsonify({'error': 'No file or text provided'}), 400
        
#         if not text or not text.strip():
#             return jsonify({'error': 'No text content found'}), 400
        
#         # Extract legal document metadata
#         metadata = legal_extractor.extract_to_json(text)
        
#         response = {
#             'metadata': metadata,
#             'text_length': len(text),
#             'timestamp': datetime.now().isoformat()
#         }
        
#         return jsonify(response)
        
#     except Exception as e:
#         logger.error(f"Error in extract_legal_document endpoint: {str(e)}")
#         logger.error(traceback.format_exc())
#         return jsonify({'error': str(e)}), 500

@app.errorhandler(413)
def too_large(e):
    """Handle file too large error"""
    return jsonify({'error': 'File too large. Maximum size is 50MB.'}), 413

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(e):
    """Handle internal server errors"""
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    print("🚀 Starting Dynamic Metadata Extraction API Server...")
    print("📖 Available endpoints:")
    print("  GET  /health                    - Health check")
    print("  POST /extract                   - Extract metadata from file/text")
    print("  POST /extract/file              - Extract metadata from file path")
    print("  POST /detect                    - Detect document type")
    print("  GET  /patterns                  - Get available patterns")
    print("  POST /patterns                  - Add custom pattern")
    print("\n🌐 Server will start on http://localhost:5000")
    print("📚 See README_API.md for detailed usage examples")
    
    app.run(host='0.0.0.0', port=5000, debug=True) 