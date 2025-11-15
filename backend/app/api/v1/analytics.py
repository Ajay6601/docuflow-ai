from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import datetime, timedelta
from typing import Optional
from app.database import get_db
from app.models.document import Document, DocumentStatus, DocumentType
from app.models.user import User
from app.dependencies import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/overview")
def get_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get overview statistics for the current user."""
    
    # Base query filtered by user
    base_query = db.query(Document).filter(Document.user_id == current_user.id)
    
    # Total documents
    total_documents = base_query.count()
    
    # Documents by status
    status_counts = {
        "uploaded": base_query.filter(Document.status == DocumentStatus.UPLOADED).count(),
        "processing": base_query.filter(Document.status == DocumentStatus.PROCESSING).count(),
        "completed": base_query.filter(Document.status == DocumentStatus.COMPLETED).count(),
        "failed": base_query.filter(Document.status == DocumentStatus.FAILED).count(),
    }
    
    # Documents uploaded today
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    uploaded_today = base_query.filter(Document.created_at >= today_start).count()
    
    # Documents uploaded this week
    week_start = today_start - timedelta(days=today_start.weekday())
    uploaded_this_week = base_query.filter(Document.created_at >= week_start).count()
    
    # Documents uploaded this month
    month_start = today_start.replace(day=1)
    uploaded_this_month = base_query.filter(Document.created_at >= month_start).count()
    
    # Average processing time (completed documents only)
    avg_processing_time = db.query(func.avg(Document.processing_time)).filter(
        Document.user_id == current_user.id,
        Document.status == DocumentStatus.COMPLETED,
        Document.processing_time.isnot(None)
    ).scalar() or 0
    
    # Total AI cost
    total_ai_cost = db.query(func.sum(Document.ai_processing_cost)).filter(
        Document.user_id == current_user.id,
        Document.ai_processing_cost.isnot(None)
    ).scalar() or 0
    
    # Total storage (bytes)
    total_storage = db.query(func.sum(Document.file_size)).filter(
        Document.user_id == current_user.id
    ).scalar() or 0
    
    return {
        "total_documents": total_documents,
        "status_counts": status_counts,
        "uploaded_today": uploaded_today,
        "uploaded_this_week": uploaded_this_week,
        "uploaded_this_month": uploaded_this_month,
        "average_processing_time": round(avg_processing_time, 2),
        "total_ai_cost": round(total_ai_cost, 4),
        "total_storage_bytes": total_storage,
    }


@router.get("/document-types")
def get_document_types(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get document count by type."""
    
    results = db.query(
        Document.document_type,
        func.count(Document.id).label('count')
    ).filter(
        Document.user_id == current_user.id
    ).group_by(
        Document.document_type
    ).all()
    
    return [
        {"type": doc_type.value, "count": count}
        for doc_type, count in results
    ]


@router.get("/upload-timeline")
def get_upload_timeline(
    days: int = Query(7, ge=1, le=90),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get document upload timeline."""
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    results = db.query(
        func.date(Document.created_at).label('date'),
        func.count(Document.id).label('count')
    ).filter(
        Document.user_id == current_user.id,
        Document.created_at >= start_date
    ).group_by(
        func.date(Document.created_at)
    ).order_by(
        func.date(Document.created_at)
    ).all()
    
    return [
        {"date": str(date), "count": count}
        for date, count in results
    ]


@router.get("/processing-stats")
def get_processing_stats(
    days: int = Query(7, ge=1, le=90),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get processing statistics over time."""
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Average processing time by day
    results = db.query(
        func.date(Document.created_at).label('date'),
        func.avg(Document.processing_time).label('avg_time'),
        func.count(Document.id).label('count')
    ).filter(
        Document.user_id == current_user.id,
        Document.status == DocumentStatus.COMPLETED,
        Document.processing_time.isnot(None),
        Document.created_at >= start_date
    ).group_by(
        func.date(Document.created_at)
    ).order_by(
        func.date(Document.created_at)
    ).all()
    
    return [
        {
            "date": str(date),
            "avg_processing_time": round(avg_time, 2),
            "document_count": count
        }
        for date, avg_time, count in results
    ]


@router.get("/cost-tracking")
def get_cost_tracking(
    days: int = Query(30, ge=1, le=90),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get AI cost tracking over time."""
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Daily AI costs
    results = db.query(
        func.date(Document.created_at).label('date'),
        func.sum(Document.ai_processing_cost).label('total_cost'),
        func.count(Document.id).label('count')
    ).filter(
        Document.user_id == current_user.id,
        Document.ai_processing_cost.isnot(None),
        Document.created_at >= start_date
    ).group_by(
        func.date(Document.created_at)
    ).order_by(
        func.date(Document.created_at)
    ).all()
    
    return [
        {
            "date": str(date),
            "cost": round(total_cost, 4),
            "document_count": count
        }
        for date, total_cost, count in results
    ]


@router.get("/extraction-methods")
def get_extraction_methods(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get document count by extraction method."""
    
    results = db.query(
        Document.extraction_method,
        func.count(Document.id).label('count')
    ).filter(
        Document.user_id == current_user.id,
        Document.extraction_method.isnot(None)
    ).group_by(
        Document.extraction_method
    ).all()
    
    return [
        {"method": method or "unknown", "count": count}
        for method, count in results
    ]


@router.get("/recent-activity")
def get_recent_activity(
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get recent document activity."""
    
    documents = db.query(Document).filter(
        Document.user_id == current_user.id
    ).order_by(
        Document.updated_at.desc()
    ).limit(limit).all()
    
    return [
        {
            "id": doc.id,
            "filename": doc.original_filename,
            "status": doc.status.value,
            "document_type": doc.document_type.value,
            "created_at": doc.created_at.isoformat(),
            "updated_at": doc.updated_at.isoformat(),
        }
        for doc in documents
    ]