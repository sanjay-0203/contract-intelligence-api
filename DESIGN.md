# DESIGN
Architecture:
- FastAPI HTTP API
- SQLite metadata DB (documents, chunks)
- PDF extraction with pdfplumber (page-aware)
- TF-IDF retriever over chunks (scikit-learn)
- Simple rule-based audit & extraction heuristics (regex/sentences)
Chunking:
- Page-aware chunks (max 1000 chars) with 200-char overlap
- Store char offsets for citations
Security & privacy:
- .env for secrets (not checked into repo). Optionally redact PII before sending to external LLMs.
