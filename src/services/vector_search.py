"""Vector search service for semantic document retrieval."""
from typing import List, Dict, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text
import numpy as np


class VectorSearchService:
    """Service for semantic search using vector embeddings."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def search_similar_chunks(
        self, 
        query_embedding: List[float], 
        document_ids: List[str] = None,
        top_k: int = 5
    ) -> List[Dict]:
        """
        Search for similar chunks using cosine similarity.
        
        Args:
            query_embedding: Query vector embedding
            document_ids: Optional list of document IDs to filter by
            top_k: Number of results to return
            
        Returns:
            List of matching chunks with similarity scores
        """
        # Build query with optional document filter
        query_str = """
        SELECT 
            dc.id,
            dc.text,
            dc.page_number,
            dc.char_start,
            dc.char_end,
            d.document_id,
            d.filename,
            1 - (dc.embedding <=> :query_embedding) as similarity
        FROM document_chunks dc
        JOIN documents d ON dc.document_id = d.id
        WHERE dc.embedding IS NOT NULL
        """
        
        params = {"query_embedding": query_embedding}
        
        if document_ids:
            query_str += " AND d.document_id = ANY(:document_ids)"
            params["document_ids"] = document_ids
        
        query_str += """
        ORDER BY dc.embedding <=> :query_embedding
        LIMIT :top_k
        """
        params["top_k"] = top_k
        
        result = self.db.execute(text(query_str), params)
        
        chunks = []
        for row in result:
            chunks.append({
                "chunk_id": row[0],
                "text": row[1],
                "page_number": row[2],
                "char_start": row[3],
                "char_end": row[4],
                "document_id": row[5],
                "filename": row[6],
                "similarity": float(row[7])
            })
        
        return chunks
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        vec1_np = np.array(vec1)
        vec2_np = np.array(vec2)
        
        dot_product = np.dot(vec1_np, vec2_np)
        norm1 = np.linalg.norm(vec1_np)
        norm2 = np.linalg.norm(vec2_np)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))
