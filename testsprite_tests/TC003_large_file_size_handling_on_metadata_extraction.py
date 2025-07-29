import os
import time
import requests

BASE_URL = "http://localhost:3000"
EXTRACT_METADATA_ENDPOINT = "/extract-metadata"
TIMEOUT = 30

def test_large_file_size_handling_on_metadata_extraction():
    # Files to test - large PDFs close to 50MB if available
    test_files = [
        "testsprite_tests/test_files/Tej Karan - Jodhpur.pdf",
        "testsprite_tests/test_files/anita_yuvraj_test.pdf",
        "testsprite_tests/test_files/Ravinder Kaur - UK.pdf"
    ]

    for file_path in test_files:
        assert os.path.isfile(file_path), f"Test file not found: {file_path}"
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        assert file_size_mb <= 50, f"Test file {file_path} exceeds 50MB limit"

        with open(file_path, "rb") as f:
            files = {"pdf": (os.path.basename(file_path), f, "application/pdf")}
            try:
                start_time = time.time()
                response = requests.post(
                    BASE_URL + EXTRACT_METADATA_ENDPOINT,
                    files=files,
                    timeout=TIMEOUT
                )
                duration = time.time() - start_time
            except requests.RequestException as e:
                assert False, f"Request failed for {file_path}: {e}"

        assert response.status_code == 200, f"Unexpected status code {response.status_code} for file {file_path}"
        try:
            json_resp = response.json()
        except Exception as e:
            assert False, f"Response is not valid JSON for file {file_path}: {e}"

        # Validate response schema and content
        assert "success" in json_resp, f"'success' field missing in response for file {file_path}"
        assert json_resp["success"] is True, f"Extraction failed for file {file_path}"

        metadata = json_resp.get("metadata")
        file_info = json_resp.get("fileInfo")
        processing_info = json_resp.get("processingInfo")

        # Validate metadata fields presence and types
        expected_metadata_fields = [
            "appellant", "respondent", "judgeName", "judgementType",
            "caseResult", "caseNumber", "courtName", "dateOfJudgement", "referredCases"
        ]
        assert isinstance(metadata, dict), f"'metadata' is not a dict for file {file_path}"
        for field in expected_metadata_fields:
            assert field in metadata, f"Metadata field '{field}' missing for file {file_path}"
        assert isinstance(metadata["referredCases"], list), f"'referredCases' is not a list for file {file_path}"

        # Validate fileInfo fields
        assert isinstance(file_info, dict), f"'fileInfo' is not a dict for file {file_path}"
        assert file_info.get("originalName") == os.path.basename(file_path), f"originalName mismatch for file {file_path}"
        assert isinstance(file_info.get("fileSize"), (int, float)), f"fileSize invalid type for file {file_path}"
        assert file_info.get("fileSize") > 0, f"fileSize should be positive for file {file_path}"
        assert isinstance(file_info.get("uploadTime"), str), f"uploadTime invalid type for file {file_path}"

        # Validate processingInfo fields
        assert isinstance(processing_info, dict), f"'processingInfo' is not a dict for file {file_path}"
        assert isinstance(processing_info.get("extractionMethod"), str), f"extractionMethod invalid type for file {file_path}"
        confidence = processing_info.get("confidence")
        assert isinstance(confidence, (int, float)), f"confidence invalid type for file {file_path}"
        assert 0 <= confidence <= 1, f"confidence out of range for file {file_path}"
        assert isinstance(processing_info.get("isScanned"), bool), f"isScanned invalid type for file {file_path}"
        page_count = processing_info.get("pageCount")
        assert isinstance(page_count, int), f"pageCount invalid type for file {file_path}"
        assert page_count > 0, f"pageCount should be positive for file {file_path}"

        # Performance check: response time should be under 30 seconds as per NFR
        assert duration < 30, f"Response time {duration}s exceeded 30 seconds for file {file_path}"

test_large_file_size_handling_on_metadata_extraction()