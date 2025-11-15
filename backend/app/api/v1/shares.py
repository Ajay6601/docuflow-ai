from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
import secrets
from app.database import get_db
from app.models.document import Document
from app.models.document_share import DocumentShare, SharePermission
from app.models.user import User
from app.schemas.share import ShareCreate, ShareResponse, ShareLinkResponse
from app.dependencies import get_current_user
from app.services.audit_service import audit_service
from app.models.audit_log import AuditAction

router = APIRouter()


@router.post("/", response_model=ShareResponse, status_code=status.HTTP_201_CREATED)
def create_share(
    share: ShareCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Share a document with another user or create a public link."""
    
    # Check if document exists and user owns it
    document = db.query(Document).filter(
        Document.id == share.document_id,
        Document.user_id == current_user.id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or you don't have permission"
        )
    
    # Check if sharing with specific user
    if share.shared_with_user_id:
        # Verify target user exists
        target_user = db.query(User).filter(User.id == share.shared_with_user_id).first()
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target user not found"
            )
        
        # Check if already shared with this user
        existing = db.query(DocumentShare).filter(
            DocumentShare.document_id == share.document_id,
            DocumentShare.shared_with_user_id == share.shared_with_user_id,
            DocumentShare.is_active == True
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document already shared with this user"
            )
        
        share_token = None
        is_public = False
    else:
        # Create public share link
        share_token = secrets.token_urlsafe(32)
        is_public = True
    
    # Calculate expiry
    expires_at = None
    if share.expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=share.expires_in_days)
    
    # Create share
    db_share = DocumentShare(
        document_id=share.document_id,
        owner_id=current_user.id,
        shared_with_user_id=share.shared_with_user_id,
        share_token=share_token,
        is_public=is_public,
        permission=share.permission,
        expires_at=expires_at
    )
    
    db.add(db_share)
    db.commit()
    db.refresh(db_share)
    
    # Audit log
    audit_service.log(
        db=db,
        action=AuditAction.DOCUMENT_SHARE,
        user=current_user,
        resource_type="document",
        resource_id=document.id,
        description=f"Shared document with {'public link' if is_public else f'user {share.shared_with_user_id}'}",
        metadata={
            "permission": share.permission.value,
            "is_public": is_public
        },
        request=request
    )
    
    return db_share


@router.get("/document/{document_id}", response_model=list[ShareResponse])
def list_document_shares(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all shares for a document (owner only)."""
    
    # Check ownership
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or you don't have permission"
        )
    
    shares = db.query(DocumentShare).filter(
        DocumentShare.document_id == document_id,
        DocumentShare.is_active == True
    ).all()
    
    return shares


@router.get("/shared-with-me", response_model=list[ShareResponse])
def list_shared_with_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all documents shared with the current user."""
    
    shares = db.query(DocumentShare).filter(
        DocumentShare.shared_with_user_id == current_user.id,
        DocumentShare.is_active == True
    ).all()
    
    return shares


@router.get("/{share_id}", response_model=ShareResponse)
def get_share(
    share_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get share details."""
    
    share = db.query(DocumentShare).filter(DocumentShare.id == share_id).first()
    
    if not share:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Share not found"
        )
    
    # Check if user is owner or recipient
    if share.owner_id != current_user.id and share.shared_with_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this share"
        )
    
    return share


@router.delete("/{share_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_share(
    share_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Revoke a share (owner only)."""
    
    share = db.query(DocumentShare).filter(DocumentShare.id == share_id).first()
    
    if not share:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Share not found"
        )
    
    # Check ownership
    if share.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the owner can revoke shares"
        )
    
    # Deactivate share
    share.is_active = False
    db.commit()
    
    # Audit log
    audit_service.log(
        db=db,
        action=AuditAction.DOCUMENT_SHARE,
        user=current_user,
        resource_type="document_share",
        resource_id=share_id,
        description="Revoked document share",
        request=request
    )
    
    return None


@router.get("/link/{share_token}")
def access_shared_document(
    share_token: str,
    db: Session = Depends(get_db)
):
    """Access a document via public share link (no auth required)."""
    
    share = db.query(DocumentShare).filter(
        DocumentShare.share_token == share_token,
        DocumentShare.is_active == True,
        DocumentShare.is_public == True
    ).first()
    
    if not share:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or expired share link"
        )
    
    # Check if expired
    if share.is_expired():
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="This share link has expired"
        )
    
    # Get document
    document = db.query(Document).filter(Document.id == share.document_id).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return {
        "document_id": document.id,
        "filename": document.original_filename,
        "file_type": document.file_type,
        "file_size": document.file_size,
        "permission": share.permission.value,
        "summary": document.summary if share.permission in [SharePermission.VIEW, SharePermission.EDIT] else None
    }