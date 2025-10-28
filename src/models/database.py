"""Database models for Contract Intelligence API."""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, JSON, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

Base = declarative_base()


class Document(Base):
    """Uploaded contract document."""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(String(100), unique=True, nullable=False, index=True)
    filename = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    page_count = Column(Integer, nullable=False)
    content_hash = Column(String(64), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    extractions = relationship("Extraction", back_populates="document", cascade="all, delete-orphan")
    audit_findings = relationship("AuditFinding", back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base):
    """Chunked text segments from documents with embeddings."""
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    page_number = Column(Integer, nullable=True)
    text = Column(Text, nullable=False)
    char_start = Column(Integer, nullable=False)
    char_end = Column(Integer, nullable=False)
    embedding = Column(Vector(1536), nullable=True)  # OpenAI ada-002 dimension
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    document = relationship("Document", back_populates="chunks")

    __table_args__ = (
        Index('ix_document_chunks_embedding', 'embedding', postgresql_using='ivfflat'),
    )


class Extraction(Base):
    """Structured field extraction from contracts."""
    __tablename__ = "extractions"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    extraction_id = Column(String(100), unique=True, nullable=False, index=True)
    
    # Extracted fields (JSON)
    parties = Column(JSON, nullable=True)  # List of party names
    effective_date = Column(String(100), nullable=True)
    term = Column(String(200), nullable=True)
    governing_law = Column(String(200), nullable=True)
    payment_terms = Column(Text, nullable=True)
    termination = Column(Text, nullable=True)
    auto_renewal = Column(String(200), nullable=True)
    confidentiality = Column(Text, nullable=True)
    indemnity = Column(Text, nullable=True)
    liability_cap_amount = Column(Float, nullable=True)
    liability_cap_currency = Column(String(10), nullable=True)
    signatories = Column(JSON, nullable=True)  # List of {name, title}
    
    # Metadata
    extraction_method = Column(String(50), nullable=False)  # 'llm' or 'rule_based'
    confidence_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    document = relationship("Document", back_populates="extractions")


class AuditFinding(Base):
    """Risk detection findings for contracts."""
    __tablename__ = "audit_findings"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    finding_id = Column(String(100), unique=True, nullable=False, index=True)
    
    # Finding details
    risk_type = Column(String(100), nullable=False)  # e.g., 'auto_renewal', 'unlimited_liability'
    severity = Column(String(20), nullable=False)  # 'low', 'medium', 'high', 'critical'
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    
    # Evidence
    evidence_text = Column(Text, nullable=True)
    page_number = Column(Integer, nullable=True)
    char_start = Column(Integer, nullable=True)
    char_end = Column(Integer, nullable=True)
    
    # Metadata
    detection_method = Column(String(50), nullable=False)  # 'rule_based' or 'llm'
    confidence_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    document = relationship("Document", back_populates="audit_findings")


class QueryLog(Base):
    """Log of Q&A queries for analytics."""
    __tablename__ = "query_logs"

    id = Column(Integer, primary_key=True, index=True)
    query_id = Column(String(100), unique=True, nullable=False, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=True)
    document_ids = Column(JSON, nullable=True)  # List of document IDs queried
    citations = Column(JSON, nullable=True)  # List of citation objects
    response_time_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
