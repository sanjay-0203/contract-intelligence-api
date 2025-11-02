# Contract Intelligence API
AI-powered contract analysis system with extraction, question answering, and risk detection capabilities.

## Features
- **Document Ingestion:** Upload multiple PDF contracts with text extraction and chunking
- **Structured Extraction:** Extract key contract fields (parties, dates, terms, liability caps, etc.)
- **Question Answering:** RAG-based Q&A with citations to specific document locations
- **Risk Auditing:** Detect problematic clauses (auto-renewal, unlimited liability, broad indemnity)
- **Streaming Support:** Real-time token streaming for long-running queries
- **Production Ready:** Docker deployment, health checks, metrics, comprehensive testing

## Quick Start

### Prerequisites
- Docker and Docker Compose
- OpenAI API key

### Setup
Clone the repository and navigate to the project directory:
```bash
cd contract-intelligence-api
