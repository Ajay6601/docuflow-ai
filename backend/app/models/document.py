from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum, BigInteger, Text, Float, JSON
from sqlalchemy.sql import func
from app.database import Base
import enum


class DocumentStatus(str, enum.Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentType(str, enum.Enum):
    UNKNOWN = "unknown"
    INVOICE = "invoice"
    CONTRACT = "contract"
    RESUME = "resume"
    RECEIPT = "receipt"
    FORM = "form"
    LETTER = "letter"
    REPORT = "report"
    OTHER = "other"


class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    file_type = Column(String(100), nullable=False)
    storage_path = Column(String(500), nullable=False)
    
    status = Column(
        SQLEnum(DocumentStatus),
        default=DocumentStatus.UPLOADED,
        nullable=False,
        index=True
    )
    
    # Extraction fields
    extracted_text = Column(Text, nullable=True)
    page_count = Column(Integer, nullable=True)
    extraction_method = Column(String(50), nullable=True)
    extraction_error = Column(Text, nullable=True)
    
    # Task tracking
    task_id = Column(String(255), nullable=True, index=True)
    retry_count = Column(Integer, default=0)
    processing_time = Column(Float, nullable=True)
    
    # NEW - AI fields
    document_type = Column(
        SQLEnum(DocumentType),
        default=DocumentType.UNKNOWN,
        nullable=False,
        index=True
    )
    document_type_confidence = Column(Float, nullable=True)  # 0.0 to 1.0
    extracted_data = Column(JSON, nullable=True)  # Structured data as JSON
    summary = Column(Text, nullable=True)  # AI-generated summary
    ai_processing_cost = Column(Float, nullable=True)  # Cost in USD
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<Document(id={self.id}, filename={self.filename}, type={self.document_type}, status={self.status})>"