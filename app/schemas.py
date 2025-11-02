from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class IngestResponse(BaseModel):
    document_ids: List[int]
    count: int
    message: str

class Citation(BaseModel):
    document_id: int
    page_number: int
    char_start: int
    char_end: int
    text: str

class AskResponse(BaseModel):
    question: str
    answer: str
    citations: List[Citation]
    confidence: float

class ExtractResponse(BaseModel):
    document_id: int
    parties: List[str] = []
    effective_date: Optional[str] = None
    term: Optional[str] = None
    governing_law: Optional[str] = None
    payment_terms: Optional[str] = None
    termination: Optional[str] = None
    auto_renewal: Optional[bool] = None
    confidentiality: Optional[str] = None
    indemnity: Optional[str] = None
    liability_cap: Optional[Dict[str,Any]] = None
    signatories: List[Dict[str,str]] = []

class AuditFinding(BaseModel):
    finding_type: str
    severity: str
    description: str
    evidence_text: str

class AuditResponse(BaseModel):
    document_id: int
    findings: List[AuditFinding]
    total_findings: int