# Troubleshooting Guide: Metadata Extraction Issues

## Problem: "Cannot destructure property 'field' of 'req.body' as it is undefined"

This error occurs when the request body is not being parsed properly by Express.js.

## Root Causes & Solutions

### 1. **Request Format**
**Problem**: Request is not properly formatted as JSON or form data.

**Solution**: Send the request with either JSON or form data:
```javascript
// JSON format
{
    "field": "citationyear",
    "fileId": "existing-file.pdf"
}

// Form data format
const formData = new FormData();
formData.append('field', 'citationyear');
formData.append('fileId', 'existing-file.pdf');
```

### 2. **Missing Required Fields**
**Problem**: Required fields are missing from the request.

**Solution**: Ensure your request contains:
- `field`: The metadata field to extract (required)
- `fileId`: The ID of an existing uploaded PDF file (required)

### 3. **Middleware Order Issues**
**Problem**: Express middleware not configured properly.

**Solution**: ✅ **FIXED** - Added proper middleware configuration:
```javascript
app.use(cors());
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));
```

**Note**: The `/extract-metadata` endpoint expects `field` and `fileId` parameters. File uploads should be done separately via the `/upload` endpoint.

## Testing Your Fix

### Option 1: Use the Test Script
```bash
node test_extract_metadata.js
```

### Option 2: Use Curl Commands
```bash
# Make the script executable (Linux/Mac)
chmod +x test_curl_examples.sh

# Run the tests
./test_curl_examples.sh
```

### Option 3: Manual Testing
```bash
# Test with JSON data
curl -X POST "http://localhost:3000/extract-metadata" \
  -H "Content-Type: application/json" \
  -d '{"field": "citationyear", "fileId": "test-file.pdf"}'

# Test with form data
curl -X POST "http://localhost:3000/extract-metadata" \
  -F "field=citationyear" \
  -F "fileId=test-file.pdf"

# Test the debug endpoint
curl -X POST "http://localhost:3000/test-body" \
  -H "Content-Type: application/json" \
  -d '{"field": "citationyear", "fileId": "test-file.pdf"}'
```

## Debug Information

The server now includes debug middleware that logs:
- Request method and path
- Content-Type header
- Request body content
- Body type and keys

Check your server console for detailed request information.

## Common Client-Side Issues

### JavaScript/Fetch
```javascript
// ✅ Correct - JSON format
fetch('/extract-metadata', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        field: 'citationyear',
        fileId: 'existing-file.pdf'
    })
});

// ✅ Correct - Form data format
const formData = new FormData();
formData.append('field', 'citationyear');
formData.append('fileId', 'existing-file.pdf');

fetch('/extract-metadata', {
    method: 'POST',
    body: formData
});
```

### Axios
```javascript
// ✅ Correct - JSON format
axios.post('/extract-metadata', {
    field: 'citationyear',
    fileId: 'existing-file.pdf'
}, {
    headers: {
        'Content-Type': 'application/json'
    }
});

// ✅ Correct - Form data format
const formData = new FormData();
formData.append('field', 'citationyear');
formData.append('fileId', 'existing-file.pdf');

axios.post('/extract-metadata', formData, {
    headers: {
        ...formData.getHeaders()
    }
});
```

## Valid Field Values

The API accepts these field values:
- `citationyear`
- `neutralcitation`
- `judge`
- `courtname`
- `party`

## Error Response Format

The API now returns detailed error information:
```json
{
    "error": "Both 'field' and 'fileId' are required in the request body.",
    "received": { "field": null, "fileId": null },
    "bodyKeys": []
}
```

## Next Steps

1. **Restart your server** to apply the middleware changes
2. **Test with the provided scripts** to verify the fix
3. **Check your client code** to ensure proper request formatting
4. **Monitor server logs** for detailed request information

If the issue persists, the debug logs will help identify the exact problem. 