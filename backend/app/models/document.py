from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum, BigInteger, Text, Float, JSON, Index, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
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
    
    # NEW - User ownership
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True, index=True)
    
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
    
    # AI fields
    document_type = Column(
        SQLEnum(DocumentType),
        default=DocumentType.UNKNOWN,
        nullable=False,
        index=True
    )
    document_type_confidence = Column(Float, nullable=True)
    extracted_data = Column(JSON, nullable=True)
    summary = Column(Text, nullable=True)
    ai_processing_cost = Column(Float, nullable=True)
    
    # Search fields
    search_vector = Column(TSVECTOR, nullable=True)
    embedding = Column(Vector(384), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('ix_documents_search_vector', 'search_vector', postgresql_using='gin'),
        Index('ix_documents_embedding', 'embedding', postgresql_using='ivfflat', postgresql_ops={'embedding': 'vector_cosine_ops'}),
    )
    
    def __repr__(self):
        return f"<Document(id={self.id}, filename={self.filename}, type={self.document_type}, status={self.status})>"