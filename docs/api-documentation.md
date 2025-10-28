# OpenAPI Documentation

## Overview

The Contract Intelligence API provides AI-powered contract analysis capabilities through a RESTful API.

Base URL: `http://localhost:8000`

## Authentication

Currently, no authentication is required. For production deployments, implement:
- API Key authentication via headers
- JWT tokens for user-specific access
- OAuth 2.0 for third-party integrations

## Endpoints

### Document Ingestion

#### POST /ingest

Upload one or more PDF contracts for processing.

**Request:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Body: Form data with `files` field containing PDF file(s)

**Request Example:**
```bash
curl -X POST http://localhost:8000/ingest \
  -F "files=@contract1.pdf" \
  -F "files=@contract2.pdf"
```

**Response:**
```json
{
  "document_ids": ["550e8400-e29b-41d4-a716-446655440000"],
  "uploaded_count": 1,
  "message": "Successfully ingested 1 document(s)"
}
```

**Status Codes:**
- `200`: Success
- `400`: Invalid file type or size
- `503`: Service unavailable

### Field Extraction

#### POST /extract

Extract structured fields from a contract.

**Request:**
- Method: `POST`
- Content-Type: `application/json`
- Body:
```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response:**
```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "extraction_id": "abc-123",
  "parties": ["Acme Corp", "Tech Solutions Inc"],
  "effective_date": "January 1, 2024",
  "term": "12 months",
  "governing_law": "State of California",
  "payment_terms": "Net 30 days",
  "termination": "Either party may terminate with 60 days notice",
  "auto_renewal": "Automatically renews unless 30 days notice given",
  "confidentiality": "5 years from disclosure",
  "indemnity": "Standard indemnification provisions",
  "liability_cap": {
    "amount": 100000,
    "currency": "USD"
  },
  "signatories": [
    {"name": "John Doe", "title": "CEO"}
  ],
  "confidence_score": 0.85,
  "extraction_method": "llm"
}
```

**Status Codes:**
- `200`: Success
- `404`: Document not found
- `500`: Extraction failed

### Question Answering

#### POST /ask

Ask a question about uploaded contracts.

**Request:**
```json
{
  "question": "What is the liability cap?",
  "document_ids": ["550e8400-e29b-41d4-a716-446655440000"],
  "max_citations": 5
}
```

**Response:**
```json
{
  "query_id": "query-123",
  "question": "What is the liability cap?",
  "answer": "The liability cap is $100,000 USD...",
  "citations": [
    {
      "document_id": "550e8400-e29b-41d4-a716-446655440000",
      "page": 3,
      "char_start": 1250,
      "char_end": 1450,
      "text": "...liability shall be limited to $100,000..."
    }
  ],
  "response_time_ms": 1234
}
```

**Status Codes:**
- `200`: Success
- `404`: No relevant documents found

### Risk Auditing

#### POST /audit

Audit a contract for risky clauses.

**Request:**
```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response:**
```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "findings": [
    {
      "finding_id": "finding-123",
      "risk_type": "auto_renewal_short_notice",
      "severity": "high",
      "title": "Auto-renewal with 15-day notice period",
      "description": "Contract automatically renews with only 15 days' notice...",
      "evidence": "...automatically renew for successive one-year terms...",
      "page": 2,
      "char_start": 850,
      "char_end": 1050,
      "confidence_score": 0.9
    }
  ],
  "total_findings": 3,
  "high_severity_count": 1,
  "medium_severity_count": 2,
  "low_severity_count": 0
}
```

**Status Codes:**
- `200`: Success
- `404`: Document not found

### Streaming Q&A

#### GET /ask/stream

Stream answer tokens in real-time.

**Request:**
```bash
curl -N "http://localhost:8000/ask/stream?question=What%20is%20the%20term%20length&document_ids=550e8400..."
```

**Response:**
Server-Sent Events stream:
```
data: The
data:  term
data:  length
data:  is
data:  12
data:  months
data: [DONE]
```

### Administrative Endpoints

#### GET /healthz

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-28T17:00:00",
  "database": "healthy",
  "openai": "healthy",
  "version": "1.0.0"
}
```

#### GET /metrics

Usage metrics.

**Response:**
```json
{
  "documents_ingested": 42,
  "extractions_performed": 35,
  "queries_answered": 128,
  "audits_performed": 30,
  "uptime_seconds": 86400
}
```

#### POST /webhook/events

Receive webhook events (placeholder for external integrations).

**Request:**
```json
{
  "event_type": "extraction_complete",
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "success",
  "timestamp": "2025-10-28T17:00:00",
  "data": {}
}
```

**Response:**
```json
{
  "status": "received",
  "event_type": "extraction_complete"
}
```

## Data Models

### Document
- `document_id`: UUID (string)
- `filename`: string
- `page_count`: integer
- `uploaded_at`: datetime

### Extraction
- All contract fields (see /extract response)
- `confidence_score`: float (0.0-1.0)
- `extraction_method`: "llm" | "rule_based"

### Citation
- `document_id`: UUID (string)
- `page`: integer (nullable)
- `char_start`: integer (nullable)
- `char_end`: integer (nullable)
- `text`: string (excerpt)

### AuditFinding
- `risk_type`: string
- `severity`: "low" | "medium" | "high" | "critical"
- `title`: string
- `description`: string
- `evidence`: string (nullable)
- `confidence_score`: float (nullable)

## Rate Limits

Current implementation has no rate limits. For production:
- Implement per-IP or per-API-key limits
- Typical: 100 requests/minute for reads, 10/minute for ingestion

## Error Handling

All errors return JSON with:
```json
{
  "detail": "Error message"
}
```

Common status codes:
- `400`: Bad request (invalid input)
- `404`: Resource not found
- `500`: Internal server error
- `503`: Service unavailable (e.g., OpenAI API down)

## SDKs and Client Libraries

Currently, no official SDKs. API is standard REST and works with:
- `curl` (command line)
- `requests` (Python)
- `axios` (JavaScript)
- Any HTTP client

Example Python client:
```python
import requests

# Upload contract
with open('contract.pdf', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/ingest',
        files={'files': f}
    )
    doc_id = response.json()['document_ids'][0]

# Extract fields
response = requests.post(
    'http://localhost:8000/extract',
    json={'document_id': doc_id}
)
extraction = response.json()
print(extraction['parties'])
```

## Interactive Documentation

FastAPI provides interactive documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

These provide a web interface to explore and test the API.
