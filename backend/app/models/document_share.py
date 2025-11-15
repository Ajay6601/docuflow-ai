from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum
from datetime import datetime


class SharePermission(str, enum.Enum):
    VIEW = "view"
    DOWNLOAD = "download"
    EDIT = "edit"


class DocumentShare(Base):
    __tablename__ = "document_shares"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Document being shared
    document_id = Column(Integer, ForeignKey('documents.id'), nullable=False, index=True)
    
    # Owner (who shared it)
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    
    # Shared with (recipient)
    shared_with_user_id = Column(Integer, ForeignKey('users.id'), nullable=True, index=True)
    
    # Public link sharing
    share_token = Column(String(100), unique=True, nullable=True, index=True)  # For public links
    is_public = Column(Boolean, default=False, nullable=False)
    
    # Permissions
    permission = Column(
        SQLEnum(SharePermission),
        default=SharePermission.VIEW,
        nullable=False
    )
    
    # Expiry
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def is_expired(self) -> bool:
        """Check if share has expired."""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at.replace(tzinfo=None)
    
    def __repr__(self):
        return f"<DocumentShare(id={self.id}, document={self.document_id}, permission={self.permission})>"