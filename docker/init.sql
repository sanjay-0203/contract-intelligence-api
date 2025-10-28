-- Initialize database with pgvector extension

CREATE EXTENSION IF NOT EXISTS vector;

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE contract_intelligence TO postgres;
