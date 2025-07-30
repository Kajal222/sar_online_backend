const express = require("express");
const fs = require("fs");
const multer = require("multer");
const cors = require("cors");
const { spawn } = require('child_process');
const path = require("path");
const rateLimit = require('express-rate-limit');
require("dotenv").config();

const app = express();

// Rate limiting configuration
const limiter = rateLimit({
    windowMs: 15 * 60 * 1000, // 15 minutes
    max: 1000, // limit each IP to 100 requests per windowMs
    message: {
        success: false,
        error: 'Too many requests from this IP, please try again later.',
        message: 'Rate limit exceeded. Please wait 15 minutes before making more requests.'
    },
    standardHeaders: true, // Return rate limit info in the `RateLimit-*` headers
    legacyHeaders: false, // Disable the `X-RateLimit-*` headers
});

// Apply rate limiting to all requests
app.use(limiter);

// Enable CORS
app.use(cors());
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));
app.use(express.json());
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
        const uploadDir = './uploads';
        // Create uploads directory if it doesn't exist
        if (!fs.existsSync(uploadDir)) {
            fs.mkdirSync(uploadDir, { recursive: true });
        }
        cb(null, uploadDir);
    },
    filename: function (req, file, cb) {
        // Generate unique filename with timestamp
        const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
        cb(null, file.fieldname + '-' + uniqueSuffix + path.extname(file.originalname));
    }
});

// File filter to only allow PDF files
const fileFilter = (req, file, cb) => {
    if (file.mimetype === 'application/pdf') {
        cb(null, true);
    } else {
        cb(new Error('Only PDF files are allowed!'), false);
    }
};

const upload = multer({
    storage: storage,
    fileFilter: fileFilter,
    limits: {
        fileSize: 50 * 1024 * 1024 // 50MB limit
    }
});

/**
 * Extract legal metadata from PDF using Python script
 * @param {string} pdfPath - Absolute path to the PDF file
 * @param {string} tesseractPath - Optional path to tesseract executable
 * @returns {Promise<Object>} - Extracted metadata
 */


/**
 * Clean up uploaded files
 * @param {string} filePath - Path to file to delete
 */
function cleanupFile(filePath) {
    try {
        if (fs.existsSync(filePath)) {
            fs.unlinkSync(filePath);
            console.log(`Cleaned up file: ${filePath}`);
        }
    } catch (error) {
        console.error(`Error cleaning up file ${filePath}:`, error);
    }
}

// Enhanced metadata extraction with async processing and better error handling
app.post('/extract-metadata', upload.single('pdf'), async (req, res) => {
    console.log('Received PDF upload request');

    // Check if file was uploaded
    if (!req.file) {
        return res.status(400).json({
            success: false,
            error: 'No PDF file uploaded',
            message: 'Please upload a PDF file using the "pdf" field name'
        });
    }

    const pdfPath = req.file.path;
    const originalName = req.file.originalname;
    const fileSize = req.file.size;
    const tesseractPath = req.query.tesseract_path || null;

    console.log(`Processing PDF: ${originalName} (${(fileSize / 1024 / 1024).toFixed(2)}MB) at ${pdfPath}`);

    // Set appropriate timeout based on file size
            const timeoutMs = fileSize > 5 * 1024 * 1024 ? 600000 : 300000; // 10 minutes for large files, 5 minutes for others

    try {
        function extractLegalMetadata(pdfPath, tesseractPath = null, timeout = 120000) {
            return new Promise((resolve, reject) => {
                // Prepare Python command arguments
                const pythonArgs = ['scripts/legal_document_extractor_simple.py', '--pdf', pdfPath];

                // Add tesseract path if provided
                if (tesseractPath) {
                    pythonArgs.push('--tesseract-path', tesseractPath);
                }

                console.log(`Executing: python ${pythonArgs.join(' ')} with ${timeout/1000}s timeout`);

                // Spawn Python process
                const python = spawn('python', pythonArgs, {
                    cwd: __dirname,
                    stdio: ['pipe', 'pipe', 'pipe']
                });

                let result = '';
                let errorOutput = '';

                // Collect stdout data
                python.stdout.on('data', (data) => {
                    result += data.toString('utf8');
                });

                // Collect stderr data
                python.stderr.on('data', (data) => {
                    errorOutput += data.toString();
                    console.error('Python stderr:', data.toString());
                });

                // Handle process completion
                python.on('close', (code) => {
                    console.log(`Python process exited with code: ${code}`);

                    if (code === 0) {
                        try {
                            const parsedResult = JSON.parse(result);
                            resolve(parsedResult);
                        } catch (parseError) {
                            console.error('JSON parsing error:', parseError);
                            reject(new Error(`Failed to parse JSON output: ${parseError.message}`));
                        }
                    } else {
                        reject(new Error(`Python script failed with code ${code}. Error: ${errorOutput}`));
                    }
                });

                // Handle process errors
                python.on('error', (error) => {
                    console.error('Python process error:', error);
                    reject(new Error(`Failed to start Python process: ${error.message}`));
                });

                // Set timeout for long-running processes
                const timeoutId = setTimeout(() => {
                    python.kill('SIGTERM');
                    reject(new Error(`PDF processing timeout after ${timeout/1000} seconds`));
                }, timeout);

                // Clear timeout on successful completion
                python.on('close', () => {
                    clearTimeout(timeoutId);
                });
            });
        }

        // Extract metadata using Python script with dynamic timeout
        const extractedData = await extractLegalMetadata(pdfPath, tesseractPath, timeoutMs);

        // Add file information to response
        const response = {
            success: true,
            metadata: extractedData,
            fileInfo: {
                originalName: originalName,
                fileSize: fileSize,
                fileSizeMB: (fileSize / 1024 / 1024).toFixed(2),
                uploadTime: new Date().toISOString()
            },
            processingInfo: {
                extractionMethod: extractedData.extractionMetadata?.pdf_processing?.extraction_method || 'Unknown',
                confidence: extractedData.extractionMetadata?.pdf_processing?.confidence || 0,
                isScanned: extractedData.extractionMetadata?.pdf_processing?.is_scanned || false,
                pageCount: extractedData.extractionMetadata?.pdf_processing?.page_count || 0,
                processingTime: new Date().toISOString()
            }
        };
        
        console.log(`✅ Successfully processed ${originalName}`);
        res.json(response);
        
    } catch (error) {
        console.error('Extraction error:', error);

        // Return error response with partial data if available
        res.status(500).json({
            success: false,
            error: error.message,
            fileInfo: {
                originalName: originalName,
                fileSize: fileSize,
                fileSizeMB: (fileSize / 1024 / 1024).toFixed(2),
                uploadTime: new Date().toISOString()
            },
            // Provide fallback data
            data: {
                appellant: 'Appellant',
                respondent: 'Respondent',
                judgeName: 'none',
                judgementType: 'Judgement',
                caseResult: 'Failed to extract case result'
            }
        });

    } finally {
        // Clean up uploaded file
        cleanupFile(pdfPath);
    }
});

// Health check endpoint
app.get('/health', (req, res) => {
    res.json({
        success: true,
        status: 'healthy',
        timestamp: new Date().toISOString(),
        version: '1.0.0',
        endpoints: {
            extract_metadata: '/extract-metadata',
            generate_docx: '/generate-docx',
            health: '/health'
        }
    });
});

/**
 * Generate a .docx file from a legal PDF document.
 * 
 * Features:
 * - Removes page numbers from headers/footers
 * - Removes watermarks and scanner artifacts
 * - Preserves original fonts, sizes, and alignment
 * - Maintains document structure and formatting
 * - Preserves content integrity for legal documents
 * 
 * Returns the .docx file as a download.
 */
//
// POST /generate-docx
//
// Convert an uploaded PDF into a Word document using the enhanced
// converter.  This endpoint accepts a single PDF file via
// multipart/form-data (field name `pdf`) and returns a `.docx` file
// download with the same basename.  It delegates the heavy lifting
// to a Python script (`scripts/enhanced_pdf_to_docx.py`) which
// implements advanced formatting preservation: removal of headers
// like page numbers and watermarks, font and alignment preservation,
// and cleanup of scanner artifacts.
//
app.post('/generate-docx', upload.single('pdf'), async (req, res) => {
    console.log('Received PDF for DOCX generation');
    // Validate that a file was actually uploaded
    if (!req.file) {
        return res.status(400).json({
            success: false,
            error: 'No PDF file uploaded',
            message: 'Please upload a PDF file using the "pdf" field name'
        });
    }
    const pdfPath = req.file.path;
    const originalName = req.file.originalname;
    const fileSize = req.file.size;
    // Ensure the temporary directory for output exists
    const tempDir = './temp';
    if (!fs.existsSync(tempDir)) {
        fs.mkdirSync(tempDir, { recursive: true });
    }
    // Construct the output DOCX path using the uploaded file's basename
    const docxFileName = path.basename(pdfPath, path.extname(pdfPath)) + '.docx';
    const docxPath = path.join(tempDir, docxFileName);
    console.log(`Converting PDF: ${originalName} (${(fileSize / 1024 / 1024).toFixed(2)}MB) to DOCX`);
    try {
        // Prepare the Python command arguments.  Use the enhanced
        // converter script rather than the older v5 converter.
        const pythonArgs = [
            'scripts/enhanced_pdf_to_docx.py',
            pdfPath,
            docxPath
        ];
        console.log(`Executing: python ${pythonArgs.join(' ')}`);
        // Spawn the Python process in the current working directory
        const python = spawn('python', pythonArgs, {
            cwd: __dirname,
            stdio: ['ignore', 'pipe', 'pipe']
        });
        let errorOutput = '';
        // Capture stderr for diagnostic purposes
        python.stderr.on('data', (data) => {
            errorOutput += data.toString();
            console.error('Python stderr:', data.toString());
        });
        // Timeout based on file size: larger files get more time
        const timeoutMs = fileSize > 5 * 1024 * 1024 ? 600000 : 300000; // 10 minutes for large files, 5 minutes for others
        // Kill the Python process if it runs too long
        const timeoutId = setTimeout(() => {
            console.error(`DOCX conversion timeout after ${timeoutMs/1000} seconds`);
            python.kill('SIGTERM');
        }, timeoutMs);
        // Await process exit
        await new Promise((resolve, reject) => {
            python.on('close', (code) => {
                clearTimeout(timeoutId);
                if (code === 0) {
                    resolve();
                } else {
                    reject(new Error(`Python script failed with code ${code}. Error: ${errorOutput}`));
                }
            });
            python.on('error', (error) => {
                clearTimeout(timeoutId);
                reject(new Error(`Failed to start Python process: ${error.message}`));
            });
        });
        // Stream the generated DOCX back to the client.  Use res.download
        // which sets appropriate headers and handles streaming.  Cleanup
        // temp files after the download completes.
        res.download(docxPath, docxFileName, (err) => {
            // Always remove the uploaded PDF and generated DOCX
            cleanupFile(pdfPath);
            cleanupFile(docxPath);
            if (err) {
                console.error('Error sending .docx:', err);
                res.status(500).json({
                    success: false,
                    error: 'Failed to send .docx file',
                    message: err.message
                });
            } else {
                console.log(`✅ Successfully converted ${originalName} to DOCX`);
            }
        });
    } catch (error) {
        console.error('DOCX generation error:', error);
        // Clean up temp files on error
        cleanupFile(pdfPath);
        cleanupFile(docxPath);
        res.status(500).json({
            success: false,
            error: error.message,
            message: 'Failed to generate .docx from PDF',
            fileInfo: {
                originalName: originalName,
                fileSize: fileSize,
                fileSizeMB: (fileSize / 1024 / 1024).toFixed(2)
            }
        });
    }
});

// Error handling middleware
app.use((error, req, res, next) => {
    if (error instanceof multer.MulterError) {
        if (error.code === 'LIMIT_FILE_SIZE') {
            return res.status(400).json({
                success: false,
                error: 'File too large',
                message: 'PDF file size must be less than 50MB'
            });
        }
        if (error.code === 'LIMIT_UNEXPECTED_FILE') {
            return res.status(400).json({
                success: false,
                error: 'Unexpected file field',
                message: 'Please use the correct field name for file upload'
            });
        }
    }

    if (error.message === 'Only PDF files are allowed!') {
        return res.status(400).json({
            success: false,
            error: 'Invalid file type',
            message: 'Only PDF files are allowed'
        });
    }

    console.error('Unhandled error:', error);
    res.status(500).json({
        success: false,
        error: 'Internal server error',
        message: error.message
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
    console.log(`Legal Document Metadata Extractor API running on port ${PORT}`);
    console.log(`Main endpoint: http://localhost:${PORT}/extract-metadata`);

    // Check if Python script exists
    const pythonScript = path.join(__dirname, 'scripts/legal_document_extractor_simple.py');
    if (!fs.existsSync(pythonScript)) {
        console.warn(`Warning: Python script not found at ${pythonScript}`);
        console.warn('Please ensure legal_document_extractor_simple.py is in the same directory as this Node.js file');
    }
});
