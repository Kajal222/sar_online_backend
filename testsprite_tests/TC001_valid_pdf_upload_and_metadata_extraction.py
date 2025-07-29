import requests
import os

BASE_URL = "http://localhost:3000"
ENDPOINT = "/extract-metadata"
TIMEOUT = 30

TEST_FILES_DIR = "testsprite_tests/test_files"
TEST_FILES = [
    "anita_yuvraj_test.pdf",
    "Tej Karan - Jodhpur.pdf",
    # Add other available PDF files in the directory for extended testing
]

def test_valid_pdf_upload_and_metadata_extraction():
    url = BASE_URL + ENDPOINT
    headers = {}
    for filename in TEST_FILES:
        file_path = os.path.join(TEST_FILES_DIR, filename)
        assert os.path.isfile(file_path), f"Test file not found: {file_path}"
        with open(file_path, "rb") as pdf_file:
            files = {"pdf": (filename, pdf_file, "application/pdf")}
            try:
                response = requests.post(url, files=files, headers=headers, timeout=TIMEOUT)
            except requests.RequestException as e:
                assert False, f"Request failed for file {filename}: {e}"
            assert response.status_code == 200, f"Unexpected status code {response.status_code} for file {filename}"
            try:
                json_resp = response.json()
            except ValueError:
                assert False, f"Response is not valid JSON for file {filename}"
            # Validate success flag
            assert "success" in json_resp, f"'success' field missing in response for file {filename}"
            assert json_resp["success"] is True, f"Extraction not successful for file {filename}"
            # Validate metadata presence and types
            metadata = json_resp.get("metadata")
            assert metadata is not None, f"'metadata' missing in response for file {filename}"
            required_fields = [
                "appellant",
                "respondent",
                "judgeName",
                "judgementType",
                "caseResult",
                "caseNumber",
                "courtName",
                "dateOfJudgement",
                "referredCases",
            ]
            for field in required_fields:
                assert field in metadata, f"Metadata field '{field}' missing for file {filename}"
            # Validate types
            assert isinstance(metadata["appellant"], str), f"Field 'appellant' is not string for file {filename}"
            assert isinstance(metadata["respondent"], str), f"Field 'respondent' is not string for file {filename}"
            assert isinstance(metadata["judgeName"], str), f"Field 'judgeName' is not string for file {filename}"
            assert isinstance(metadata["judgementType"], str), f"Field 'judgementType' is not string for file {filename}"
            assert isinstance(metadata["caseResult"], str), f"Field 'caseResult' is not string for file {filename}"
            assert isinstance(metadata["caseNumber"], str), f"Field 'caseNumber' is not string for file {filename}"
            assert isinstance(metadata["courtName"], str), f"Field 'courtName' is not string for file {filename}"
            assert isinstance(metadata["dateOfJudgement"], str), f"Field 'dateOfJudgement' is not string for file {filename}"
            assert isinstance(metadata["referredCases"], list), f"Field 'referredCases' is not list for file {filename}"
            # Validate fileInfo presence and types
            file_info = json_resp.get("fileInfo")
            assert file_info is not None, f"'fileInfo' missing in response for file {filename}"
            assert isinstance(file_info.get("originalName"), str), f"'originalName' missing or not string for file {filename}"
            assert isinstance(file_info.get("fileSize"), (int, float)), f"'fileSize' missing or not number for file {filename}"
            assert isinstance(file_info.get("uploadTime"), str), f"'uploadTime' missing or not string for file {filename}"
            # Validate processingInfo presence and types
            processing_info = json_resp.get("processingInfo")
            assert processing_info is not None, f"'processingInfo' missing in response for file {filename}"
            assert isinstance(processing_info.get("extractionMethod"), str), f"'extractionMethod' missing or not string for file {filename}"
            confidence = processing_info.get("confidence")
            assert isinstance(confidence, (int, float)), f"'confidence' missing or not number for file {filename}"
            assert 0.0 <= confidence <= 1.0, f"'confidence' out of range [0,1] for file {filename}"
            assert isinstance(processing_info.get("isScanned"), bool), f"'isScanned' missing or not boolean for file {filename}"
            page_count = processing_info.get("pageCount")
            assert isinstance(page_count, int), f"'pageCount' missing or not int for file {filename}"
            assert page_count > 0, f"'pageCount' should be positive for file {filename}"

test_valid_pdf_upload_and_metadata_extraction()