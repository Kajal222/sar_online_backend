import requests
import time
import os

BASE_URL = "http://localhost:3000"
EXTRACT_METADATA_ENDPOINT = "/extract-metadata"
TEST_FILES_DIR = "testsprite_tests/test_files"
TEST_FILES = [
    "anita_yuvraj_test.pdf",
    "Tej Karan - Jodhpur.pdf",
    "Ravinder Kaur - UK.pdf",
    "file-1752733837504-630102423.pdf",
    "pdf-1752741187792-923217221.pdf"
]

def test_rate_limiting_enforcement():
    url = BASE_URL + EXTRACT_METADATA_ENDPOINT
    headers = {}
    timeout = 30
    files = []
    # Prepare file handles for all test files to cycle through
    file_handles = []
    try:
        for filename in TEST_FILES:
            path = os.path.join(TEST_FILES_DIR, filename)
            f = open(path, "rb")
            file_handles.append(f)
        # We will send 105 requests in quick succession to trigger rate limiting
        # Cycle through the files to simulate realistic usage
        total_requests = 105
        rate_limit_exceeded = False
        rate_limit_status_codes = {429}
        rate_limit_error_messages = []
        for i in range(total_requests):
            file_index = i % len(file_handles)
            f = file_handles[file_index]
            f.seek(0)
            files = {"pdf": (os.path.basename(f.name), f, "application/pdf")}
            try:
                response = requests.post(url, files=files, headers=headers, timeout=timeout)
            except requests.RequestException as e:
                # Network or other request error, fail the test
                assert False, f"Request failed with exception: {e}"
            if response.status_code in rate_limit_status_codes:
                rate_limit_exceeded = True
                try:
                    json_resp = response.json()
                    if "error" in json_resp:
                        rate_limit_error_messages.append(json_resp["error"])
                    elif "message" in json_resp:
                        rate_limit_error_messages.append(json_resp["message"])
                except Exception:
                    # Response not JSON or no error message
                    pass
            else:
                # For non-rate limited responses, expect success or valid error codes (e.g. 200 or 4xx)
                assert response.status_code in (200, 400, 422), f"Unexpected status code {response.status_code} on request {i+1}"
        assert rate_limit_exceeded, "Rate limiting was not enforced after sending more than 100 requests per minute"
        # Optionally check that error messages are meaningful
        assert any(rate_limit_error_messages), "Rate limit error responses did not contain error messages"
    finally:
        for f in file_handles:
            f.close()

test_rate_limiting_enforcement()