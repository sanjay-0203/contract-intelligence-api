# Changelog

All notable changes to the Contract Intelligence API project.

## [1.0.0] - 2025-10-28

### Added - Initial Release

#### Core Features
- PDF document ingestion with multi-file upload support
- Structured field extraction using GPT-4 (12 contract fields)
- RAG-based question answering with citations
- Rule-based risk auditing (6 risk categories)
- Server-Sent Events streaming for Q&A
- Health checks and usage metrics
- Webhook endpoint for event notifications

#### Infrastructure
- FastAPI application with auto-generated OpenAPI docs
- PostgreSQL database with pgvector extension
- Docker containerization with docker-compose
- Database schema with 5 tables
- Connection pooling and transaction management

#### Services
- **PDF Processor**: Text extraction, chunking, hashing
  - pdfplumber with PyPDF2 fallback
  - 1000-char chunks with 200-char overlap
  - Sentence-aware boundary detection
  
- **LLM Service**: OpenAI integration
  - GPT-4-turbo for extraction and Q&A
  - text-embedding-3-small for embeddings
  - Token management and truncation
  - Rule-based fallback extraction
  
- **Vector Search**: Semantic document retrieval
  - pgvector with IVFFlat indexing
  - Cosine similarity ranking
  - Top-K retrieval with filtering
  
- **Audit Service**: Risk detection
  - Auto-renewal with short notice detection
  - Unlimited liability clause detection
  - Broad indemnification detection
  - Unilateral termination detection
  - Assignment restriction detection
  - Perpetual confidentiality detection

#### Testing
- Unit tests for core services
- Integration tests for API endpoints
- Test configuration with pytest
- Q&A evaluation framework with 10 test questions
- Automated scoring and metrics

#### Documentation
- README with quick start guide
- Design document (architecture, rationale, trade-offs)
- API documentation with examples
- Prompt engineering documentation
  - Extraction prompt with rationale
  - Q&A prompt with examples
  - Audit rules documentation
- Quick reference guide
- Project summary

#### Example Content
- Service agreement template
- NDA template
- PDF generation script
- Q&A evaluation dataset

#### Developer Tools
- Setup script (setup.sh)
- API test script (test_api.sh)
- Docker configuration
- Environment variable templates
- .gitignore for Python projects

### Technical Details

#### API Endpoints
- `POST /ingest` - Upload 1-10 PDFs (max 50MB each)
- `POST /extract` - Extract structured fields
- `POST /ask` - Question answering with RAG
- `POST /audit` - Detect risky clauses
- `GET /ask/stream` - SSE streaming responses
- `GET /healthz` - Health status
- `GET /metrics` - Usage statistics
- `POST /webhook/events` - Event notifications

#### Database Schema
- `documents` - PDF metadata (UUID, filename, pages, hash)
- `document_chunks` - Text chunks with 1536-dim embeddings
- `extractions` - Structured contract fields
- `audit_findings` - Risk detection results
- `query_logs` - Q&A query history

#### Dependencies
- FastAPI 0.104.1
- SQLAlchemy 2.0.23
- OpenAI 1.3.7
- pgvector 0.2.4
- pdfplumber 0.10.3
- PyPDF2 3.0.1

#### Configuration
- Environment-based configuration
- Configurable file size limits
- Configurable chunking parameters
- Configurable vector search top-K

### Design Decisions

- **LLM-First Strategy**: Use GPT-4 for accuracy, fall back to rules
- **Embedded Vector DB**: pgvector in PostgreSQL vs separate service
- **Synchronous API**: Simpler than async, sufficient for current needs
- **Rule-Based Audit**: Deterministic and explainable
- **Chunking Strategy**: Balance context preservation vs precision
- **Denormalized Schema**: Query performance over normalization

### Known Limitations

- No OCR support (digital PDFs only)
- English language only
- No authentication (add for production)
- No rate limiting
- Synchronous processing only (large docs may timeout)
- No contract versioning

### Future Enhancements

#### Planned for v1.1
- Authentication (JWT/API keys)
- Rate limiting
- Async processing for large documents
- Caching layer (Redis)

#### Planned for v2.0
- OCR support for scanned PDFs
- Multi-language support
- Custom extraction templates
- Contract comparison features
- Fine-tuned models

#### Long-term Roadmap
- Active learning from user feedback
- Contract generation
- Automated negotiation suggestions
- Clause library and templates

### Performance Characteristics

- Ingestion: ~2-5 seconds per document (10 pages)
- Extraction: ~3-5 seconds per document
- Q&A: ~1-3 seconds per question
- Audit: ~0.5-1 second per document (rule-based)
- Embedding generation: ~0.2-0.5 seconds per chunk

### Cost Estimates

For typical usage (1000 docs, 1000 extractions, 5000 questions/month):
- OpenAI API: ~$130/month
- Infrastructure: ~$100-200/month
- Total: ~$230-330/month

### Contributors

- Initial implementation: MiniMax Agent
- Framework: FastAPI, OpenAI, PostgreSQL
- Containerization: Docker

### License

MIT License - See LICENSE file for details

---

## Version Format

This project follows Semantic Versioning (semver):
- MAJOR: Breaking API changes
- MINOR: New features, backward compatible
- PATCH: Bug fixes, backward compatible

## Release Process

1. Update CHANGELOG.md
2. Update version in src/__init__.py
3. Tag release: git tag -a v1.0.0 -m "Release v1.0.0"
4. Build and test Docker image
5. Deploy to production environment
