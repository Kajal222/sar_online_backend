import requests
import os

BASE_URL = "http://localhost:3000"
ENDPOINT = "/generate-docx"
TIMEOUT = 30
TEST_FILE_PATH = "testsprite_tests/test_files/anita_yuvraj_test.pdf"

def test_pdf_to_docx_conversion_success():
    url = BASE_URL + ENDPOINT
    headers = {}
    try:
        with open(TEST_FILE_PATH, "rb") as pdf_file:
            files = {"pdf": (os.path.basename(TEST_FILE_PATH), pdf_file, "application/pdf")}
            response = requests.post(url, files=files, headers=headers, timeout=TIMEOUT)
        # Validate response status code
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        # Validate content-type header for DOCX
        content_type = response.headers.get("Content-Type", "")
        expected_content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        assert content_type == expected_content_type, f"Expected Content-Type '{expected_content_type}', got '{content_type}'"
        # Validate content-disposition header for attachment with .docx filename
        content_disposition = response.headers.get("Content-Disposition", "")
        assert "attachment" in content_disposition.lower(), "Content-Disposition header missing 'attachment'"
        assert content_disposition.lower().endswith(".docx\"") or ".docx" in content_disposition.lower(), "Content-Disposition header missing .docx filename"
        # Validate response content is not empty
        assert response.content and len(response.content) > 0, "Response content is empty"
        # Additional heuristic: DOCX files are ZIP archives, check first 2 bytes for PK signature
        assert response.content[:2] == b"PK", "Response content does not start with PK signature, likely not a DOCX file"
    except requests.exceptions.RequestException as e:
        assert False, f"Request failed: {e}"

test_pdf_to_docx_conversion_success()