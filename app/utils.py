import hashlib, os, io, math
from typing import List, Tuple
import pdfplumber

def sha256_bytesio(fbytes: bytes) -> str:
    return hashlib.sha256(fbytes).hexdigest()

def extract_pdf_pages(file_bytes: bytes) -> List[str]:
    text_pages = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for p in pdf.pages:
            text = p.extract_text() or ""
            text_pages.append(text)
    return text_pages

def chunk_text_pages(pages: List[str], max_chunk=1000, overlap=200):
    chunks = []
    for page_idx, ptext in enumerate(pages, start=1):
        if not ptext:
            continue
        start = 0
        L = len(ptext)
        while start < L:
            end = min(start + max_chunk, L)
            chunk_text = ptext[start:end]
            chunks.append((page_idx, start, end, chunk_text))
            if end == L:
                break
            start = max(0, end - overlap)
    return chunks