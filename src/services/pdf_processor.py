"""PDF processing service for text extraction."""
import hashlib
from typing import List, Dict, Tuple
import PyPDF2
import pdfplumber
from io import BytesIO


class PDFProcessor:
    """Process PDF files and extract text content."""
    
    def __init__(self):
        self.chunk_size = 1000  # characters per chunk
        self.chunk_overlap = 200  # overlap between chunks
    
    def extract_text(self, pdf_bytes: bytes) -> Tuple[str, int, List[Dict]]:
        """
        Extract full text from PDF.
        
        Returns:
            Tuple of (full_text, page_count, pages_info)
            pages_info: List of {page_num, text, char_start, char_end}
        """
        pages_info = []
        full_text = ""
        char_position = 0
        
        try:
            with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
                page_count = len(pdf.pages)
                
                for i, page in enumerate(pdf.pages, start=1):
                    page_text = page.extract_text() or ""
                    
                    # Clean up text
                    page_text = self._clean_text(page_text)
                    
                    char_start = char_position
                    char_end = char_position + len(page_text)
                    
                    pages_info.append({
                        "page_num": i,
                        "text": page_text,
                        "char_start": char_start,
                        "char_end": char_end
                    })
                    
                    full_text += page_text + "\n"
                    char_position = char_end + 1  # +1 for newline
                
                return full_text.strip(), page_count, pages_info
                
        except Exception as e:
            # Fallback to PyPDF2 if pdfplumber fails
            return self._extract_with_pypdf2(pdf_bytes)
    
    def _extract_with_pypdf2(self, pdf_bytes: bytes) -> Tuple[str, int, List[Dict]]:
        """Fallback extraction using PyPDF2."""
        pages_info = []
        full_text = ""
        char_position = 0
        
        pdf_reader = PyPDF2.PdfReader(BytesIO(pdf_bytes))
        page_count = len(pdf_reader.pages)
        
        for i, page in enumerate(pdf_reader.pages, start=1):
            page_text = page.extract_text() or ""
            page_text = self._clean_text(page_text)
            
            char_start = char_position
            char_end = char_position + len(page_text)
            
            pages_info.append({
                "page_num": i,
                "text": page_text,
                "char_start": char_start,
                "char_end": char_end
            })
            
            full_text += page_text + "\n"
            char_position = char_end + 1
        
        return full_text.strip(), page_count, pages_info
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted text."""
        # Remove excessive whitespace
        text = " ".join(text.split())
        # Remove null bytes
        text = text.replace("\x00", "")
        return text
    
    def chunk_text(self, text: str, page_info: List[Dict]) -> List[Dict]:
        """
        Split text into overlapping chunks for vector search.
        
        Returns:
            List of {chunk_index, text, char_start, char_end, page_number}
        """
        chunks = []
        chunk_index = 0
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # Find the last sentence boundary before chunk_size
            if end < len(text):
                # Look for sentence endings
                for delimiter in [". ", ".\n", "! ", "?\n"]:
                    last_delimiter = text.rfind(delimiter, start, end)
                    if last_delimiter != -1:
                        end = last_delimiter + 1
                        break
            
            chunk_text = text[start:end].strip()
            
            if chunk_text:
                # Find which page this chunk belongs to
                page_num = self._find_page_number(start, page_info)
                
                chunks.append({
                    "chunk_index": chunk_index,
                    "text": chunk_text,
                    "char_start": start,
                    "char_end": end,
                    "page_number": page_num
                })
                chunk_index += 1
            
            # Move start position with overlap
            start = end - self.chunk_overlap if end < len(text) else len(text)
        
        return chunks
    
    def _find_page_number(self, char_position: int, page_info: List[Dict]) -> int:
        """Find which page a character position belongs to."""
        for page in page_info:
            if page["char_start"] <= char_position <= page["char_end"]:
                return page["page_num"]
        return 1  # Default to first page
    
    def compute_hash(self, pdf_bytes: bytes) -> str:
        """Compute SHA-256 hash of PDF content."""
        return hashlib.sha256(pdf_bytes).hexdigest()
