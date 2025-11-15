from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from app.database import get_db
from app.models.document import DocumentStatus, DocumentType, Document
from app.services.search_service import search_service
from app.dependencies import get_current_user
from app.models.user import User
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class SearchResult(BaseModel):
    id: int
    filename: str
    original_filename: str
    document_type: str
    status: str
    summary: Optional[str]
    created_at: str
    score: Optional[float] = None
    
    class Config:
        from_attributes = True


class SearchResponse(BaseModel):
    query: str
    total: int
    results: List[SearchResult]
    search_type: str
    page: int
    page_size: int


@router.get("/full-text", response_model=SearchResponse)
def search_full_text(
    q: str = Query(..., description="Search query"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status: Optional[DocumentStatus] = None,
    doc_type: Optional[DocumentType] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Full-text search using PostgreSQL tsvector.
    Best for: exact keyword matching, document titles, specific terms.
    """
    offset = (page - 1) * page_size
    
    documents, total = search_service.full_text_search(
        db=db,
        query=q,
        limit=page_size,
        offset=offset,
        status_filter=status,
        type_filter=doc_type
    )
    
    # Filter by user
    documents = [doc for doc in documents if doc.user_id == current_user.id]
    total = len(documents)
    
    results = [
        SearchResult(
            id=doc.id,
            filename=doc.filename,
            original_filename=doc.original_filename,
            document_type=doc.document_type.value,
            status=doc.status.value,
            summary=doc.summary,
            created_at=doc.created_at.isoformat(),
            score=None
        )
        for doc in documents
    ]
    
    return SearchResponse(
        query=q,
        total=total,
        results=results,
        search_type="full_text",
        page=page,
        page_size=page_size
    )


@router.get("/semantic", response_model=SearchResponse)
def search_semantic(
    q: str = Query(..., description="Search query"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status: Optional[DocumentStatus] = None,
    doc_type: Optional[DocumentType] = None,
    similarity_threshold: float = Query(0.3, ge=0.0, le=1.0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Semantic search using AI embeddings.
    Best for: conceptual searches, meaning-based queries, natural language.
    """
    offset = (page - 1) * page_size
    
    results_with_scores, total = search_service.semantic_search(
        db=db,
        query=q,
        limit=page_size,
        offset=offset,
        status_filter=status,
        type_filter=doc_type,
        similarity_threshold=similarity_threshold
    )
    
    # Filter by user
    results_with_scores = [(doc, score) for doc, score in results_with_scores if doc.user_id == current_user.id]
    total = len(results_with_scores)
    
    results = [
        SearchResult(
            id=doc.id,
            filename=doc.filename,
            original_filename=doc.original_filename,
            document_type=doc.document_type.value,
            status=doc.status.value,
            summary=doc.summary,
            created_at=doc.created_at.isoformat(),
            score=round(score, 4)
        )
        for doc, score in results_with_scores
    ]
    
    return SearchResponse(
        query=q,
        total=total,
        results=results,
        search_type="semantic",
        page=page,
        page_size=page_size
    )


@router.get("/hybrid", response_model=SearchResponse)
def search_hybrid(
    q: str = Query(..., description="Search query"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status: Optional[DocumentStatus] = None,
    doc_type: Optional[DocumentType] = None,
    text_weight: float = Query(0.5, ge=0.0, le=1.0),
    semantic_weight: float = Query(0.5, ge=0.0, le=1.0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Hybrid search combining full-text and semantic search.
    Best for: most accurate results, balanced keyword and meaning search.
    """
    offset = (page - 1) * page_size
    
    results_with_scores, total = search_service.hybrid_search(
        db=db,
        query=q,
        limit=page_size,
        offset=offset,
        status_filter=status,
        type_filter=doc_type,
        text_weight=text_weight,
        semantic_weight=semantic_weight
    )
    
    # Filter by user
    results_with_scores = [(doc, score) for doc, score in results_with_scores if doc.user_id == current_user.id]
    total = len(results_with_scores)
    
    results = [
        SearchResult(
            id=doc.id,
            filename=doc.filename,
            original_filename=doc.original_filename,
            document_type=doc.document_type.value,
            status=doc.status.value,
            summary=doc.summary,
            created_at=doc.created_at.isoformat(),
            score=round(score, 4)
        )
        for doc, score in results_with_scores
    ]
    
    return SearchResponse(
        query=q,
        total=total,
        results=results,
        search_type="hybrid",
        page=page,
        page_size=page_size
    )