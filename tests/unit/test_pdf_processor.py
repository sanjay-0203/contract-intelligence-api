"""Unit tests for PDF processor service."""
import pytest
from src.services.pdf_processor import PDFProcessor


@pytest.fixture
def pdf_processor():
    return PDFProcessor()


def test_clean_text(pdf_processor):
    """Test text cleaning."""
    dirty_text = "This  is   a    test\n\n\n  text"
    clean = pdf_processor._clean_text(dirty_text)
    assert clean == "This is a test text"


def test_chunk_text(pdf_processor):
    """Test text chunking."""
    text = "This is a test. " * 200  # Long text
    page_info = [{"page_num": 1, "char_start": 0, "char_end": len(text)}]
    
    chunks = pdf_processor.chunk_text(text, page_info)
    
    assert len(chunks) > 1
    assert all("chunk_index" in c for c in chunks)
    assert all("text" in c for c in chunks)
    assert all("char_start" in c for c in chunks)
    assert all("char_end" in c for c in chunks)
    assert all("page_number" in c for c in chunks)


def test_compute_hash(pdf_processor):
    """Test hash computation."""
    content1 = b"test content"
    content2 = b"test content"
    content3 = b"different content"
    
    hash1 = pdf_processor.compute_hash(content1)
    hash2 = pdf_processor.compute_hash(content2)
    hash3 = pdf_processor.compute_hash(content3)
    
    assert hash1 == hash2
    assert hash1 != hash3
    assert len(hash1) == 64  # SHA-256 hex length
