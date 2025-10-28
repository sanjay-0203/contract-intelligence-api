"""Unit tests for audit service."""
import pytest
from src.services.audit_service import AuditService
from unittest.mock import MagicMock


@pytest.fixture
def audit_service():
    db_mock = MagicMock()
    return AuditService(db_mock)


def test_check_auto_renewal_short_notice(audit_service):
    """Test detection of auto-renewal with short notice."""
    text = """
    This agreement will automatically renew for successive one-year terms
    unless either party provides written notice of non-renewal at least
    15 days prior to the end of the then-current term.
    """
    
    findings = audit_service._check_auto_renewal(text)
    
    assert len(findings) > 0
    assert findings[0]["risk_type"] == "auto_renewal_short_notice"
    assert findings[0]["severity"] in ["medium", "high"]


def test_check_unlimited_liability(audit_service):
    """Test detection of unlimited liability."""
    text = """
    The liability of the service provider under this agreement shall be
    unlimited and not subject to any cap or limitation.
    """
    
    findings = audit_service._check_unlimited_liability(text)
    
    assert len(findings) > 0
    assert findings[0]["risk_type"] == "unlimited_liability"
    assert findings[0]["severity"] == "critical"


def test_check_broad_indemnity(audit_service):
    """Test detection of broad indemnity clauses."""
    text = """
    Customer shall indemnify and hold harmless Provider from any and all
    claims, losses, damages, and liabilities, including without limitation
    attorney fees and costs.
    """
    
    findings = audit_service._check_broad_indemnity(text)
    
    assert len(findings) > 0
    assert findings[0]["risk_type"] == "broad_indemnity"
    assert findings[0]["severity"] in ["medium", "high"]


def test_no_findings_for_safe_contract(audit_service):
    """Test that safe contracts produce minimal findings."""
    text = """
    This is a standard service agreement between parties with balanced terms.
    The contract has a defined term of 12 months. Either party may terminate
    with 60 days written notice. Liability is capped at fees paid in the
    12 months prior to the claim. The agreement is governed by the laws
    of California.
    """
    
    findings = audit_service.audit_contract("doc_id", text)
    
    # Should have few or no high-severity findings
    high_severity = [f for f in findings if f["severity"] == "high"]
    assert len(high_severity) == 0
