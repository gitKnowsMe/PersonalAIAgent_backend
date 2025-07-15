# Documents API

Manage PDF document uploads, processing, and retrieval.

## Endpoints Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/documents/upload` | Upload and process PDF |
| GET | `/api/v1/documents/` | List user documents |
| GET | `/api/v1/documents/{id}` | Get document details |
| DELETE | `/api/v1/documents/{id}` | Delete document |

## Upload Document

Upload and process a PDF document.

```http
POST /api/v1/documents/upload
```

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

**Request Body:**
- `file`: PDF file (multipart/form-data)

**Response:**
```json
{
  "id": 1,
  "filename": "document.pdf",
  "original_filename": "My Document.pdf",
  "file_size": 1048576,
  "document_type": "financial",
  "processing_status": "completed",
  "created_at": "2024-01-01T00:00:00Z",
  "processed_at": "2024-01-01T00:01:30Z",
  "chunk_count": 45,
  "metadata": {
    "page_count": 10,
    "classification_confidence": 0.92,
    "processing_time": 90.5
  }
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -H "Authorization: Bearer <token>" \
  -F "file=@/path/to/document.pdf"
```

### Document Types

The system automatically classifies documents:

- **financial**: Bank statements, invoices, receipts
- **long_form**: Research papers, reports, contracts (20+ pages)
- **generic**: Resumes, letters, personal documents

### Processing Status

- `pending`: Upload received, processing not started
- `processing`: Document being analyzed and chunked
- `completed`: Ready for queries
- `failed`: Processing error occurred

## List Documents

Retrieve user's uploaded documents.

```http
GET /api/v1/documents/
```

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Maximum records to return (default: 100)
- `document_type` (optional): Filter by type (`financial`, `long_form`, `generic`)
- `status` (optional): Filter by processing status

**Response:**
```json
{
  "documents": [
    {
      "id": 1,
      "filename": "bank_statement.pdf",
      "original_filename": "Chase Bank Statement Jan 2024.pdf",
      "file_size": 856432,
      "document_type": "financial",
      "processing_status": "completed",
      "created_at": "2024-01-01T00:00:00Z",
      "processed_at": "2024-01-01T00:01:15Z",
      "chunk_count": 23
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 100
}
```

**Example:**
```bash
curl -X GET "http://localhost:8000/api/v1/documents/?document_type=financial&limit=10" \
  -H "Authorization: Bearer <token>"
```

## Get Document Details

Retrieve detailed information about a specific document.

```http
GET /api/v1/documents/{id}
```

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "id": 1,
  "filename": "document.pdf",
  "original_filename": "My Document.pdf",
  "file_size": 1048576,
  "document_type": "financial",
  "processing_status": "completed",
  "created_at": "2024-01-01T00:00:00Z",
  "processed_at": "2024-01-01T00:01:30Z",
  "chunk_count": 45,
  "metadata": {
    "page_count": 10,
    "classification_confidence": 0.92,
    "processing_time": 90.5,
    "text_length": 15420,
    "language": "en"
  },
  "chunks": [
    {
      "id": 1,
      "content_preview": "Account Summary for January 2024...",
      "chunk_index": 0,
      "chunk_size": 500
    }
  ]
}
```

## Delete Document

Remove a document and its associated data.

```http
DELETE /api/v1/documents/{id}
```

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "message": "Document deleted successfully",
  "deleted_id": 1
}
```

**Example:**
```bash
curl -X DELETE "http://localhost:8000/api/v1/documents/1" \
  -H "Authorization: Bearer <token>"
```

!!! warning "Permanent Deletion"
    Deleting a document removes the file, all chunks, and vector embeddings. This action cannot be undone.

## Error Responses

### 400 Bad Request - Invalid File

```json
{
  "detail": "Invalid file type. Only PDF files are supported."
}
```

### 413 Request Entity Too Large

```json
{
  "detail": "File size exceeds maximum allowed size of 10MB"
}
```

### 422 Processing Failed

```json
{
  "detail": "Document processing failed: Unable to extract text from PDF"
}
```

### 404 Not Found

```json
{
  "detail": "Document not found"
}
```

## File Requirements

### Supported Formats

- **PDF**: Primary format, all versions supported
- **Text extraction**: Must contain selectable text (not scanned images)
- **Size limit**: Configurable, default 10MB
- **Page limit**: No hard limit, but processing time increases

### File Validation

The system validates:

1. **File type**: Must be PDF (MIME type check)
2. **File size**: Must be under configured limit
3. **Content**: Must contain extractable text
4. **Structure**: Must be valid PDF format

## Processing Pipeline

1. **Upload Validation**: File type, size, format checks
2. **Text Extraction**: PDF content extraction using PyPDF
3. **Classification**: Automatic document type detection
4. **Chunking**: Category-specific text segmentation
5. **Embedding**: Vector representation generation
6. **Storage**: Database and vector store persistence

### Processing Times

| Document Type | Size | Typical Processing Time |
|---------------|------|------------------------|
| Financial (1-5 pages) | 1MB | 30-60 seconds |
| Generic (5-20 pages) | 3MB | 1-2 minutes |
| Long-form (50+ pages) | 10MB | 3-5 minutes |

## Integration Examples

### JavaScript Upload

```javascript
const uploadDocument = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch('/api/v1/documents/upload', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    },
    body: formData
  });
  
  return response.json();
};
```

### Python Upload

```python
import requests

def upload_document(file_path, token):
    with open(file_path, 'rb') as file:
        files = {'file': file}
        headers = {'Authorization': f'Bearer {token}'}
        
        response = requests.post(
            'http://localhost:8000/api/v1/documents/upload',
            files=files,
            headers=headers
        )
        
        return response.json()
```

## Best Practices

1. **Check file size** before upload
2. **Monitor processing status** for large files
3. **Use appropriate error handling** for failed uploads
4. **Validate PDF text content** before upload
5. **Consider batch uploads** for multiple files
6. **Clean up old documents** periodically