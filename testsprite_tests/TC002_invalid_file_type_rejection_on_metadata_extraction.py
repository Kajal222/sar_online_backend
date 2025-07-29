import requests

def test_invalid_file_type_rejection_on_metadata_extraction():
    url = "http://localhost:3000/extract-metadata"
    # Use a non-PDF file for testing - a simple text file created on the fly
    # Since no specific non-PDF file path is given, create a small in-memory file
    non_pdf_content = b"This is a test text file, not a PDF."
    files = {
        "pdf": ("test.txt", non_pdf_content, "text/plain")
    }
    try:
        response = requests.post(url, files=files, timeout=30)
    except requests.RequestException as e:
        assert False, f"Request failed: {e}"

    # Expecting a rejection due to invalid file type
    assert response.status_code in (400, 415), f"Expected 400 or 415 status code, got {response.status_code}"
    try:
        json_resp = response.json()
    except ValueError:
        assert False, "Response is not valid JSON"

    # The response should indicate failure and mention invalid file type
    assert "success" in json_resp, "Response JSON missing 'success' field"
    assert json_resp["success"] is False, "Expected success to be False for invalid file type"
    error_msg = json_resp.get("error") or json_resp.get("message") or ""
    assert any(keyword in error_msg.lower() for keyword in ["invalid file type", "unsupported file type", "file type"]), \
        f"Error message does not indicate invalid file type: {error_msg}"

test_invalid_file_type_rejection_on_metadata_extraction()