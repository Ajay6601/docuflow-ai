from sqlalchemy.orm import Session
from fastapi import Request
from app.models.audit_log import AuditLog, AuditAction
from app.models.user import User
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class AuditService:
    """Service for creating audit log entries."""
    
    @staticmethod
    def log(
        db: Session,
        action: AuditAction,
        user: Optional[User] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[int] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None,
        status: str = "success",
        error_message: Optional[str] = None
    ):
        """Create an audit log entry."""
        try:
            # Extract request info
            ip_address = None
            user_agent = None
            request_method = None
            request_path = None
            
            if request:
                ip_address = request.client.host if request.client else None
                user_agent = request.headers.get("user-agent")
                request_method = request.method
                request_path = str(request.url.path)
            
            # Create audit log
            audit_log = AuditLog(
                user_id=user.id if user else None,
                username=user.username if user else None,
                action=action.value,
                resource_type=resource_type,
                resource_id=resource_id,
                description=description,
                metadata=metadata,
                ip_address=ip_address,
                user_agent=user_agent,
                request_method=request_method,
                request_path=request_path,
                status=status,
                error_message=error_message
            )
            
            db.add(audit_log)
            db.commit()
            
            logger.debug(f"Audit log created: {action.value} by {user.username if user else 'anonymous'}")
            
        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")
            db.rollback()


# Singleton instance
audit_service = AuditService()