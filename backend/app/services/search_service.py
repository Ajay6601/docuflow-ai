from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Float, or_, and_
from sqlalchemy.sql import text
from app.models.document import Document, DocumentStatus, DocumentType
from app.services.embedding_service import embedding_service
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class SearchService:
    """Service for document search - full-text and semantic."""
    
    @staticmethod
    def update_search_vector(db: Session, document_id: int):
        """
        Update the full-text search vector for a document.
        Uses PostgreSQL's to_tsvector function.
        """
        try:
            # Update search vector using SQL
            db.execute(
                text("""
                    UPDATE documents 
                    SET search_vector = 
                        setweight(to_tsvector('english', COALESCE(original_filename, '')), 'A') ||
                        setweight(to_tsvector('english', COALESCE(summary, '')), 'B') ||
                        setweight(to_tsvector('english', COALESCE(extracted_text, '')), 'C')
                    WHERE id = :doc_id
                """),
                {"doc_id": document_id}
            )
            db.commit()
            logger.info(f"Updated search vector for document {document_id}")
            
        except Exception as e:
            logger.error(f"Error updating search vector: {e}")
            db.rollback()
    
    @staticmethod
    def update_embedding(db: Session, document_id: int):
        """
        Generate and store embedding for a document.
        """
        try:
            document = db.query(Document).filter(Document.id == document_id).first()
            
            if not document or not document.extracted_text:
                logger.warning(f"Cannot generate embedding for document {document_id}: no text")
                return
            
            # Combine relevant text for embedding
            text_parts = []
            
            if document.original_filename:
                text_parts.append(document.original_filename)
            
            if document.summary:
                text_parts.append(document.summary)
            
            if document.extracted_text:
                # Use first 3000 chars of extracted text
                text_parts.append(document.extracted_text[:3000])
            
            combined_text = " ".join(text_parts)
            
            # Generate embedding
            embedding = embedding_service.generate_embedding(combined_text)
            
            if embedding:
                document.embedding = embedding
                db.commit()
                logger.info(f"Updated embedding for document {document_id}")
            else:
                logger.warning(f"Failed to generate embedding for document {document_id}")
                
        except Exception as e:
            logger.error(f"Error updating embedding: {e}")
            db.rollback()
    
    @staticmethod
    def full_text_search(
        db: Session,
        query: str,
        limit: int = 20,
        offset: int = 0,
        status_filter: Optional[DocumentStatus] = None,
        type_filter: Optional[DocumentType] = None
    ) -> tuple[List[Document], int]:
        """
        Perform full-text search using PostgreSQL tsvector.
        
        Returns:
            Tuple of (documents, total_count)
        """
        try:
            # Build base query
            base_query = db.query(Document).filter(Document.search_vector.isnot(None))
            
            # Apply filters
            if status_filter:
                base_query = base_query.filter(Document.status == status_filter)
            
            if type_filter:
                base_query = base_query.filter(Document.document_type == type_filter)
            
            # Convert query to tsquery format
            tsquery = func.plainto_tsquery('english', query)
            
            # Search with ranking
            search_query = base_query.filter(
                Document.search_vector.op('@@')(tsquery)
            ).order_by(
                func.ts_rank(Document.search_vector, tsquery).desc(),
                Document.created_at.desc()
            )
            
            # Get total count
            total = search_query.count()
            
            # Get paginated results
            documents = search_query.offset(offset).limit(limit).all()
            
            logger.info(f"Full-text search for '{query}': found {total} results")
            
            return documents, total
            
        except Exception as e:
            logger.error(f"Error in full-text search: {e}")
            return [], 0
    
    @staticmethod
    def semantic_search(
        db: Session,
        query: str,
        limit: int = 20,
        offset: int = 0,
        status_filter: Optional[DocumentStatus] = None,
        type_filter: Optional[DocumentType] = None,
        similarity_threshold: float = 0.3
    ) -> tuple[List[tuple[Document, float]], int]:
        """
        Perform semantic search using vector embeddings.
        
        Returns:
            Tuple of ([(document, similarity_score), ...], total_count)
        """
        try:
            # Generate query embedding
            query_embedding = embedding_service.generate_embedding(query)
            
            if not query_embedding:
                logger.warning("Failed to generate query embedding")
                return [], 0
            
            # Build base query
            base_query = db.query(Document).filter(Document.embedding.isnot(None))
            
            # Apply filters
            if status_filter:
                base_query = base_query.filter(Document.status == status_filter)
            
            if type_filter:
                base_query = base_query.filter(Document.document_type == type_filter)
            
            # Calculate cosine distance (lower is more similar)
            # We'll use <=> operator which is cosine distance
            distance = Document.embedding.cosine_distance(query_embedding)
            
            # Query with similarity ranking
            search_query = base_query.filter(
                distance < (1 - similarity_threshold)  # Convert similarity to distance
            ).order_by(distance)
            
            # Get total count
            total = search_query.count()
            
            # Get paginated results with scores
            results = []
            for doc in search_query.offset(offset).limit(limit).all():
                # Calculate similarity score (1 - distance)
                doc_embedding = doc.embedding
                if doc_embedding:
                    similarity = embedding_service.compute_similarity(query_embedding, doc_embedding)
                    results.append((doc, similarity))
            
            logger.info(f"Semantic search for '{query}': found {total} results")
            
            return results, total
            
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return [], 0
    
    @staticmethod
    def hybrid_search(
        db: Session,
        query: str,
        limit: int = 20,
        offset: int = 0,
        status_filter: Optional[DocumentStatus] = None,
        type_filter: Optional[DocumentType] = None,
        text_weight: float = 0.5,
        semantic_weight: float = 0.5
    ) -> tuple[List[tuple[Document, float]], int]:
        """
        Combine full-text and semantic search with weighted ranking.
        
        Args:
            text_weight: Weight for full-text search score (0-1)
            semantic_weight: Weight for semantic search score (0-1)
            
        Returns:
            Tuple of ([(document, combined_score), ...], total_count)
        """
        try:
            # Get full-text results
            text_docs, _ = SearchService.full_text_search(
                db, query, limit=100, status_filter=status_filter, type_filter=type_filter
            )
            
            # Get semantic results
            semantic_results, _ = SearchService.semantic_search(
                db, query, limit=100, status_filter=status_filter, type_filter=type_filter
            )
            
            # Combine and score
            doc_scores: Dict[int, float] = {}
            all_docs: Dict[int, Document] = {}
            
            # Add text search scores (normalized by rank)
            for i, doc in enumerate(text_docs):
                score = 1.0 - (i / max(len(text_docs), 1))  # Rank-based score
                doc_scores[doc.id] = score * text_weight
                all_docs[doc.id] = doc
            
            # Add semantic search scores
            for doc, similarity in semantic_results:
                current_score = doc_scores.get(doc.id, 0)
                doc_scores[doc.id] = current_score + (similarity * semantic_weight)
                all_docs[doc.id] = doc
            
            # Sort by combined score
            sorted_docs = sorted(
                doc_scores.items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            # Apply pagination
            total = len(sorted_docs)
            paginated = sorted_docs[offset:offset + limit]
            
            # Build result with scores
            results = [(all_docs[doc_id], score) for doc_id, score in paginated]
            
            logger.info(f"Hybrid search for '{query}': found {total} results")
            
            return results, total
            
        except Exception as e:
            logger.error(f"Error in hybrid search: {e}")
            return [], 0


# Singleton instance
search_service = SearchService()