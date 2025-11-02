import os, io, asyncio, json
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Request
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.orm import Session
from .db import engine, SessionLocal
from .models import Base, Document, Chunk
from .schemas import IngestResponse, AskResponse, Citation, ExtractResponse, AuditResponse, AuditFinding
from .utils import sha256_bytesio, extract_pdf_pages, chunk_text_pages
from .vectorstore import RETRIEVER
from typing import List
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select
import os

app = FastAPI(title='Contract Intelligence API - Fixed')

# create tables
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get('/healthz')
def healthz():
    return {'status':'ok'}

@app.get('/metrics')
def metrics():
    return {'documents_count': count_documents()}

def count_documents():
    db = SessionLocal()
    try:
        return db.query(Document).count()
    finally:
        db.close()

@app.post('/ingest', response_model=IngestResponse)
async def ingest(files: List[UploadFile] = File(...)):
    db = SessionLocal()
    created_ids = []
    try:
        for f in files:
            content = await f.read()
            file_hash = sha256_bytesio(content)
            # dedupe by hash
            existing = db.query(Document).filter(Document.file_hash==file_hash).first()
            if existing:
                created_ids.append(existing.id)
                continue
            doc = Document(filename=f.filename, file_hash=file_hash)
            db.add(doc)
            db.commit()
            db.refresh(doc)
            created_ids.append(doc.id)
            # extract pages and chunks
            pages = extract_pdf_pages(content)
            chunks = chunk_text_pages(pages)
            for page_number, start, end, text in chunks:
                ch = Chunk(document_id=doc.id, page_number=page_number, char_start=start, char_end=end, text=text)
                db.add(ch)
            db.commit()
        # rebuild retriever every ingest (simple approach)
        rebuild_retriever()
        return IngestResponse(document_ids=created_ids, count=len(created_ids), message=f"Successfully ingested {len(created_ids)} document(s)")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

def rebuild_retriever():
    db = SessionLocal()
    try:
        rows = db.query(Chunk).all()
        texts = [r.text for r in rows]
        ids = [r.id for r in rows]
        if len(texts)>0:
            RETRIEVER.fit(texts, ids)
    finally:
        db.close()

@app.post('/ask', response_model=AskResponse)
def ask(payload: dict):
    question = payload.get('question')
    document_id = payload.get('document_id')
    if not question:
        raise HTTPException(status_code=400, detail="question required")
    # retrieve
    results = RETRIEVER.query(question, top_k=5)
    citations = []
    db = SessionLocal()
    try:
        for r in results:
            ch = db.query(Chunk).filter(Chunk.id==r['id']).first()
            if ch:
                citations.append(Citation(document_id=ch.document_id, page_number=ch.page_number, char_start=ch.char_start, char_end=ch.char_end, text=ch.text))
        # simple answer: join top texts
        answer = "\n\n".join([c.text for c in citations]) or "No relevant information found."
        confidence = sum([r['score'] for r in results]) / (len(results) or 1)
        return AskResponse(question=question, answer=answer, citations=citations, confidence=confidence)
    finally:
        db.close()

@app.get('/ask/stream')
def ask_stream(question: str, document_id: int = None):
    # synchronous simple streaming of tokens from retrieved answer
    results = RETRIEVER.query(question, top_k=5)
    db = SessionLocal()
    texts = []
    try:
        for r in results:
            ch = db.query(Chunk).filter(Chunk.id==r['id']).first()
            if ch:
                texts.append(ch.text)
    finally:
        db.close()
    answer = "\n\n".join(texts) or "No relevant information found."
    async def event_generator():
        yield f"data: {json.dumps({'status':'processing','question':question})}\n\n"
        for token in answer.split():
            yield f"data: {json.dumps({'token': token})}\n\n"
            await asyncio.sleep(0.02)
        yield f"data: {json.dumps({'status':'complete','confidence': 0.9})}\n\n"
    return StreamingResponse(event_generator(), media_type='text/event-stream')

@app.post('/extract', response_model=ExtractResponse)
def extract(document_id: int):
    # heuristic-based extraction from concatenated chunks of the document
    db = SessionLocal()
    try:
        chunks = db.query(Chunk).filter(Chunk.document_id==document_id).order_by(Chunk.page_number).all()
        if not chunks:
            raise HTTPException(status_code=404, detail='document not found')
        full = "\n\n".join([c.text for c in chunks])
        # naive heuristics (regex could be improved)
        parties = []
        import re
        # look for 'between X and Y' pattern
        m = re.search(r'between\s+(.*?)\s+and\s+(.*?)[\.,\n]', full, re.I|re.S)
        if m:
            parties = [m.group(1).strip(), m.group(2).strip()]
        # dates
        m2 = re.search(r'effective date[:\s]*([A-Za-z0-9,\-\s]+)', full, re.I)
        eff = m2.group(1).strip() if m2 else None
        auto_renewal = bool(re.search(r'auto[- ]?renew', full, re.I))
        # liability cap
        m3 = re.search(r'liabilit[y|ies|y cap][:\s\$]*([0-9,\.]+)\s*(USD|EUR|INR|GBP)?', full, re.I)
        liability = None
        if m3:
            amt = m3.group(1).replace(',','')
            cur = m3.group(2) or 'USD'
            liability = {'amount': float(amt), 'currency': cur}
        # signatories: look for 'By:' lines
        signatories = []
        for s in re.findall(r'By:\s*(.*?)\n', full):
            signatories.append({'name': s.strip(), 'title': ''})
        return ExtractResponse(document_id=document_id, parties=parties, effective_date=eff, term=None, governing_law=None, payment_terms=None, termination=None, auto_renewal=auto_renewal, confidentiality=None, indemnity=None, liability_cap=liability, signatories=signatories)
    finally:
        db.close()

@app.post('/audit', response_model=AuditResponse)
def audit(document_id: int, use_llm: bool = True):
    # rule-based audits
    db = SessionLocal()
    try:
        chunks = db.query(Chunk).filter(Chunk.document_id==document_id).all()
        if not chunks:
            raise HTTPException(status_code=404, detail='document not found')
        full = "\n\n".join([c.text for c in chunks])
        findings = []
        import re
        if re.search(r'auto[- ]?renew', full, re.I):
            # find notice days
            m = re.search(r'notice.*?(\d{1,3})\s*days', full, re.I)
            days = int(m.group(1)) if m else None
            sev = 'high' if days and days<30 else 'medium'
            findings.append(AuditFinding(finding_type='AutoRenewal', severity=sev, description='Auto-renewal clause detected', evidence_text=m.group(0) if m else 'Auto-renewal language present'))
        if re.search(r'unlimited liabilit', full, re.I):
            findings.append(AuditFinding(finding_type='UnlimitedLiability', severity='critical', description='Unlimited liability language found', evidence_text='Unlimited liability'))
        total = len(findings)
        return AuditResponse(document_id=document_id, findings=findings, total_findings=total)
    finally:
        db.close()

@app.post('/webhook/events')
def webhook_events(payload: dict):
    # simple receiver for events; in real use you'd send events to external webhook destinations
    print('webhook received', payload)
    return {'received': True, 'payload': payload}