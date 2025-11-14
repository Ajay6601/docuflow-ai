from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional, Dict, Any
from app.models.document import DocumentStatus, DocumentType


class DocumentBase(BaseModel):
    filename: str
    file_size: int
    file_type: str


class DocumentCreate(DocumentBase):
    original_filename: str
    storage_path: str


class DocumentResponse(DocumentBase):
    id: int
    original_filename: str
    storage_path: str
    status: DocumentStatus
    
    # Extraction fields
    extracted_text: Optional[str] = None
    page_count: Optional[int] = None
    extraction_method: Optional[str] = None
    extraction_error: Optional[str] = None
    
    # Task tracking fields
    task_id: Optional[str] = None
    retry_count: int = 0
    processing_time: Optional[float] = None
    
    # NEW - AI fields
    document_type: DocumentType = DocumentType.UNKNOWN
    document_type_confidence: Optional[float] = None
    extracted_data: Optional[Dict[str, Any]] = None
    summary: Optional[str] = None
    ai_processing_cost: Optional[float] = None
    
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DocumentList(BaseModel):
    total: int
    items: List[DocumentResponse]
    page: int
    page_size: int


class ExtractionResult(BaseModel):
    document_id: int
    extracted_text: str
    page_count: Optional[int] = None
    extraction_method: str
    status: DocumentStatus
    document_type: Optional[DocumentType] = None
    summary: Optional[str] = None