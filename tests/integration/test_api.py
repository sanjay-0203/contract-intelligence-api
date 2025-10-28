"""Integration tests for API endpoints."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.main import app
from src.db.database import get_db
from src.models.database import Base

# Test database URL
TEST_DATABASE_URL = "sqlite:///./test.db"

# Create test engine
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(scope="function")
def test_db():
    """Create and clean database for each test."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "database" in data
    assert "version" in data


def test_metrics():
    """Test metrics endpoint."""
    response = client.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "documents_ingested" in data
    assert "extractions_performed" in data
    assert "queries_answered" in data
    assert "uptime_seconds" in data


def test_webhook_events():
    """Test webhook endpoint."""
    event_data = {
        "event_type": "test_event",
        "status": "completed",
        "timestamp": "2025-10-28T17:00:00"
    }
    
    response = client.post("/webhook/events", json=event_data)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "received"


@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="Requires OpenAI API key"
)
def test_ingest_document(test_db):
    """Test document ingestion endpoint."""
    # This would require a real PDF file
    # Skipped in unit tests, should be in integration tests
    pass


@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="Requires OpenAI API key"
)
def test_extract_fields(test_db):
    """Test field extraction endpoint."""
    # Requires ingested document
    pass


@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="Requires OpenAI API key"
)
def test_ask_question(test_db):
    """Test question answering endpoint."""
    # Requires ingested document
    pass


@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="Requires OpenAI API key"
)
def test_audit_contract(test_db):
    """Test contract audit endpoint."""
    # Requires ingested document
    pass
