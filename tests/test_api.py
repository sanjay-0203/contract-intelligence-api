import pytest
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app, get_db
from app.models import Base
from app.database import init_db
from app.rule_engine import RuleBasedAuditEngine

# Use in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

class TestHealthEndpoint:
    def test_health_check(self):
        """Test /healthz endpoint."""
        response = client.get("/healthz")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert data["version"] == "1.0.0"

class TestMetricsEndpoint:
    def test_metrics_endpoint(self):
        """Test /metrics endpoint."""
        response = client.get("/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "ingest_count" in data
        assert "extract_count" in data
        assert "ask_count" in data
        assert "audit_count" in data
        assert "total_documents" in data
        assert "total_chunks" in data

class TestRuleEngine:
    def test_auto_renewal_detection(self):
        """Test auto-renewal clause detection."""
        engine = RuleBasedAuditEngine()
        text = "The contract will auto-renew after 15 days notice."
        findings = engine.audit(text)
        
        assert len(findings) > 0
        assert any(f["finding_type"] == "Insufficient Auto-Renewal Notice" for f in findings)
    
    def test_unlimited_liability_detection(self):
        """Test unlimited liability detection."""
        engine = RuleBasedAuditEngine()
        text = "The parties agree to unlimited liability for all claims."
        findings = engine.audit(text)
        
        assert len(findings) > 0
        assert any(f["severity"] == "critical" for f in findings)
    
    def test_broad_indemnity_detection(self):
        """Test broad indemnity detection."""
        engine = RuleBasedAuditEngine()
        text = "Party A indemnifies Party B against any and all claims arising."
        findings = engine.audit(text)
        
        assert len(findings) > 0
        assert any(f["finding_type"] == "Broad Indemnity Clause" for f in findings)
    
    def test_no_findings_clean_text(self):
        """Test clean contract text returns no findings."""
        engine = RuleBasedAuditEngine()
        text = "This is a standard contract with normal terms and conditions."
        findings = engine.audit(text)
        
        # Should have minimal or no findings
        assert len(findings) <= 1

class TestEdgeCases:
    def test_empty_text_extraction(self):
        """Test extraction with empty text."""
        from app.llm_service import extract_contract_fields
        result = extract_contract_fields("")
        
        assert isinstance(result, dict)
        assert "parties" in result
        assert isinstance(result["parties"], list)
    
    def test_very_long_text_chunking(self):
        """Test chunking with very long text."""
        from app.pdf_processor import chunk_text
        
        # Create a very long text
        long_text = "This is a contract. " * 1000
        chunks = chunk_text(long_text, chunk_size=500, overlap=50)
        
        assert len(chunks) > 1
        assert all("text" in chunk for chunk in chunks)
        assert all("char_start" in chunk for chunk in chunks)
        assert all("char_end" in chunk for chunk in chunks)
    
    def test_special_characters_in_text(self):
        """Test handling special characters."""
        engine = RuleBasedAuditEngine()
        text = "Contract © 2024 with special chars: é, ñ, 中文"
        findings = engine.audit(text)
        
        # Should not raise an error
        assert isinstance(findings, list)

class TestIngestValidation:
    def test_ingest_requires_files(self):
        """Test that ingest endpoint requires files."""
        response = client.post("/ingest")
        assert response.status_code == 422  # Unprocessable Entity

class TestAskValidation:
    def test_ask_requires_parameters(self):
        """Test that ask endpoint requires parameters."""
        response = client.post("/ask")
        assert response.status_code == 422

class TestAuditValidation:
    def test_audit_requires_document_id(self):
        """Test that audit endpoint requires document_id."""
        response = client.post("/audit")
        assert response.status_code == 422

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
