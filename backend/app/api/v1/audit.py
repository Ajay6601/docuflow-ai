from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
from app.database import get_db
from app.models.audit_log import AuditLog
from app.models.user import User, UserRole
from app.dependencies import get_current_user, require_role
from pydantic import BaseModel

router = APIRouter()


class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int]
    username: Optional[str]
    action: str
    resource_type: Optional[str]
    resource_id: Optional[int]
    description: Optional[str]
    ip_address: Optional[str]
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class AuditLogList(BaseModel):
    total: int
    items: list[AuditLogResponse]
    page: int
    page_size: int


@router.get("/", response_model=AuditLogList)
def list_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    action: Optional[str] = None,
    user_id: Optional[int] = None,
    days: int = Query(7, ge=1, le=90),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List audit logs.
    - Regular users can only see their own logs
    - Admins can see all logs
    """
    offset = (page - 1) * page_size
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Base query
    query = db.query(AuditLog).filter(AuditLog.created_at >= start_date)
    
    # Filter by user (non-admins can only see their own logs)
    if current_user.role != UserRole.ADMIN:
        query = query.filter(AuditLog.user_id == current_user.id)
    elif user_id:
        query = query.filter(AuditLog.user_id == user_id)
    
    # Filter by action
    if action:
        query = query.filter(AuditLog.action == action)
    
    # Get total and paginated results
    total = query.count()
    logs = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(page_size).all()
    
    return {
        "total": total,
        "items": logs,
        "page": page,
        "page_size": page_size
    }


@router.get("/actions")
def get_audit_actions(current_user: User = Depends(get_current_user)):
    """Get list of all audit action types."""
    from app.models.audit_log import AuditAction
    return [action.value for action in AuditAction]


@router.get("/stats")
def get_audit_stats(
    days: int = Query(7, ge=1, le=90),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Get audit log statistics (admin only)."""
    from sqlalchemy import func
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Total actions
    total_actions = db.query(AuditLog).filter(AuditLog.created_at >= start_date).count()
    
    # Actions by type
    actions_by_type = db.query(
        AuditLog.action,
        func.count(AuditLog.id).label('count')
    ).filter(
        AuditLog.created_at >= start_date
    ).group_by(AuditLog.action).all()
    
    # Failed actions
    failed_actions = db.query(AuditLog).filter(
        AuditLog.created_at >= start_date,
        AuditLog.status == "failed"
    ).count()
    
    # Most active users
    active_users = db.query(
        AuditLog.username,
        func.count(AuditLog.id).label('count')
    ).filter(
        AuditLog.created_at >= start_date,
        AuditLog.username.isnot(None)
    ).group_by(AuditLog.username).order_by(func.count(AuditLog.id).desc()).limit(10).all()
    
    return {
        "total_actions": total_actions,
        "failed_actions": failed_actions,
        "actions_by_type": [{"action": action, "count": count} for action, count in actions_by_type],
        "most_active_users": [{"username": username, "count": count} for username, count in active_users]
    }