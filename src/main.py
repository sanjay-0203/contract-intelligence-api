"""Main FastAPI application with all API endpoints."""
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
import time
from datetime import datetime
import logging
import os

from src.models import schemas
from src.models.database import Document, DocumentChunk, Extraction, AuditFinding, QueryLog
from src.db.database import get_db, init_db
from src.services.pdf_processor import PDFProcessor
from src.services.llm_service import LLMService
from src.services.vector_search import VectorSearchService
from src.services.audit_service import AuditService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Contract Intelligence API",
    description="AI-powered contract analysis with extraction, Q&A, and risk detection",
    version="1.0.0"
)

# Global metrics
metrics = {
    "documents_ingested": 0,
    "extractions_performed": 0,
    "queries_answered": 0,
    "audits_performed": 0,
    "start_time": time.time()
}

# Initialize services
pdf_processor = PDFProcessor()
llm_service = None  # Will be initialized on first request


def get_llm_service():
    """Get or initialize LLM service."""
    global llm_service
    if llm_service is None:
        try:
            llm_service = LLMService()
        except Exception as e:
            logger.error(f"Failed to initialize LLM service: {e}")
            raise HTTPException(status_code=503, detail="LLM service unavailable")
    return llm_service


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized successfully")


@app.post("/ingest", response_model=schemas.DocumentUploadResponse)
async def ingest_documents(
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload and ingest 1 or more PDF contracts.
    
    Returns list of document IDs for ingested files.
    """
    max_files = int(os.getenv("MAX_FILES_PER_REQUEST", "10"))
    max_size_mb = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
    max_size_bytes = max_size_mb * 1024 * 1024
    
    if len(files) > max_files:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum {max_files} files allowed per request"
        )
    
    document_ids = []
    # llm = get_llm_service() # Moved inside the loop to ensure clean initialization if needed
    
    for file in files:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail=f"File {file.filename} is not a PDF"
            )
        
        # Read file content
        content = await file.read()
        file_size = len(content)
        
        if file_size > max_size_bytes:
            raise HTTPException(
                status_code=400,
                detail=f"File {file.filename} exceeds {max_size_mb}MB limit"
            )
        
        # Extract text from PDF
        try:
            full_text, page_count, pages_info = pdf_processor.extract_text(content)
            content_hash = pdf_processor.compute_hash(content)
        except Exception as e:
            logger.error(f"Failed to process {file.filename}: {e}")
            raise HTTPException(
                status_code=400,
                detail=f"Failed to process PDF: {str(e)}"
            )
        
        # Create document record
        document_id = str(uuid.uuid4())
        document = Document(
            document_id=document_id,
            filename=file.filename,
            file_size=file_size,
            page_count=page_count,
            content_hash=content_hash
        )
        db.add(document)
        db.flush()
        
        # Create chunks and embeddings
        chunks = pdf_processor.chunk_text(full_text, pages_info)
        
        for chunk_data in chunks:
            # Create embedding for chunk
            # NOTE: Embedding creation is a heavy operation. It should ideally be
            # offloaded to a background worker (like Celery/Redis Queue) or a
            # dedicated background task. For simplicity, we'll keep it synchronous
            # but wrap the exception properly.
            llm = get_llm_service() # Get LLM service inside the loop
            try:
                embedding = llm.create_embedding(chunk_data["text"])
            except Exception as e:
                logger.error(f"Failed to create embedding for chunk: {e}")
                embedding = None
            
            chunk = DocumentChunk(
                document_id=document.id,
                chunk_index=chunk_data["chunk_index"],
                page_number=chunk_data["page_number"],
                text=chunk_data["text"],
                char_start=chunk_data["char_start"],
                char_end=chunk_data["char_end"],
                embedding=embedding
            )
            db.add(chunk)
        
        db.commit()
        document_ids.append(document_id)
        
        logger.info(f"Ingested document {document_id}: {file.filename} ({page_count} pages, {len(chunks)} chunks)")
        
        # IMPORTANT: Ensure the file handle is closed after reading
        await file.close()
    
    metrics["documents_ingested"] += len(document_ids)
    
    return schemas.DocumentUploadResponse(
        document_ids=document_ids,
        uploaded_count=len(document_ids),
        message=f"Successfully ingested {len(document_ids)} document(s)"
    )


@app.post("/extract", response_model=schemas.ExtractionResponse)
async def extract_fields(
    request: schemas.ExtractionRequest,
    db: Session = Depends(get_db)
):
    """
    Extract structured fields from a contract document.
    
    Returns JSON with parties, dates, terms, and other contract metadata.
    """
    # Get document
    document = db.query(Document).filter(
        Document.document_id == request.document_id
    ).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Get full text from chunks
    chunks = db.query(DocumentChunk).filter(
        DocumentChunk.document_id == document.id
    ).order_by(DocumentChunk.chunk_index).all()
    
    full_text = " ".join([chunk.text for chunk in chunks])
    
    # Extract fields using LLM
    # llm = get_llm_service() # Moved inside the loop to ensure clean initialization if needed
    try:
        extracted_data = llm.extract_fields(full_text)
    except Exception as e:
        logger.error(f"Extraction failed for {request.document_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Field extraction failed"
        )
    
    # Save extraction to database
    extraction_id = str(uuid.uuid4())
    
    extraction = Extraction(
        document_id=document.id,
        extraction_id=extraction_id,
        parties=extracted_data.get("parties"),
        effective_date=extracted_data.get("effective_date"),
        term=extracted_data.get("term"),
        governing_law=extracted_data.get("governing_law"),
        payment_terms=extracted_data.get("payment_terms"),
        termination=extracted_data.get("termination"),
        auto_renewal=extracted_data.get("auto_renewal"),
        confidentiality=extracted_data.get("confidentiality"),
        indemnity=extracted_data.get("indemnity"),
        liability_cap_amount=extracted_data.get("liability_cap_amount"),
        liability_cap_currency=extracted_data.get("liability_cap_currency"),
        signatories=extracted_data.get("signatories"),
        extraction_method=extracted_data.get("extraction_method", "llm"),
        confidence_score=extracted_data.get("confidence_score")
    )
    db.add(extraction)
    db.commit()
    
    metrics["extractions_performed"] += 1
    
    # Build response
    liability_cap = None
    if extraction.liability_cap_amount is not None:
        liability_cap = {
            "amount": extraction.liability_cap_amount,
            "currency": extraction.liability_cap_currency or "USD"
        }
    
    signatories = None
    if extraction.signatories:
        signatories = [
            schemas.Signatory(**sig) for sig in extraction.signatories
        ]
    
    return schemas.ExtractionResponse(
        document_id=request.document_id,
        extraction_id=extraction_id,
        parties=extraction.parties,
        effective_date=extraction.effective_date,
        term=extraction.term,
        governing_law=extraction.governing_law,
        payment_terms=extraction.payment_terms,
        termination=extraction.termination,
        auto_renewal=extraction.auto_renewal,
        confidentiality=extraction.confidentiality,
        indemnity=extraction.indemnity,
        liability_cap=liability_cap,
        signatories=signatories,
        confidence_score=extraction.confidence_score,
        extraction_method=extraction.extraction_method
    )


@app.post("/ask", response_model=schemas.AskResponse)
async def ask_question(
    request: schemas.AskRequest,
    db: Session = Depends(get_db)
):
    """
    Answer a question about uploaded contracts using RAG.
    
    Returns answer with citations (document ID, page, character ranges).
    """
    start_time = time.time()
    
    # llm = get_llm_service() # Moved inside the loop to ensure clean initialization if needed
    
    # Create embedding for question
    question_embedding = llm.create_embedding(request.question)
    
    # Search for relevant chunks
    vector_search = VectorSearchService(db)
    relevant_chunks = vector_search.search_similar_chunks(
        query_embedding=question_embedding,
        document_ids=request.document_ids,
        top_k=request.max_citations
    )
    
    if not relevant_chunks:
        raise HTTPException(
            status_code=404,
            detail="No relevant documents found"
        )
    
    # Generate answer
    context_texts = [chunk["text"] for chunk in relevant_chunks]
    answer = llm.answer_question(request.question, context_texts)
    
    # Build citations
    citations = []
    for chunk in relevant_chunks:
        citations.append(schemas.Citation(
            document_id=chunk["document_id"],
            page=chunk["page_number"],
            char_start=chunk["char_start"],
            char_end=chunk["char_end"],
            text=chunk["text"][:200] + "..." if len(chunk["text"]) > 200 else chunk["text"]
        ))
    
    # Calculate response time
    response_time_ms = int((time.time() - start_time) * 1000)
    
    # Log query
    query_id = str(uuid.uuid4())
    query_log = QueryLog(
        query_id=query_id,
        question=request.question,
        answer=answer,
        document_ids=request.document_ids,
        citations=[c.dict() for c in citations],
        response_time_ms=response_time_ms
    )
    db.add(query_log)
    db.commit()
    
    metrics["queries_answered"] += 1
    
    return schemas.AskResponse(
        query_id=query_id,
        question=request.question,
        answer=answer,
        citations=citations,
        response_time_ms=response_time_ms
    )


@app.post("/audit", response_model=schemas.AuditResponse)
async def audit_contract(
    request: schemas.AuditRequest,
    db: Session = Depends(get_db)
):
    """
    Audit contract for risky clauses.
    
    Returns findings with severity levels and evidence spans.
    """
    # Get document
    document = db.query(Document).filter(
        Document.document_id == request.document_id
    ).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Get full text
    chunks = db.query(DocumentChunk).filter(
        DocumentChunk.document_id == document.id
    ).order_by(DocumentChunk.chunk_index).all()
    
    full_text = " ".join([chunk.text for chunk in chunks])
    
    # Run audit
    audit_service = AuditService(db)
    findings_data = audit_service.audit_contract(request.document_id, full_text)
    
    # Save findings to database
    findings_response = []
    severity_counts = {"high": 0, "medium": 0, "low": 0}
    
    for finding_data in findings_data:
        finding_id = str(uuid.uuid4())
        
        # Determine page number from character position
        page_num = None
        if finding_data.get("char_start") is not None:
            for chunk in chunks:
                if chunk.char_start <= finding_data["char_start"] <= chunk.char_end:
                    page_num = chunk.page_number
                    break
        
        audit_finding = AuditFinding(
            document_id=document.id,
            finding_id=finding_id,
            risk_type=finding_data["risk_type"],
            severity=finding_data["severity"],
            title=finding_data["title"],
            description=finding_data["description"],
            evidence_text=finding_data.get("evidence_text"),
            page_number=page_num or finding_data.get("page"),
            char_start=finding_data.get("char_start"),
            char_end=finding_data.get("char_end"),
            detection_method=finding_data.get("detection_method", "rule_based"),
            confidence_score=finding_data.get("confidence_score")
        )
        db.add(audit_finding)
        
        # Count severity
        if finding_data["severity"] in severity_counts:
            severity_counts[finding_data["severity"]] += 1
        
        findings_response.append(schemas.AuditFinding(
            finding_id=finding_id,
            risk_type=finding_data["risk_type"],
            severity=finding_data["severity"],
            title=finding_data["title"],
            description=finding_data["description"],
            evidence=finding_data.get("evidence_text"),
            page=page_num,
            char_start=finding_data.get("char_start"),
            char_end=finding_data.get("char_end"),
            confidence_score=finding_data.get("confidence_score")
        ))
    
    db.commit()
    
    metrics["audits_performed"] += 1
    
    return schemas.AuditResponse(
        document_id=request.document_id,
        findings=findings_response,
        total_findings=len(findings_response),
        high_severity_count=severity_counts["high"],
        medium_severity_count=severity_counts["medium"],
        low_severity_count=severity_counts["low"]
    )


@app.get("/ask/stream")
async def stream_question(
    question: str,
    document_ids: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Stream answer tokens for a question using Server-Sent Events.
    """
    # llm = get_llm_service() # Moved inside the loop to ensure clean initialization if needed
    
    # Parse document_ids if provided
    doc_ids = document_ids.split(",") if document_ids else None
    
    # Create embedding and search
    question_embedding = llm.create_embedding(question)
    vector_search = VectorSearchService(db)
    relevant_chunks = vector_search.search_similar_chunks(
        query_embedding=question_embedding,
        document_ids=doc_ids,
        top_k=5
    )
    
    if not relevant_chunks:
        return JSONResponse({"error": "No relevant documents found"}, status_code=404)
    
    # Generate streaming response
    async def generate():
        context_texts = [chunk["text"] for chunk in relevant_chunks]
        context = "\n\n".join(context_texts)
        
        prompt = f"""Answer the following question based on the provided contract excerpts.

Context:
{context}

Question: {question}

Answer:"""
        
        try:
            stream = llm.client.chat.completions.create(
                model=llm.qa_model,
                messages=[
                    {"role": "system", "content": "You are a legal document analyst."},
                    {"role": "user", "content": prompt}
                ],
                stream=True,
                temperature=0.2,
                max_tokens=1000
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield f"data: {chunk.choices[0].delta.content}\n\n"
            
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            yield f"data: Error: {str(e)}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")


@app.get("/healthz", response_model=schemas.HealthResponse)
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint."""
    # Check database
    db_status = "healthy"
    try:
        db.execute("SELECT 1")
    except:
        db_status = "unhealthy"
    
    # Check OpenAI
    openai_status = "healthy"
    try:
        get_llm_service()
    except:
        openai_status = "unavailable"
    
    overall_status = "healthy" if db_status == "healthy" else "degraded"
    
    return schemas.HealthResponse(
        status=overall_status,
        timestamp=datetime.utcnow(),
        database=db_status,
        openai=openai_status,
        version="1.0.0"
    )


@app.get("/metrics", response_model=schemas.MetricsResponse)
async def get_metrics():
    """Get API usage metrics."""
    uptime = int(time.time() - metrics["start_time"])
    
    return schemas.MetricsResponse(
        documents_ingested=metrics["documents_ingested"],
        extractions_performed=metrics["extractions_performed"],
        queries_answered=metrics["queries_answered"],
        audits_performed=metrics["audits_performed"],
        uptime_seconds=uptime
    )


@app.post("/webhook/events")
async def webhook_events(event: schemas.WebhookEvent):
    """
    Webhook endpoint for receiving event notifications.
    
    This is a placeholder for external systems to send events.
    """
    logger.info(f"Received webhook event: {event.event_type}")
    
    # Here you would process the webhook event
    # For now, just acknowledge receipt
    
    return {"status": "received", "event_type": event.event_type}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", "8000")),
        reload=os.getenv("DEBUG", "false").lower() == "true"
    )
