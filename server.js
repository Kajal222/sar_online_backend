const express = require("express");
const fs = require("fs");
const multer = require("multer");
const cors = require("cors");
const { spawn } = require('child_process');
const path = require("path");
const app = express();
const pdfParse = require('pdf-parse');
// Middleware
app.use(cors());
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// Debug middleware to log request details
app.use((req, res, next) => {
    console.log(`${req.method} ${req.path}`, {
        contentType: req.get('Content-Type'),
        body: req.body,
        bodyType: typeof req.body,
        bodyKeys: req.body ? Object.keys(req.body) : 'undefined'
    });
    next();
});

// Configure multer for file uploads
const storage = multer.diskStorage({
    destination: function (req, file, cb) {
        const uploadDir = path.join(__dirname, 'uploads');
        if (!fs.existsSync(uploadDir)) {
            fs.mkdirSync(uploadDir, { recursive: true });
        }
        cb(null, uploadDir);
    },
    filename: function (req, file, cb) {
        const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
        cb(null, file.fieldname + '-' + uniqueSuffix + path.extname(file.originalname));
    }
});

const upload = multer({ 
    storage: storage,
    limits: {
        fileSize: 50 * 1024 * 1024 // 50MB limit
    },
    fileFilter: function (req, file, cb) {
        // Accept PDF files and images
        const allowedTypes = [
            'application/pdf',
            'image/jpeg',
            'image/jpg', 
            'image/png',
            'image/tiff',
            'image/bmp'
        ];
        
        if (allowedTypes.includes(file.mimetype)) {
            cb(null, true);
        } else {
            cb(new Error('Only PDF files and images (JPEG, PNG, TIFF, BMP) are supported'), false);
        }
    }
});

// Utility function to get Python path
function getPythonPath() {
    return process.env.PYTHON_PATH || 'python';
}

// Utility function to clean up files
function cleanupFile(filePath) {
    try {
        if (fs.existsSync(filePath)) {
            fs.unlinkSync(filePath);
            console.log(`Cleaned up file: ${filePath}`);
        }
    } catch (error) {
        console.error(`Failed to cleanup file ${filePath}:`, error);
    }
}

// Main endpoint for legal document extraction
app.post("/extract/legal", upload.single("file"), async (req, res) => {
    console.log("/extract/legal endpoint hit");
    
    try {
        let processingMethod = '';
        let filePath = null;
        let extractedText = '';
        
        // Handle different input types
        if (req.file) {
            // File upload handling
            console.log("Processing uploaded file:", req.file.originalname);
            console.log("File type:", req.file.mimetype);
            console.log("File size:", req.file.size, "bytes");
            
            filePath = req.file.path;
            processingMethod = 'file_upload';
            
        } else if (req.body.text) {
            // Direct text input for testing
            extractedText = req.body.text;
            processingMethod = 'text_input';
            console.log("Processing direct text input, length:", extractedText.length);
            
        } else {
            return res.status(400).json({ 
                error: "No input provided. Please upload a PDF/image file or provide text content.",
                supported_formats: ["PDF", "JPEG", "PNG", "TIFF", "BMP"],
                success: false
            });
        }
        
        console.log("Starting AI-powered legal metadata extraction...");
        
        // Call the comprehensive AI extractor
        const extractLegalMetadata = (inputPath, inputText) => {
            return new Promise((resolve, reject) => {
                
                // Prepare Python command arguments
                let pythonArgs = ['scripts/legal_document_extractor_simple.py'];
                
                if (inputPath) {
                    // File processing
                    pythonArgs.push('--file', inputPath);
                } else if (inputText) {
                    // Text processing
                    pythonArgs.push('--text', inputText);
                } else {
                    reject(new Error('No input provided to Python script'));
                    return;
                }
                
                console.log("Executing Python command:", getPythonPath(), pythonArgs.join(' '));
                
                // Spawn Python process with enhanced configuration
                const pythonProcess = spawn(getPythonPath(), pythonArgs, {
                    env: {
                        ...process.env,
                        OPENAI_API_KEY: process.env.OPENAI_API_KEY,
                        PYTHONIOENCODING: 'utf-8',
                        PYTHONUNBUFFERED: '1'
                    },
                    maxBuffer: 1024 * 1024 * 20, // 20MB buffer for large outputs
                    timeout: 120000 // 2 minutes timeout for AI processing
                });
                
                let output = '';
                let error = '';
                let processStartTime = Date.now();
                
                pythonProcess.stdout.on('data', (data) => {
                    output += data.toString();
                    console.log(`Python output received (${data.length} bytes)`);
                });

                pythonProcess.stderr.on('data', (data) => {
                    error += data.toString();
                    console.log("Python stderr:", data.toString());
                });

                pythonProcess.on('close', (code) => {
                    const processingTime = Date.now() - processStartTime;
                    console.log(`Python process completed in ${processingTime}ms with exit code ${code}`);
                    
                    if (code !== 0) {
                        console.error("Python process failed:", error);
                        reject(new Error(error || `Python process exited with code ${code}`));
                    } else {
                        try {
                            // Parse the JSON output
                            const cleanOutput = output.trim();
                            
                            // Handle potential multiple JSON objects in output
                            let jsonStart = cleanOutput.indexOf('{');
                            let jsonEnd = cleanOutput.lastIndexOf('}');
                            
                            if (jsonStart !== -1 && jsonEnd !== -1) {
                                const jsonString = cleanOutput.substring(jsonStart, jsonEnd + 1);
                                const result = JSON.parse(jsonString);
                                
                                // Log extraction results
                                console.log("✓ AI Extraction Results:");
                                console.log("  Appellant:", result.appellant);
                                console.log("  Respondent:", result.respondent);
                                console.log("  Judge:", result.judgeName);
                                console.log("  Case Number:", result.caseHistoryRequest?.caseNumber);
                                console.log("  Case Year:", result.caseHistoryRequest?.year);
                                console.log("  Extraction Method:", result.extraction_method);
                                
                                resolve(result);
                            } else {
                                reject(new Error("No valid JSON found in Python output"));
                            }
                            
                        } catch (parseError) {
                            console.error("JSON parsing failed:", parseError);
                            console.error("Raw output (first 1000 chars):", output.substring(0, 1000));
                            reject(new Error(`Failed to parse extraction results: ${parseError.message}`));
                        }
                    }
                });

                pythonProcess.on('error', (err) => {
                    console.error("Python process spawn error:", err);
                    reject(new Error(`Failed to start AI extraction process: ${err.message}`));
                });

                // Handle process timeout
                setTimeout(() => {
                    if (!pythonProcess.killed) {
                        pythonProcess.kill();
                        reject(new Error('AI extraction timed out after 2 minutes'));
                    }
                }, 120000);
            });
        };

        // Execute extraction
        const metadata = await extractLegalMetadata(filePath, extractedText);
        
        // Clean up uploaded file
        if (filePath) {
            cleanupFile(filePath);
        }
        
        console.log("✓ Legal metadata extraction completed successfully");
        
        // Prepare comprehensive response
        const response = {
            success: true,
            timestamp: new Date().toISOString(),
            processing_method: processingMethod,
            extraction_method: metadata.extraction_method || 'Unknown',
            
            // Core metadata
            metadata: metadata,
            
            // Key extracted fields for easy access
            key_fields: {
                appellant: metadata.appellant,
                respondent: metadata.respondent,
                judge: metadata.judgeName,
                case_number: metadata.caseHistoryRequest?.caseNumber,
                case_year: metadata.caseHistoryRequest?.year,
                case_type: metadata.ai_metadata?.case_type,
                case_status: metadata.ai_metadata?.case_status,
                court_location: metadata.ai_metadata?.court_location,
                judgment_type: metadata.judgementType,
                case_result: metadata.caseResult
            },
            
            // Processing info
            processing_info: {
                input_type: req.file ? req.file.mimetype : 'text/plain',
                file_size: req.file ? req.file.size : extractedText.length,
                file_name: req.file ? req.file.originalname : 'text_input',
                text_length: extractedText.length || 'processed_from_file'
            },
            
            // API info
            api_info: {
                version: "2.0",
                capabilities: [
                    "PDF text extraction",
                    "Image OCR processing", 
                    "Scanned document processing",
                    "AI-powered entity recognition",
                    "Indian legal document parsing",
                    "Multi-format support"
                ],
                supported_formats: ["PDF", "JPEG", "PNG", "TIFF", "BMP", "Text"]
            }
        };
        
        res.json(response);
        
    } catch (error) {
        console.error("❌ Error in /extract/legal:", error);
        
        // Clean up uploaded file on error
        if (req.file && req.file.path) {
            cleanupFile(req.file.path);
        }
        
        // Determine error type and message
        let errorMessage = "Legal document extraction failed";
        let errorCode = 500;
        
        if (error.message.includes("timed out")) {
            errorMessage = "Extraction timed out. Please try with a smaller document or try again later.";
            errorCode = 408;
        } else if (error.message.includes("OPENAI_API_KEY")) {
            errorMessage = "AI service not configured. Please contact administrator.";
            errorCode = 503;
        } else if (error.message.includes("Failed to parse")) {
            errorMessage = "Document format not supported or corrupted.";
            errorCode = 422;
        } else if (error.message.includes("No text content")) {
            errorMessage = "No readable content found in the document.";
            errorCode = 422;
        } else {
            errorMessage = error.message;
        }
        
        const errorResponse = {
            success: false,
            error: errorMessage,
            error_type: error.constructor.name,
            timestamp: new Date().toISOString(),
            supported_formats: ["PDF", "JPEG", "PNG", "TIFF", "BMP"],
            help: {
                message: "Ensure your document is a valid legal document with readable text",
                tips: [
                    "For scanned documents, ensure good image quality",
                    "PDF files should contain text (not just images)",
                    "Supported languages: English (legal documents)",
                    "Maximum file size: 50MB"
                ]
            }
        };
        
        // Add debug info in development
        if (process.env.NODE_ENV === 'development') {
            errorResponse.debug = {
                stack: error.stack,
                arguments: process.argv,
                environment: {
                    node_version: process.version,
                    openai_configured: !!process.env.OPENAI_API_KEY
                }
            };
        }
        
        res.status(errorCode).json(errorResponse);
    }
});

// Health check endpoint
app.get("/extract/legal/health", (req, res) => {
    const health = {
        status: "healthy",
        timestamp: new Date().toISOString(),
        version: "2.0",
        services: {
            openai: !!process.env.OPENAI_API_KEY,
            python: true, // We assume Python is available
            file_upload: true,
            ocr: true // We assume OCR libraries are installed
        },
        capabilities: [
            "PDF text extraction",
            "Image OCR processing",
            "AI-powered extraction", 
            "Multi-format support"
        ]
    };
    
    res.json(health);
});

// Get supported formats endpoint
app.get("/extract/legal/formats", (req, res) => {
    res.json({
        supported_formats: {
            "application/pdf": {
                description: "PDF documents with text or images",
                max_size: "50MB",
                processing: ["text_extraction", "ocr_fallback"]
            },
            "image/jpeg": {
                description: "JPEG images of documents",
                max_size: "50MB", 
                processing: ["ocr"]
            },
            "image/png": {
                description: "PNG images of documents",
                max_size: "50MB",
                processing: ["ocr"]
            },
            "image/tiff": {
                description: "TIFF images of documents",
                max_size: "50MB",
                processing: ["ocr"]
            },
            "image/bmp": {
                description: "BMP images of documents", 
                max_size: "50MB",
                processing: ["ocr"]
            },
            "text/plain": {
                description: "Direct text input",
                max_size: "10MB",
                processing: ["ai_extraction"]
            }
        },
        extraction_fields: [
            "appellant",
            "respondent", 
            "judgeName",
            "caseNumber",
            "caseYear",
            "courtName",
            "judgmentType",
            "caseResult",
            "appellantAdvocate",
            "respondentAdvocate",
            "caseType",
            "citation"
        ]
    });
});

// 404 handler
app.use((req, res) => {
    res.status(404).json({ 
        error: 'Endpoint not found' 
    });
});

// Global error handler
app.use((error, req, res, next) => {
    console.error('Unhandled error:', error);
    res.status(500).json({ 
        error: 'Internal server error' 
    });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`🚀 Server running on port ${PORT}`);
    console.log(`📁 Upload directory: ${path.join(__dirname, 'uploads')}`);
    console.log(`🐍 Python path: ${getPythonPath()}`);
});
