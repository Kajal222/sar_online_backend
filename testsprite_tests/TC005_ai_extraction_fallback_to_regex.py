import requests
import os

BASE_URL = "http://localhost:3000"
EXTRACT_METADATA_ENDPOINT = "/extract-metadata"
TIMEOUT = 30

# Files to test AI extraction fallback to regex
TEST_FILES = [
    "testsprite_tests/test_files/file-1752733837504-630102423.pdf",
    "testsprite_tests/test_files/pdf-1752741187792-923217221.pdf"
]

def test_ai_extraction_fallback_to_regex():
    for file_path in TEST_FILES:
        assert os.path.isfile(file_path), f"Test file not found: {file_path}"
        with open(file_path, "rb") as pdf_file:
            files = {"pdf": (os.path.basename(file_path), pdf_file, "application/pdf")}
            try:
                response = requests.post(
                    BASE_URL + EXTRACT_METADATA_ENDPOINT,
                    files=files,
                    timeout=TIMEOUT
                )
            except requests.RequestException as e:
                assert False, f"Request failed for {file_path}: {e}"

            assert response.status_code == 200, f"Unexpected status code {response.status_code} for {file_path}"
            try:
                data = response.json()
            except ValueError:
                assert False, f"Response is not valid JSON for {file_path}"

            # Validate response schema basics
            assert "success" in data, f"'success' field missing in response for {file_path}"
            assert isinstance(data["success"], bool), f"'success' field is not boolean for {file_path}"
            assert "metadata" in data, f"'metadata' field missing in response for {file_path}"
            assert isinstance(data["metadata"], dict), f"'metadata' field is not a dict for {file_path}"
            assert "processingInfo" in data, f"'processingInfo' field missing in response for {file_path}"
            assert isinstance(data["processingInfo"], dict), f"'processingInfo' field is not a dict for {file_path}"

            # Check fallback extraction method
            extraction_method = data["processingInfo"].get("extractionMethod", "").lower()
            # We expect either 'regex' or fallback indicator if AI failed
            assert extraction_method in ("regex", "ai-failed-regex-fallback", "fallback-regex"), (
                f"Extraction method is not fallback regex for {file_path}, got '{extraction_method}'"
            )

            # Check that metadata fields are present (may be empty strings if extraction partially failed)
            metadata = data["metadata"]
            expected_fields = [
                "appellant", "respondent", "judgeName", "judgementType",
                "caseResult", "caseNumber", "courtName", "dateOfJudgement", "referredCases"
            ]
            for field in expected_fields:
                assert field in metadata, f"Metadata field '{field}' missing for {file_path}"
            # referredCases should be a list
            assert isinstance(metadata.get("referredCases", []), list), f"'referredCases' is not a list for {file_path}"

            # Additional checks: confidence should be a number, isScanned boolean, pageCount number
            processing_info = data["processingInfo"]
            assert isinstance(processing_info.get("confidence", None), (int, float)), f"'confidence' not a number for {file_path}"
            assert isinstance(processing_info.get("isScanned", None), bool), f"'isScanned' not a boolean for {file_path}"
            assert isinstance(processing_info.get("pageCount", None), int), f"'pageCount' not an int for {file_path}"

test_ai_extraction_fallback_to_regex()