@echo off
echo ========================================
echo Quick API Test (Individual Commands)
echo ========================================
echo.
echo Choose an option:
echo 1. Test Health Check
echo 2. Test Metadata Extraction
echo 3. Test DOCX Conversion
echo 4. Test Error Handling
echo 5. Exit
echo.
set /p choice="Enter your choice (1-5): "

if "%choice%"=="1" goto health
if "%choice%"=="2" goto metadata
if "%choice%"=="3" goto docx
if "%choice%"=="4" goto error
if "%choice%"=="5" goto end

:health
echo.
echo Testing Health Check:
curl -X GET http://localhost:3000/health
echo.
goto end

:metadata
echo.
echo Testing Metadata Extraction:
curl -X POST http://localhost:3000/extract-metadata -F "pdf=@uploads/Ravinder Kaur - UK.pdf"
echo.
goto end

:docx
echo.
echo Testing DOCX Conversion:
curl -X POST http://localhost:3000/generate-docx -F "pdf=@uploads/anita_yuvraj_test.pdf" --output quick_test_output.docx
echo.
echo DOCX file saved as: quick_test_output.docx
goto end

:error
echo.
echo Testing Error Handling:
curl -X POST http://localhost:3000/extract-metadata
echo.
goto end

:end
echo.
echo Test completed!
pause 