# Contract Intelligence API

AI-powered contract analysis system with extraction, question answering, and risk detection capabilities.

## Features

- **Document Ingestion**: Upload multiple PDF contracts with text extraction and chunking
- **Structured Extraction**: Extract key contract fields (parties, dates, terms, liability caps, etc.)
- **Question Answering**: RAG-based Q&A with citations to specific document locations
- **Risk Auditing**: Detect problematic clauses (auto-renewal, unlimited liability, broad indemnity)
- **Streaming Support**: Real-time token streaming for long-running queries
- **Production Ready**: Docker deployment, health checks, metrics, comprehensive testing

## Quick Start

### Prerequisites

- Docker and Docker Compose
- OpenAI API key

### Setup

1. Clone the repository and navigate to the project directory:
```bash
cd contract-intelligence-api
```

2. Create `.env` file with your configuration:
```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

3. Start the services:
```bash
docker-compose up -d
```

4. Verify the API is running:
```bash
curl http://localhost:8000/healthz
```

The API will be available at `http://localhost:8000`

## API Documentation

### Endpoints

#### POST /ingest
Upload 1 or more PDF contracts for processing.

**Request:**
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

#### POST /extract
Extract structured fields from a contract.

**Request:**
```bash
curl -X POST http://localhost:8000/extract \
  -H "Content-Type: application/json" \
  -d '{"document_id": "550e8400-e29b-41d4-a716-446655440000"}'
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
  "auto_renewal": "Automatically renews unless notice given 30 days prior",
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

#### POST /ask
Ask questions about uploaded contracts with RAG-based answers.

**Request:**
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the liability cap in this contract?",
    "document_ids": ["550e8400-e29b-41d4-a716-446655440000"],
    "max_citations": 5
  }'
```

**Response:**
```json
{
  "query_id": "query-123",
  "question": "What is the liability cap in this contract?",
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

#### POST /audit
Audit contract for risky clauses.

**Request:**
```bash
curl -X POST http://localhost:8000/audit \
  -H "Content-Type: application/json" \
  -d '{"document_id": "550e8400-e29b-41d4-a716-446655440000"}'
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

#### GET /ask/stream
Stream answer tokens in real-time using Server-Sent Events.

**Request:**
```bash
curl -N http://localhost:8000/ask/stream?question=What%20is%20the%20term%20length&document_ids=550e8400...
```

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
Usage metrics and statistics.

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

## Development

### Local Development Without Docker

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up PostgreSQL with pgvector:
```bash
# Install PostgreSQL and pgvector extension
# Create database: contract_intelligence
```

3. Configure environment variables:
```bash
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/contract_intelligence"
export OPENAI_API_KEY="your-api-key"
```

4. Run the application:
```bash
python -m uvicorn src.main:app --reload
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src tests/

# Run specific test file
pytest tests/unit/test_pdf_processor.py

# Run integration tests (requires OpenAI API key)
OPENAI_API_KEY=your-key pytest tests/integration/
```

### Evaluation

Run the Q&A evaluation framework:

```bash
cd eval
python evaluate_qa.py
```

This will test the system against a curated dataset of questions and expected answers.

## Architecture

### Components

1. **PDF Processor**: Extracts text from PDFs, handles chunking with overlap
2. **LLM Service**: OpenAI integration for extraction and Q&A
3. **Vector Search**: pgvector-based semantic search for RAG
4. **Audit Service**: Rule-based risk detection with fallback to LLM
5. **API Layer**: FastAPI endpoints with request validation

### Data Flow

1. PDF Upload → Text Extraction → Chunking → Embedding Generation → Database Storage
2. Extraction Request → LLM Analysis → Structured JSON → Database Storage
3. Question → Embedding → Vector Search → Context Retrieval → LLM Answer → Citations
4. Audit Request → Rule-based Analysis → Finding Detection → Severity Assignment

### Database Schema

- **documents**: Uploaded PDF metadata
- **document_chunks**: Text chunks with embeddings for vector search
- **extractions**: Structured field extraction results
- **audit_findings**: Risk detection findings
- **query_logs**: Q&A query history

## Configuration

### Environment Variables

- `DATABASE_URL`: PostgreSQL connection string
- `OPENAI_API_KEY`: OpenAI API key (required)
- `API_HOST`: API host (default: 0.0.0.0)
- `API_PORT`: API port (default: 8000)
- `DEBUG`: Debug mode (default: false)
- `MAX_FILE_SIZE_MB`: Maximum file size in MB (default: 50)
- `MAX_FILES_PER_REQUEST`: Maximum files per upload (default: 10)

## Deployment

### Production Deployment

1. Build the Docker image:
```bash
docker build -t contract-intelligence-api .
```

2. Deploy with environment variables:
```bash
docker run -d \
  -p 8000:8000 \
  -e DATABASE_URL="your-db-url" \
  -e OPENAI_API_KEY="your-key" \
  contract-intelligence-api
```

### Scaling Considerations

- Use connection pooling for database (configured in SQLAlchemy)
- Deploy multiple API instances behind a load balancer
- Consider caching embeddings for frequently queried documents
- Monitor OpenAI API rate limits and costs

## Security

- API keys stored in environment variables, never in code
- PII redacted from logs automatically
- Database credentials secured via environment variables
- CORS configured for production deployments
- Input validation on all endpoints

## Monitoring

- Health checks at `/healthz`
- Metrics endpoint at `/metrics`
- Structured logging with request IDs
- Database query performance tracking

## License

MIT License

## Support

For issues or questions, please open an issue on GitHub.
