# Contract Intelligence API - Quick Reference

## Installation & Setup

```bash
# 1. Clone and navigate
cd contract-intelligence-api

# 2. Configure
cp .env.example .env
# Edit .env: Add OPENAI_API_KEY

# 3. Start services
./setup.sh
# OR manually: docker-compose up -d

# 4. Verify
curl http://localhost:8000/healthz
```

## Common Commands

### Docker Management
```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f
docker-compose logs api
docker-compose logs postgres

# Restart services
docker-compose restart

# Stop services
docker-compose down

# Rebuild after code changes
docker-compose up -d --build
```

### API Testing
```bash
# Health check
curl http://localhost:8000/healthz

# Metrics
curl http://localhost:8000/metrics

# Upload document
curl -X POST http://localhost:8000/ingest \
  -F "files=@example_contracts/service_agreement.pdf"

# Extract fields (replace DOC_ID)
curl -X POST http://localhost:8000/extract \
  -H "Content-Type: application/json" \
  -d '{"document_id":"DOC_ID"}'

# Ask question
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"What is the term length?","document_ids":["DOC_ID"]}'

# Audit contract
curl -X POST http://localhost:8000/audit \
  -H "Content-Type: application/json" \
  -d '{"document_id":"DOC_ID"}'

# Stream Q&A
curl -N "http://localhost:8000/ask/stream?question=What%20is%20the%20liability%20cap"
```

### Development

```bash
# Run tests
pytest

# Run specific test
pytest tests/unit/test_pdf_processor.py -v

# Run with coverage
pytest --cov=src tests/

# Generate PDFs from templates
cd example_contracts
python generate_pdfs.py

# Run Q&A evaluation
cd eval
python evaluate_qa.py
```

### Database Access

```bash
# Connect to database
docker exec -it contract_postgres psql -U postgres -d contract_intelligence

# Useful SQL queries
SELECT COUNT(*) FROM documents;
SELECT COUNT(*) FROM document_chunks;
SELECT COUNT(*) FROM extractions;
SELECT * FROM audit_findings ORDER BY severity DESC LIMIT 10;
```

## Project Structure Quick Reference

```
src/
├── main.py              - FastAPI app & endpoints
├── models/
│   ├── database.py     - SQLAlchemy models
│   └── schemas.py      - Pydantic request/response models
├── services/
│   ├── pdf_processor.py    - PDF extraction & chunking
│   ├── llm_service.py      - OpenAI integration
│   ├── vector_search.py    - Semantic search
│   └── audit_service.py    - Risk detection
└── db/
    └── database.py     - Database connection
```

## Environment Variables

```bash
# Required
OPENAI_API_KEY=sk-...           # OpenAI API key
DATABASE_URL=postgresql://...   # PostgreSQL connection

# Optional
API_HOST=0.0.0.0               # API host (default: 0.0.0.0)
API_PORT=8000                  # API port (default: 8000)
DEBUG=false                    # Debug mode (default: false)
MAX_FILE_SIZE_MB=50           # Max PDF size (default: 50)
MAX_FILES_PER_REQUEST=10      # Max files per upload (default: 10)
```

## Key Files

- `README.md` - Quick start guide
- `PROJECT_SUMMARY.md` - Complete implementation summary
- `docs/design-doc.md` - Architecture & design rationale
- `docs/api-documentation.md` - API reference
- `prompts/*.md` - LLM prompt documentation
- `setup.sh` - Automated setup script
- `test_api.sh` - API testing script

## Troubleshooting

### API won't start
```bash
# Check logs
docker-compose logs api

# Common issues:
# 1. OPENAI_API_KEY not set in .env
# 2. Port 8000 already in use
# 3. Database not ready - wait 10-15 seconds after docker-compose up
```

### Database connection errors
```bash
# Restart database
docker-compose restart postgres

# Check database health
docker exec contract_postgres pg_isready

# Recreate database
docker-compose down -v  # WARNING: Deletes data
docker-compose up -d
```

### OpenAI API errors
```bash
# Verify API key
echo $OPENAI_API_KEY

# Check quota: https://platform.openai.com/usage

# Test with fallback (rule-based extraction still works)
```

### PDF processing errors
```bash
# Ensure PDF is valid (not encrypted, not scanned)
# Check file size (must be < MAX_FILE_SIZE_MB)
# Try with example contracts first
```

## Performance Tuning

### Database
```sql
-- Check index usage
SELECT schemaname, tablename, indexname, idx_scan 
FROM pg_stat_user_indexes 
ORDER BY idx_scan;

-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM document_chunks WHERE ...;
```

### API
```python
# Adjust chunk size in PDFProcessor
chunk_size = 1000  # Increase for fewer chunks, better context
chunk_overlap = 200  # Increase to prevent boundary issues

# Adjust vector search top-k
top_k = 5  # Increase for more context, slower queries
```

## Common Workflows

### Testing New Contract
```bash
# 1. Upload
DOC_ID=$(curl -s -X POST http://localhost:8000/ingest \
  -F "files=@contract.pdf" | jq -r '.document_ids[0]')

# 2. Extract fields
curl -X POST http://localhost:8000/extract \
  -H "Content-Type: application/json" \
  -d "{\"document_id\":\"$DOC_ID\"}" | jq

# 3. Audit risks
curl -X POST http://localhost:8000/audit \
  -H "Content-Type: application/json" \
  -d "{\"document_id\":\"$DOC_ID\"}" | jq

# 4. Ask questions
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d "{\"question\":\"What is the liability cap?\",\"document_ids\":[\"$DOC_ID\"]}" | jq
```

### Adding New Risk Rule
1. Edit `src/services/audit_service.py`
2. Add new `_check_*` method with regex patterns
3. Add to `audit_contract()` method
4. Document in `prompts/audit_rules.md`
5. Add test in `tests/unit/test_audit_service.py`

### Customizing Extraction Fields
1. Edit `src/models/database.py` - add column to Extraction
2. Edit `src/models/schemas.py` - add field to ExtractionResponse
3. Edit `prompts/extraction_prompt.md` - update prompt template
4. Edit `src/services/llm_service.py` - update extraction logic
5. Create migration for database schema change

## API Response Examples

### Successful Extraction
```json
{
  "parties": ["Acme Corp", "Tech Solutions Inc"],
  "effective_date": "January 1, 2024",
  "term": "12 months",
  "liability_cap": {"amount": 500000, "currency": "USD"},
  "confidence_score": 0.85
}
```

### Audit Finding
```json
{
  "risk_type": "auto_renewal_short_notice",
  "severity": "high",
  "title": "Auto-renewal with 15-day notice",
  "evidence": "...automatically renew...",
  "confidence_score": 0.9
}
```

### Q&A Answer
```json
{
  "answer": "The liability cap is $500,000 USD...",
  "citations": [{
    "document_id": "...",
    "page": 3,
    "text": "...liability shall not exceed $500,000..."
  }]
}
```

## Support

- Documentation: `docs/` directory
- Issues: Create GitHub issue (if applicable)
- API Docs: http://localhost:8000/docs (when running)

## Quick Tips

- Always check `/healthz` before testing
- Use `/docs` for interactive API exploration
- Check `docker-compose logs` for debugging
- Start with example contracts for testing
- Run evaluation framework to verify Q&A quality
- Monitor OpenAI API costs at platform.openai.com
