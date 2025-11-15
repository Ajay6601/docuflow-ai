from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.models.document_share import SharePermission


class ShareCreate(BaseModel):
    document_id: int
    shared_with_user_id: Optional[int] = None  # None for public links
    permission: SharePermission = SharePermission.VIEW
    expires_in_days: Optional[int] = None  # Expiry in days


class ShareResponse(BaseModel):
    id: int
    document_id: int
    owner_id: int
    shared_with_user_id: Optional[int]
    share_token: Optional[str]
    is_public: bool
    permission: SharePermission
    expires_at: Optional[datetime]
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class ShareLinkResponse(BaseModel):
    share_id: int
    share_url: str
    permission: str
    expires_at: Optional[datetime]