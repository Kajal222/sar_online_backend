import requests
import os

def test_scanned_document_processing_with_ocr():
    base_url = "http://localhost:3000"
    endpoint = "/extract-metadata"
    url = base_url + endpoint
    test_file_path = "testsprite_tests/test_files/Ravinder Kaur - UK.pdf"
    tesseract_path = None  # Optionally set this if known, e.g. "/usr/bin/tesseract"

    if not os.path.isfile(test_file_path):
        raise FileNotFoundError(f"Test file not found: {test_file_path}")

    params = {}
    if tesseract_path:
        params['tesseract_path'] = tesseract_path

    with open(test_file_path, "rb") as pdf_file:
        files = {
            "pdf": (os.path.basename(test_file_path), pdf_file, "application/pdf")
        }
        try:
            response = requests.post(url, files=files, params=params, timeout=30)
            response.raise_for_status()
        except requests.RequestException as e:
            assert False, f"Request failed: {e}"

    try:
        json_resp = response.json()
    except ValueError:
        assert False, "Response is not valid JSON"

    # Validate top-level success flag
    assert "success" in json_resp, "Response missing 'success' field"
    assert json_resp["success"] is True, "Extraction was not successful"

    # Validate metadata presence and types
    metadata = json_resp.get("metadata")
    assert metadata is not None, "Response missing 'metadata' field"
    expected_metadata_fields = [
        "appellant", "respondent", "judgeName", "judgementType",
        "caseResult", "caseNumber", "courtName", "dateOfJudgement", "referredCases"
    ]
    for field in expected_metadata_fields:
        assert field in metadata, f"Metadata missing field '{field}'"
    # referredCases should be a list
    assert isinstance(metadata["referredCases"], list), "'referredCases' should be a list"

    # Validate fileInfo presence and types
    file_info = json_resp.get("fileInfo")
    assert file_info is not None, "Response missing 'fileInfo' field"
    assert "originalName" in file_info and isinstance(file_info["originalName"], str), "'fileInfo.originalName' missing or not string"
    assert "fileSize" in file_info and isinstance(file_info["fileSize"], (int, float)), "'fileInfo.fileSize' missing or not number"
    assert "uploadTime" in file_info and isinstance(file_info["uploadTime"], str), "'fileInfo.uploadTime' missing or not string"

    # Validate processingInfo presence and types
    processing_info = json_resp.get("processingInfo")
    assert processing_info is not None, "Response missing 'processingInfo' field"
    assert "extractionMethod" in processing_info and isinstance(processing_info["extractionMethod"], str), "'processingInfo.extractionMethod' missing or not string"
    assert "confidence" in processing_info and isinstance(processing_info["confidence"], (int, float)), "'processingInfo.confidence' missing or not number"
    assert "isScanned" in processing_info and isinstance(processing_info["isScanned"], bool), "'processingInfo.isScanned' missing or not boolean"
    assert "pageCount" in processing_info and isinstance(processing_info["pageCount"], (int, float)), "'processingInfo.pageCount' missing or not number"

    # Specifically check that OCR was used for scanned document
    assert processing_info["isScanned"] is True, "Document is not marked as scanned"
    # extractionMethod should indicate OCR usage (e.g. contain 'OCR' or 'ocr')
    assert "ocr" in processing_info["extractionMethod"].lower(), "Extraction method does not indicate OCR usage"

    # Confidence should be a reasonable number between 0 and 1
    confidence = processing_info["confidence"]
    assert 0.0 <= confidence <= 1.0, f"Confidence value out of range: {confidence}"

test_scanned_document_processing_with_ocr()