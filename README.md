D:\contract-intelligence-api\README.md
# Contract Intelligence API

Contract Intelligence API is an AI-powered contract analysis system that performs document ingestion, structured extraction, question answering, and risk auditing. It is built with FastAPI and uses OpenAI embeddings for semantic search and RAG-based Q&A. For local development the project uses SQLite; for production we recommend PostgreSQL with pgvector.

---

## Features

- Document ingestion: Upload one or more PDF contracts; extract text and chunk for retrieval.
- Structured extraction: Extract parties, dates, terms, liability caps, governing law, payment terms, termination, signatories and more.
- Question answering: RAG-based answers with citations to document locations.
- Risk auditing: Detect risky clauses such as auto-renewal, unlimited liability, broad indemnity, short notice periods.
- Streaming support: Server-Sent Events (SSE) token streaming for long-running queries.
- Production-ready features: Docker deployment, health checks, metrics endpoint, structured logging, and tests.

---

## Quick Start

### Prerequisites
- Docker & Docker Compose (optional but recommended for production)
- Python 3.10+
- OpenAI API key

### Clone
```bash
git clone https://github.com/sanjay-0203/contract-intelligence-api.git
cd contract-intelligence-api
Local env
Create .env from .env.example and add your keys:

bash
Copy code
cp .env.example .env
# Edit .env, set OPENAI_API_KEY and DATABASE_URL
Example local .env:

ini
Copy code
OPENAI_API_KEY=REPLACE_WITH_OPENAI_KEY
DATABASE_URL=sqlite:///./data/dev.db
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true
Run with Docker Compose (recommended for demo/production)
bash
Copy code
docker-compose up -d --build
Verify:

bash
Copy code
curl http://localhost:8000/healthz
Run locally (without Docker)
bash
Copy code
python -m venv .venv
# Windows
.\\.venv\\Scripts\\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
mkdir -p data

# start server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
Interactive docs: http://127.0.0.1:8000/docs

API Documentation (examples)
POST /ingest
Ingest one or more PDFs (multipart/form-data). Extracts text, chunks, creates embeddings and stores metadata.

Request (curl):

bash
Copy code
curl -X POST http://localhost:8000/ingest \
  -F "files=@contract1.pdf" \
  -F "files=@contract2.pdf"
Response:

json
Copy code
{
  "document_ids": ["550e8400-e29b-41d4-a716-446655440000"],
  "uploaded_count": 1,
  "message": "Successfully ingested 1 document(s)"
}
POST /extract
Extract structured fields for a given document.

Request:

bash
Copy code
curl -X POST http://localhost:8000/extract \
  -H "Content-Type: application/json" \
  -d '{"document_id":"550e8400-e29b-41d4-a716-446655440000"}'
Response:

json
Copy code
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "extraction_id": "abc-123",
  "parties": ["Acme Corp", "Tech Solutions Inc"],
  "effective_date": "January 1, 2024",
  "term": "12 months",
  "governing_law": "State of California",
  "payment_terms": "Net 30 days",
  "termination": "Either party may terminate with 60 days notice",
  "auto_renewal": "Automatically renews unless notice given 30 days prior",
  "confidentiality": "5 years from disclosure",
  "indemnity": "Standard indemnification provisions",
  "liability_cap": { "amount": 100000, "currency": "USD" },
  "signatories": [{ "name": "John Doe", "title": "CEO" }],
  "confidence_score": 0.85,
  "extraction_method": "llm"
}
POST /ask
RAG-based QA over selected documents.

Request:

bash
Copy code
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question":"What is the liability cap in this contract?",
    "document_ids":["550e8400-e29b-41d4-a716-446655440000"],
    "max_citations":5
  }'
Response:

json
Copy code
{
  "query_id":"query-123",
  "question":"What is the liability cap in this contract?",
  "answer":"The liability cap is $100,000 USD...",
  "citations":[
    {
      "document_id":"550e8400-e29b-41d4-a716-446655440000",
      "page":3,
      "char_start":1250,
      "char_end":1450,
      "text":"...liability shall be limited to $100,000..."
    }
  ],
  "response_time_ms":1234
}
POST /audit
Run risk checks and produce findings.

Request:

bash
Copy code
curl -X POST http://localhost:8000/audit \
  -H "Content-Type: application/json" \
  -d '{"document_id":"550e8400-e29b-41d4-a716-446655440000"}'
Response:

json
Copy code
{
  "document_id":"550e8400-e29b-41d4-a716-446655440000",
  "findings":[
    {
      "finding_id":"finding-123",
      "risk_type":"auto_renewal_short_notice",
      "severity":"high",
      "title":"Auto-renewal with 15-day notice period",
      "description":"Contract automatically renews with only 15 days' notice...",
      "evidence":"...automatically renew for successive one-year terms...",
      "page":2,
      "char_start":850,
      "char_end":1050,
      "confidence_score":0.9
    }
  ],
  "total_findings":3,
  "high_severity_count":1,
  "medium_severity_count":2,
  "low_severity_count":0
}
GET /ask/stream
Server-Sent Events endpoint for streaming tokens:

perl
Copy code
curl -N "http://localhost:8000/ask/stream?question=What%20is%20the%20term%20length&document_ids=550e8400..."
GET /healthz
Health check:

json
Copy code
{
  "status":"healthy",
  "timestamp":"2025-10-28T17:00:00",
  "database":"healthy",
  "openai":"healthy",
  "version":"1.0.0"
}
GET /metrics
Usage metrics:

json
Copy code
{
  "documents_ingested":42,
  "extractions_performed":35,
  "queries_answered":128,
  "audits_performed":30,
  "uptime_seconds":86400
}
Development
Local (no Docker)
bash
Copy code
pip install -r requirements.txt
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/contract_intelligence"  # optional
export OPENAI_API_KEY="your-api-key"
python -m uvicorn src.main:app --reload
Tests
Run unit and integration tests:

bash
Copy code
pytest
pytest --cov=src
# integration tests example (requires OPENAI_API_KEY)
OPENAI_API_KEY=your-key pytest tests/integration/
Evaluation
A QA evaluation harness can be run to test the system against curated Q&A pairs.

bash
Copy code
cd eval
python evaluate_qa.py
Architecture & Components
PDF Processor: Extracts text from PDFs and generates overlapping chunks.

Embedding Service: Generates embeddings (OpenAI) for chunks.

Vector Search: pgvector-based semantic search (Postgres) or lightweight local alternative (SQLite).

Audit Service: Rule-based + LLM-assisted detection of risky clauses.

API Layer: FastAPI endpoints with validation and streaming support.

Database schema (high level)
documents: uploaded documents metadata

document_chunks: text chunks + embeddings + chunk metadata

extractions: structured extraction results

audit_findings: risk detection outputs

query_logs: Q&A history and metadata

Configuration (environment variables)
DATABASE_URL — Postgres or SQLite connection string

OPENAI_API_KEY — OpenAI API key (required)

API_HOST — default 0.0.0.0

API_PORT — default 8000

DEBUG — true/false

MAX_FILE_SIZE_MB — default 50

MAX_FILES_PER_REQUEST — default 10

Deployment
Docker (build & run)
bash
Copy code
docker build -t contract-intelligence-api .
docker run -d -p 8000:8000 \
  -e DATABASE_URL="your-db-url" \
  -e OPENAI_API_KEY="your-key" \
  contract-intelligence-api
Production considerations
Use a process manager (systemd/docker swarm/k8s) with multiple replicas behind a load balancer.

Use a production Postgres instance with pgvector enabled and connection pooling.

Cache frequent queries and consider precomputing embeddings for large static corpora.

Monitor OpenAI rate limits and costs.

Security & Privacy
Never store API keys in source code or commits. Use environment variables or secret management.

Rotate keys immediately if leaked.

Redact or avoid logging PII; use structured logs with request IDs.

Use HTTPS/TLS in production and secure DB credentials with secrets manager.

Scaling & Observability
Add metrics (Prometheus) and health checks (/healthz).

Centralized logs and tracing (e.g., OpenTelemetry).

Horizontal scale API instances; shard or partition large vector stores if needed.

License
MIT License — see LICENSE file.