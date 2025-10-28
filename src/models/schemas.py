"""Pydantic schemas for request/response validation."""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class DocumentUploadResponse(BaseModel):
    """Response for document upload."""
    document_ids: List[str]
    uploaded_count: int
    message: str


class ExtractionRequest(BaseModel):
    """Request to extract structured data from document."""
    document_id: str


class Signatory(BaseModel):
    """Signatory information."""
    name: str
    title: Optional[str] = None


class ExtractionResponse(BaseModel):
    """Structured extraction results."""
    document_id: str
    extraction_id: str
    parties: Optional[List[str]] = None
    effective_date: Optional[str] = None
    term: Optional[str] = None
    governing_law: Optional[str] = None
    payment_terms: Optional[str] = None
    termination: Optional[str] = None
    auto_renewal: Optional[str] = None
    confidentiality: Optional[str] = None
    indemnity: Optional[str] = None
    liability_cap: Optional[Dict[str, Any]] = None  # {"amount": float, "currency": str}
    signatories: Optional[List[Signatory]] = None
    confidence_score: Optional[float] = None
    extraction_method: str


class Citation(BaseModel):
    """Citation reference for answers."""
    document_id: str
    page: Optional[int] = None
    char_start: Optional[int] = None
    char_end: Optional[int] = None
    text: str


class AskRequest(BaseModel):
    """Question answering request."""
    question: str
    document_ids: Optional[List[str]] = None  # If None, search all documents
    max_citations: int = Field(default=5, ge=1, le=20)


class AskResponse(BaseModel):
    """Question answering response."""
    query_id: str
    question: str
    answer: str
    citations: List[Citation]
    response_time_ms: int


class AuditFinding(BaseModel):
    """Individual audit finding."""
    finding_id: str
    risk_type: str
    severity: str  # low, medium, high, critical
    title: str
    description: str
    evidence: Optional[str] = None
    page: Optional[int] = None
    char_start: Optional[int] = None
    char_end: Optional[int] = None
    confidence_score: Optional[float] = None


class AuditRequest(BaseModel):
    """Risk audit request."""
    document_id: str


class AuditResponse(BaseModel):
    """Risk audit results."""
    document_id: str
    findings: List[AuditFinding]
    total_findings: int
    high_severity_count: int
    medium_severity_count: int
    low_severity_count: int


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: datetime
    database: str
    openai: str
    version: str


class MetricsResponse(BaseModel):
    """Metrics response."""
    documents_ingested: int
    extractions_performed: int
    queries_answered: int
    audits_performed: int
    uptime_seconds: int


class WebhookEvent(BaseModel):
    """Webhook event payload."""
    event_type: str
    document_id: Optional[str] = None
    status: str
    timestamp: datetime
    data: Optional[Dict[str, Any]] = None
