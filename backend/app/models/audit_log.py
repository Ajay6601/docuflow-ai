from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Text
from sqlalchemy.sql import func
from app.database import Base
import enum


class AuditAction(str, enum.Enum):
    # Authentication
    LOGIN = "login"
    LOGOUT = "logout"
    REGISTER = "register"
    LOGIN_FAILED = "login_failed"
    
    # Documents
    DOCUMENT_UPLOAD = "document_upload"
    DOCUMENT_VIEW = "document_view"
    DOCUMENT_DOWNLOAD = "document_download"
    DOCUMENT_DELETE = "document_delete"
    DOCUMENT_SHARE = "document_share"
    DOCUMENT_REPROCESS = "document_reprocess"
    
    # Search
    SEARCH_PERFORMED = "search_performed"
    
    # System
    API_KEY_CREATED = "api_key_created"
    API_KEY_REVOKED = "api_key_revoked"
    SETTINGS_CHANGED = "settings_changed"


class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Who performed the action
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True, index=True)
    username = Column(String(100), nullable=True)
    
    # What action was performed
    action = Column(String(50), nullable=False, index=True)
    resource_type = Column(String(50), nullable=True)
    resource_id = Column(Integer, nullable=True)
    
    # Details
    description = Column(Text, nullable=True)
    details = Column(JSON, nullable=True)  # CHANGED from 'metadata' to 'details'
    
    # Request info
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    request_method = Column(String(10), nullable=True)
    request_path = Column(String(500), nullable=True)
    
    # Status
    status = Column(String(20), nullable=False, default="success")
    error_message = Column(Text, nullable=True)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, user={self.username}, action={self.action})>"