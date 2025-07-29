@echo off
echo ========================================
echo Legal Document Extractor API Test
echo ========================================
echo.

echo Waiting for rate limit to reset (15 minutes)...
echo You can press Ctrl+C to skip waiting and test immediately
echo.

REM Wait for 15 minutes (900 seconds) for rate limit to reset
timeout /t 900 /nobreak >nul 2>&1

echo.
echo Testing API endpoints...
echo.

echo 1. Testing Health Check:
curl -X GET http://localhost:3000/health
echo.
echo.

echo 2. Testing Metadata Extraction (Small PDF):
curl -X POST http://localhost:3000/extract-metadata -F "pdf=@uploads/Ravinder Kaur - UK.pdf"
echo.
echo.

echo 3. Testing DOCX Conversion:
curl -X POST http://localhost:3000/generate-docx -F "pdf=@uploads/anita_yuvraj_test.pdf" --output test_output.docx
echo.
echo.

echo 4. Testing Error Handling (No file):
curl -X POST http://localhost:3000/extract-metadata
echo.
echo.

echo ========================================
echo Test completed!
echo Check test_output.docx for converted file
echo ========================================
pause 