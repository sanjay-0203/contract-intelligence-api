# Contract Intelligence API - Design Document

## Overview

The Contract Intelligence API is an AI-powered system for analyzing legal contracts, extracting structured information, answering questions, and detecting risky clauses.

## Architecture

### High-Level Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       │ HTTP/REST
       │
┌──────▼──────────────────────────────────────────┐
│            FastAPI Application                   │
│  ┌──────────────────────────────────────────┐  │
│  │          API Endpoints                    │  │
│  │  /ingest  /extract  /ask  /audit          │  │
│  └──────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────┐  │
│  │           Service Layer                   │  │
│  │  ┌────────────┐  ┌─────────────┐         │  │
│  │  │ PDF        │  │ LLM         │         │  │
│  │  │ Processor  │  │ Service     │         │  │
│  │  └────────────┘  └─────────────┘         │  │
│  │  ┌────────────┐  ┌─────────────┐         │  │
│  │  │ Vector     │  │ Audit       │         │  │
│  │  │ Search     │  │ Service     │         │  │
│  │  └────────────┘  └─────────────┘         │  │
│  └──────────────────────────────────────────┘  │
└──────┬──────────────────────┬──────────────────┘
       │                      │
       │                      │
┌──────▼────────┐     ┌───────▼────────┐
│  PostgreSQL   │     │   OpenAI API   │
│  + pgvector   │     │                │
└───────────────┘     └────────────────┘
```

### Component Responsibilities

#### 1. PDF Processor
- Extract text from PDF files
- Chunk text into overlapping segments for vector search
- Compute document hashes for deduplication
- Handle multiple PDF libraries with fallback

**Key Design Decisions:**
- **Chunk Size**: 1000 characters with 200 character overlap
  - Rationale: Balances context preservation with embedding model limits
  - Trade-off: Larger chunks = better context, but less precise retrieval
- **Overlap**: Prevents sentence splitting across chunk boundaries
- **Fallback**: pdfplumber → PyPDF2 for robust extraction

#### 2. LLM Service
- OpenAI integration for GPT-4 based extraction and Q&A
- Embedding generation using text-embedding-3-small
- Token management and prompt engineering
- Fallback to rule-based extraction when LLM unavailable

**Key Design Decisions:**
- **Model Selection**: 
  - GPT-4-turbo for extraction/Q&A (accuracy over speed)
  - text-embedding-3-small for embeddings (cost-effective, 1536 dimensions)
- **Temperature**: 
  - 0.1 for extraction (deterministic)
  - 0.2 for Q&A (slight creativity)
- **Response Format**: JSON mode for structured extraction
- **Fallback Strategy**: Rule-based regex extraction when API fails

#### 3. Vector Search Service
- Semantic similarity search using pgvector
- Cosine distance for ranking chunks
- Optional document filtering

**Key Design Decisions:**
- **Index Type**: IVFFlat for balanced performance
- **Distance Metric**: Cosine distance (normalized similarity)
- **Top-K**: Default 5 chunks for Q&A context
- **Filter Support**: Allow querying specific documents

#### 4. Audit Service
- Rule-based risk detection for known patterns
- Severity classification (low, medium, high, critical)
- Evidence extraction with character positions

**Key Design Decisions:**
- **Rule-First Approach**: Deterministic rules for known risks
- **Pattern Coverage**:
  - Auto-renewal with short notice (<30 days)
  - Unlimited liability clauses
  - Broad indemnification
  - Unilateral termination
  - Assignment restrictions
  - Perpetual confidentiality
- **Severity Logic**:
  - Critical: Unlimited liability exposure
  - High: Auto-renewal <15 days, no liability cap
  - Medium: Auto-renewal 15-29 days, broad indemnity
  - Low: Minor restrictions with carveouts

## Data Model

### Documents Table
- **Purpose**: Store uploaded PDF metadata
- **Key Fields**: document_id (UUID), filename, page_count, content_hash
- **Relationships**: One-to-many with chunks, extractions, audit findings

### Document Chunks Table
- **Purpose**: Store text segments with embeddings for vector search
- **Key Fields**: chunk_index, text, char_start, char_end, embedding (1536-dim vector)
- **Index**: IVFFlat index on embedding column
- **Design Choice**: Store embeddings with chunks (not separate table) for query efficiency

### Extractions Table
- **Purpose**: Cache structured field extraction results
- **Key Fields**: All contract fields as separate columns
- **Design Choice**: Denormalized for query performance
- **Metadata**: extraction_method (llm/rule_based), confidence_score

### Audit Findings Table
- **Purpose**: Store risk detection results
- **Key Fields**: risk_type, severity, evidence_text, char_start/end
- **Design Choice**: Separate findings (not embedded in extractions) for flexible querying

### Query Logs Table
- **Purpose**: Track Q&A queries for analytics and debugging
- **Key Fields**: question, answer, citations, response_time_ms
- **Design Choice**: Separate from main data for historical analysis

## Chunking Strategy

### Rationale
Text is chunked for two reasons:
1. **Embedding Model Limits**: Models have token limits (8191 for text-embedding-3-small)
2. **Retrieval Precision**: Smaller chunks = more precise citation locations

### Implementation
- **Chunk Size**: 1000 characters
- **Overlap**: 200 characters
- **Boundary Detection**: Sentence-aware splitting (look for ". ", ".\n", etc.)
- **Metadata**: Each chunk stores page_number, char_start, char_end

### Trade-offs
- **Smaller chunks**: Better precision, but may lose context
- **Larger chunks**: Better context, but less precise citations
- **Overlap**: Prevents context loss at boundaries, but increases storage/compute

## LLM Prompt Engineering

### Extraction Prompt
See `prompts/extraction_prompt.md` for details.

**Key Elements:**
- System message establishes legal expert role
- Few-shot examples would improve accuracy (future enhancement)
- JSON schema specified explicitly
- Handles missing fields gracefully (null values)

### Q&A Prompt
See `prompts/qa_prompt.md` for details.

**Key Elements:**
- Context-first approach (relevant chunks before question)
- Explicit instruction to cite sources
- Fallback response when answer not in context
- Temperature tuned for accuracy over creativity

## Fallback Behavior

### When LLM Unavailable
1. **Extraction**: Falls back to rule-based regex extraction
   - Effective date: Multiple date format patterns
   - Governing law: "governed by laws of X" pattern
   - Term: "term of X" pattern
   - Limited coverage but deterministic

2. **Q&A**: Returns error message
   - Could add keyword-based search as fallback (future)

3. **Embeddings**: Returns zero vector
   - Disables vector search for that chunk
   - Document still searchable via text

### When Database Unavailable
- Health check reports degraded status
- API returns 503 Service Unavailable
- Prevents data corruption from partial operations

## Security Considerations

### PII Handling
- **Logging**: Redact document content from logs
- **Storage**: Encrypted database recommended for production
- **Access**: No authentication in v1 (add JWT/API keys for production)

### API Keys
- **Storage**: Environment variables only
- **Edge Functions**: Access via Deno.env.get() (future Supabase integration)
- **Rotation**: Support key rotation without downtime

### Input Validation
- **File Type**: PDF only (validated by extension and content)
- **File Size**: Configurable limit (default 50MB)
- **Request Rate**: No rate limiting in v1 (add for production)

### Injection Prevention
- **SQL Injection**: SQLAlchemy ORM protects against SQL injection
- **Prompt Injection**: LLM prompts use user input as data, not instructions

## Monitoring and Observability

### Health Checks
- `/healthz`: Database + OpenAI API status
- Returns "healthy", "degraded", or "unhealthy"

### Metrics
- `/metrics`: Document counts, query counts, uptime
- Prometheus-compatible format (future: export to Prometheus)

### Logging
- Structured JSON logs
- Request ID tracking
- Error stack traces
- Performance metrics (response times)

## Performance Considerations

### Database Optimization
- **Connection Pooling**: 10 connections, 20 max overflow
- **Indexes**: On document_id, embedding vector
- **Batch Operations**: Bulk insert chunks for ingestion

### Caching Strategy
- **Embeddings**: Cached in database with chunks
- **Extractions**: Cached in extractions table
- **Future**: Redis cache for frequently queried answers

### Scaling
- **Horizontal**: Stateless API allows multiple instances
- **Database**: Read replicas for query scaling
- **Async Processing**: Background tasks for long-running operations (future)

## Testing Strategy

### Unit Tests
- PDF processor text extraction and chunking
- Audit service rule detection
- LLM service fallback behavior

### Integration Tests
- End-to-end API workflows
- Database transactions
- Error handling

### Evaluation Framework
- Q&A accuracy against curated dataset
- Extraction field completeness
- Audit detection precision/recall

## Future Enhancements

### Short-term
- [ ] Authentication and authorization (JWT/API keys)
- [ ] Rate limiting
- [ ] Caching layer (Redis)
- [ ] Async processing for large documents
- [ ] Webhook delivery for long-running tasks

### Medium-term
- [ ] Multi-language support
- [ ] Custom extraction templates
- [ ] Clause comparison across contracts
- [ ] Bulk operations API
- [ ] Export to various formats (JSON, CSV, PDF reports)

### Long-term
- [ ] Fine-tuned models for legal domain
- [ ] Active learning from user feedback
- [ ] Contract generation from templates
- [ ] Automated negotiation suggestions

## Limitations and Trade-offs

### Current Limitations
1. **No OCR**: Scanned PDFs not supported (only digital text)
2. **English Only**: No multi-language support
3. **No Authentication**: Open API (add for production)
4. **No Batch Processing**: One document at a time for extraction/audit
5. **No Versioning**: Contract updates create new documents

### Design Trade-offs
1. **LLM vs Rule-based**:
   - Chose: LLM-first with rule-based fallback
   - Rationale: Better accuracy, graceful degradation
   - Trade-off: Higher cost, slower response

2. **Vector DB vs Separate Service**:
   - Chose: pgvector in PostgreSQL
   - Rationale: Simplifies deployment, transaction support
   - Trade-off: Less specialized than Pinecone/Weaviate

3. **Sync vs Async Processing**:
   - Chose: Synchronous API
   - Rationale: Simpler implementation, lower latency for small docs
   - Trade-off: Timeout risk for large documents

4. **Caching Strategy**:
   - Chose: Database-backed caching only
   - Rationale: Avoids cache invalidation complexity
   - Trade-off: Slower repeated queries

## Deployment Architecture

### Docker Compose (Development)
- PostgreSQL with pgvector
- FastAPI application
- Shared volume for logs

### Production (Recommended)
- Kubernetes deployment with:
  - Multiple API pods
  - Managed PostgreSQL (AWS RDS, Google Cloud SQL)
  - Load balancer
  - Secret management (Vault, AWS Secrets Manager)
  - Monitoring (Prometheus + Grafana)

## Cost Estimation

### OpenAI API Costs (Approximate)
- **Embeddings**: $0.00002/1K tokens × ~500 tokens/chunk = $0.00001/chunk
- **Extraction**: $0.01/1K tokens × ~3K tokens = $0.03/extraction
- **Q&A**: $0.01/1K tokens × ~2K tokens = $0.02/question

### Example Monthly Cost
- 1000 documents/month × 50 chunks = 50K chunks = $0.50
- 1000 extractions/month = $30
- 5000 questions/month = $100
- **Total**: ~$130.50/month (excluding infrastructure)

## Conclusion

This design balances accuracy, performance, and cost-effectiveness while maintaining production-ready quality. The architecture supports horizontal scaling and graceful degradation when external services are unavailable.
