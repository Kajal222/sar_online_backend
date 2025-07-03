const express = require("express");
const fs = require("fs");
const multer = require("multer");
const { PythonShell } = require("python-shell");
const cors = require("cors");
const { spawn } = require('child_process');
const path = require("path");
const app = express();

// Middleware
app.use(cors());
app.use(express.json());

// Configure multer for file uploads with validation
const storage = multer.diskStorage({
    destination: (req, file, cb) => {
        cb(null, 'uploads/');
    },
    filename: (req, file, cb) => {
        // Generate unique filename with timestamp
        const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
        cb(null, file.fieldname + '-' + uniqueSuffix + path.extname(file.originalname));
    }
});

const fileFilter = (req, file, cb) => {
    // Validate file type
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
        fileSize: 10 * 1024 * 1024 // 10MB limit
    }
});

// Utility function to get Python executable path
function getPythonPath() {
    // Try to use environment variable first, fallback to hardcoded path
    return process.env.PYTHON_PATH || 'C:\\Users\\Asus\\miniconda3\\envs\\saronline\\python.exe';
}

// Utility function to clean up files
function cleanupFile(filePath) {
    try {
        if (fs.existsSync(filePath)) {
            fs.unlinkSync(filePath);
        }
    } catch (error) {
        console.error('Error cleaning up file:', filePath, error);
    }
}

function parsePdf(pdfPath, callback) {
    const pythonProcess = spawn(getPythonPath(), ['scripts/pdf_parser.py', pdfPath]);
    console.log(pythonProcess, "pythonProcess")
    let output = '';
    let error = '';

    pythonProcess.stdout.on('data', (data) => {
        output += data.toString();
    });

    pythonProcess.stderr.on('data', (data) => {
        error += data.toString();
    });

    pythonProcess.on('close', (code) => {
        if (code !== 0) {
            callback(new Error(error || `Process exited with code ${code}`), null);
        } else {
            callback(null, output);
        }
    });
}
function parseextractPdf(pdfTextPath, field, callback) {
    const pythonProcess = spawn(getPythonPath(), ['scripts/metadata_extractor.py', pdfTextPath, field]);
    let output = '';
    let error = '';

    pythonProcess.stdout.on('data', (data) => {
        output += data.toString();
    });

    pythonProcess.stderr.on('data', (data) => {
        error += data.toString();
    });
    console.log(output, "output");
    console.log(error, "error");

    pythonProcess.on('close', (code) => {
        console.log(code, "code");

        if (code !== 0) {
            callback(new Error(error || `Process exited with code ${code}`), null);
        } else {
            callback(null, output);
        }
    });
}
app.post("/upload", upload.single("pdf"), async (req, res) => {
    console.log("/upload endpoint hit");
    
    try {
        if (!req.file) {
            console.error("No file uploaded");
            return res.status(400).json({ 
                error: "No file uploaded. Field name must be 'pdf'." 
            });
        }

        const filePath = req.file.path;
        const fileId = req.file.filename;
        const originalName = req.file.originalname;
        
        console.log("Uploaded file:", {
            originalName,
            fileId,
            filePath,
            size: req.file.size
        });

        if (!fs.existsSync(filePath)) {
            console.error("Uploaded file does not exist at:", filePath);
            return res.status(404).json({ 
                error: "Uploaded file not found on server." 
            });
        }

        // Validate file size
        if (req.file.size === 0) {
            cleanupFile(filePath);
            return res.status(400).json({ 
                error: "Uploaded file is empty." 
            });
        }

        res.json({ 
            fileId,
            originalName,
            size: req.file.size,
            message: "File uploaded successfully"
        });
        
    } catch (error) {
        console.error("Exception in /upload handler:", error);
        
        // Clean up file if it was uploaded but error occurred
        if (req.file && req.file.path) {
            cleanupFile(req.file.path);
        }
        
        res.status(500).json({ 
            error: "Internal server error during file upload." 
        });
    }
});
// /extract-metadata, /detect-paragraphs, /generate-docx
app.post("/detect-paragraphs", async (req, res) => {
    const tempTextPath = `./temp/${Date.now()}_text.txt`;
    fs.writeFileSync(tempTextPath, req.body.text);
    const pythonProcess = spawn(getPythonPath(), ['scripts/paragraph_detector.py', tempTextPath]);
    let output = '';
    let errorOutput = '';
    pythonProcess.stdout.on('data', (data) => {
        output += data.toString();
    });
    pythonProcess.stderr.on('data', (data) => {
        errorOutput += data.toString();
    });
    pythonProcess.on('close', (code) => {
        cleanupFile(tempTextPath);
        if (code !== 0) {
            return res.status(500).json({ error: errorOutput || `Python process exited with code ${code}` });
        }
        try {
            res.json(JSON.parse(output));
        } catch (e) {
            res.status(500).json({ error: "Failed to parse paragraphs output" });
        }
    });
});

app.post("/generate-docx", async (req, res) => {
    const metaPath = `./temp/${Date.now()}_meta.json`;
    const paraPath = `./temp/${Date.now()}_paras.json`;
    const outputPath = `./generated/${Date.now()}.docx`;
    fs.writeFileSync(metaPath, JSON.stringify(req.body.metadata));
    fs.writeFileSync(paraPath, JSON.stringify(req.body.paragraphs));
    PythonShell.run("scripts/docx_generator.py", {
        args: [metaPath, paraPath, outputPath]
    }, (err) => {
        cleanupFile(metaPath);
        cleanupFile(paraPath);
        if (err) return res.status(500).json({ error: err.message });
        res.json({ downloadLink: `/download/${outputPath.split("/").pop()}` });
    });
});

app.post("/extract-metadata", async (req, res) => {
    try {
        const { field, fileId } = req.body;
        
        // Validate required parameters
        if (!field || !fileId) {
            return res.status(400).json({ 
                error: "Both 'field' and 'fileId' are required." 
            });
        }

        // Validate field parameter
        const validFields = ['citationyear', 'neutralcitation', 'judge', 'courtname', 'party'];
        if (!validFields.includes(field.toLowerCase())) {
            return res.status(400).json({ 
                error: `Invalid field. Supported fields: ${validFields.join(', ')}` 
            });
        }

        console.log("Extracting metadata:", { field, fileId });

        const filePath = path.join(__dirname, "uploads", fileId);
        console.log("File path:", filePath);

        if (!fs.existsSync(filePath)) {
            return res.status(404).json({ 
                error: "File not found. Please upload the file first." 
            });
        }

        // Check if file is actually a PDF
        const fileExtension = path.extname(filePath).toLowerCase();
        if (fileExtension !== '.pdf') {
            return res.status(400).json({ 
                error: "File must be a PDF document." 
            });
        }

        // Use Promise-based approach for better error handling
        const extractMetadata = (pdfPath, fieldName) => {
            return new Promise((resolve, reject) => {
                const pythonProcess = spawn(getPythonPath(), ['scripts/metadata_extractor.py', pdfPath, fieldName]);
                
                let output = '';
                let error = '';
                let timeout;

                // Set timeout for Python process
                timeout = setTimeout(() => {
                    pythonProcess.kill();
                    reject(new Error('Metadata extraction timed out'));
                }, 30000); // 30 seconds timeout

                pythonProcess.stdout.on('data', (data) => {
                    output += data.toString();
                });

                pythonProcess.stderr.on('data', (data) => {
                    error += data.toString();
                });

                pythonProcess.on('close', (code) => {
                    clearTimeout(timeout);
                    
                    if (code !== 0) {
                        reject(new Error(error || `Python process exited with code ${code}`));
                    } else {
                        resolve(output.trim());
                    }
                });

                pythonProcess.on('error', (err) => {
                    clearTimeout(timeout);
                    reject(new Error(`Failed to start Python process: ${err.message}`));
                });
            });
        };

        const result = await extractMetadata(filePath, field);
        
        console.log("Metadata extraction result:", { field, result });
        
        res.json({ 
            field, 
            value: result,
            success: true 
        });

    } catch (error) {
        console.error("Error in /extract-metadata:", error);
        res.status(500).json({ 
            error: `Metadata extraction failed: ${error.message}`,
            success: false
        });
    }
});

// Global error handler for multer errors
app.use((error, req, res, next) => {
    if (error instanceof multer.MulterError) {
        if (error.code === 'LIMIT_FILE_SIZE') {
            return res.status(400).json({ 
                error: 'File too large. Maximum size is 10MB.' 
            });
        }
        return res.status(400).json({ 
            error: `Upload error: ${error.message}` 
        });
    }
    
    if (error.message === 'Only PDF files are allowed!') {
        return res.status(400).json({ 
            error: 'Only PDF files are allowed!' 
        });
    }
    
    next(error);
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

app.use("/download", express.static("generated"));

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`🚀 Server running on port ${PORT}`);
    console.log(`📁 Upload directory: ${path.join(__dirname, 'uploads')}`);
    console.log(`🐍 Python path: ${getPythonPath()}`);
});
