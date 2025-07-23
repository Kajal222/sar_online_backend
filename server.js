const express = require("express");
const fs = require("fs");
const multer = require("multer");
const cors = require("cors");
const { spawn } = require('child_process');
const path = require("path");
const pdfParse = require("pdf-parse");
const { OpenAI } = require("openai");
require("dotenv").config();

const app = express();
const openai = new OpenAI({
    apiKey: process.env.OPENAI_API_KEY,
});

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


app.post('/extract-parties', upload.single('pdf'), async (req, res) => {
    try {
        if (!req.file) {
            return res.status(400).json({ error: 'No PDF file uploaded' });
        }

        // Read file as buffer
        const dataBuffer = fs.readFileSync(req.file.path);

        // Parse PDF to text
        const pdfData = await pdfParse(dataBuffer);
        const text = pdfData.text;

        // Prompt to extract metadata
        const prompt = `
  You are a legal document analysis assistant. Given the following court judgment content, extract only the following:
  1. Appellant Name(s)
  2. Respondent Name(s)
  
  Return response in this JSON format:
  {
    "appellant": "...",
    "respondent": "..."
  }
  
  CONTENT:
  ${text}
  `;

        // Send to OpenAI
        const completion = await openai.chat.completions.create({
            model: 'gpt-4o',
            messages: [{
                role: 'user', content: `Extract the following fields and return ONLY valid JSON with these exact keys: 1. "appellants": Look for words like "Appellant", "Petitioner", or "Petitioners" — these are mostly found on the first page. There can be multiple names, so return them in an array format. Extract only the main entity names (e.g., remove address, "through Secretary", etc.).

2. "respondents": Look for words like "Respondent" or "Respondents", also typically on the first page. Extract all respondent names in an array. Same as appellants, extract only the main names.
3. "judge_name": Check for presence of "Judgment" or "Order" in the document. Judge names are often mentioned in dedicated paragraphs or at the end of the document like "(ANIL KSHETARPAL) JUDGE". Extract the full name of the judge, excluding prefixes like "Justice", "Hon'ble", etc.

  CONTENT:
  ${text}
  
  Return response in this JSON format:
  {
    "appellant": "...",
    "respondent": "..."
    "judge_name:": "..."
  }` }],
            max_tokens: 2000,
            temperature: 0.3
        });

        let resultText = completion.choices[0]?.message?.content || '{}';

        // Sanitize: Remove code block markers and language tags
        resultText = resultText.replace(/```json\s*|```/g, '').trim();

        let parsedJSON = {};
        try {
            parsedJSON = JSON.parse(resultText);
        } catch (err) {
            return res.status(500).json({
                error: 'Failed to parse AI response. Content was:',
                content: resultText,
            });
        }

        res.json(parsedJSON);
    } catch (err) {
        console.error(err);
        res.status(500).json({ error: 'Internal server error', details: err.message });
    } finally {
        // Cleanup uploaded file
        if (req.file) fs.unlinkSync(req.file.path);
    }
});

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
    const tesseractPath = req.query.tesseract_path || null;

    console.log(`Processing PDF: ${originalName} at ${pdfPath}`);

    try {
        function extractLegalMetadata(pdfPath, tesseractPath = null) {
            return new Promise((resolve, reject) => {
                // Prepare Python command arguments
                const pythonArgs = ['scripts/legal_document_extractor_simple.py', '--pdf', pdfPath];

                // Add tesseract path if provided
                if (tesseractPath) {
                    pythonArgs.push('--tesseract-path', tesseractPath);
                }

                console.log(`Executing: python ${pythonArgs.join(' ')}`);

                // Spawn Python process
                const python = spawn('python', pythonArgs, {
                    cwd: __dirname, // Ensure we're in the correct directory
                    stdio: ['pipe', 'pipe', 'pipe']
                });

                let result = '';
                let errorOutput = '';

                // Collect stdout data
                python.stdout.on('data', (data) => {
                    result += data.toString();
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
                setTimeout(() => {
                    python.kill('SIGTERM');
                    reject(new Error('PDF processing timeout after 2 minutes'));
                }, 120000); // 2 minutes timeout
            });
        }
        // Extract metadata using Python script
        const extractedData = await extractLegalMetadata(pdfPath, tesseractPath);

        // Add file information to response
        const response = {
            success: true,
            metadata: extractedData,
            fileInfo: {
                originalName: originalName,
                fileSize: req.file.size,
                uploadTime: new Date().toISOString()
            },
            processingInfo: {
                extractionMethod: extractedData.extractionMetadata?.pdf_processing?.extraction_method || 'Unknown',
                confidence: extractedData.extractionMetadata?.pdf_processing?.confidence || 0,
                isScanned: extractedData.extractionMetadata?.pdf_processing?.is_scanned || false,
                pageCount: extractedData.extractionMetadata?.pdf_processing?.page_count || 0
            }
        };
        
        res.json(response);
        
    } catch (error) {
        console.error('Extraction error:', error);

        // Return error response with partial data if available
        res.status(500).json({
            success: false,
            error: error.message,
            fileInfo: {
                originalName: originalName,
                fileSize: req.file.size,
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
