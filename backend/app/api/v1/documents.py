from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from io import BytesIO
import logging
from typing import List, Optional
from app.database import get_db
from app.models.document import Document, DocumentStatus
from app.schemas.document import DocumentResponse, DocumentList, ExtractionResult
from app.services.storage import storage_service
from app.services.extraction import extraction_service
from app.utils.file_utils import (
    generate_unique_filename,
    generate_storage_path,
    detect_file_type,
    validate_file_size,
    validate_file_type,
    format_file_size
)
from app.config import settings
from app.tasks.extraction_tasks import process_document

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    process_async: bool = Form(default=True),
    db: Session = Depends(get_db)
):
    """
    Upload a document file.
    
    - process_async=True: Process in background (recommended for large files)
    - process_async=False: Process immediately (blocks until complete)
    """
    try:
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
        
        # Validate file size
        if not validate_file_size(file_size):
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size is {format_file_size(settings.MAX_FILE_SIZE)}"
            )
        
        # Detect actual file type
        detected_mime_type = detect_file_type(file_content, file.filename)
        
        # Validate file type
        if not validate_file_type(detected_mime_type):
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"File type '{detected_mime_type}' not supported."
            )
        
        # Generate unique filename and storage path
        unique_filename = generate_unique_filename(file.filename)
        storage_path = generate_storage_path(unique_filename)
        
        # Upload to MinIO
        storage_service.upload_file(
            file_data=file_content,
            object_name=storage_path,
            content_type=detected_mime_type,
            metadata={
                "original_filename": file.filename,
                "uploaded_by": "system"
            }
        )
        
        # Create document record
        db_document = Document(
            filename=unique_filename,
            original_filename=file.filename,
            file_size=file_size,
            file_type=detected_mime_type,
            storage_path=storage_path,
            status=DocumentStatus.UPLOADED
        )
        
        db.add(db_document)
        db.commit()
        db.refresh(db_document)
        
        logger.info(f"Document uploaded successfully: {db_document.id} - {file.filename}")
        
        # Process extraction
        if process_async:
            # # Queue background task
            # task = process_document.delay(db_document.id)
            # db_document.task_id = task.id
            # db_document.status = DocumentStatus.PROCESSING
            # db.commit()
            # db.refresh(db_document)
            
            # logger.info(f"Queued extraction task {task.id} for document {db_document.id}")
            try:
                logger.info(f"About to queue task for document {db_document.id}")
                task = process_document.delay(db_document.id, use_ai=True)
                logger.info(f"Task queued successfully: {task.id}")
                
                db_document.task_id = task.id
                db_document.status = DocumentStatus.PROCESSING
                db.commit()
                db.refresh(db_document)
                
                logger.info(f"Document {db_document.id} updated with task_id {task.id}")
            except Exception as e:
                logger.error(f"Error queuing task: {e}")
                raise
        else:
            # Process immediately (synchronous)
            try:
                db_document.status = DocumentStatus.PROCESSING
                db.commit()
                
                extracted_text, page_count, method, error = extraction_service.extract_text(
                    file_content, detected_mime_type
                )
                
                if error:
                    db_document.status = DocumentStatus.FAILED
                    db_document.extraction_error = error
                else:
                    db_document.status = DocumentStatus.COMPLETED
                    db_document.extracted_text = extracted_text
                    db_document.page_count = page_count
                    db_document.extraction_method = method
                
                db.commit()
                db.refresh(db_document)
                
            except Exception as e:
                logger.error(f"Error during immediate extraction: {e}")
                db_document.status = DocumentStatus.FAILED
                db_document.extraction_error = str(e)
                db.commit()
        
        db.refresh(db_document)
        return db_document
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload document: {str(e)}"
        )

@router.post("/upload/batch", response_model=List[DocumentResponse], status_code=status.HTTP_201_CREATED)
async def upload_documents_batch(
    files: List[UploadFile] = File(..., description="Multiple files to upload"),
    process_async: bool = Form(default=True),
    db: Session = Depends(get_db)
):
    """
    Upload multiple documents at once.
    
    - Supports up to 10 files per request
    - Each file is validated independently
    - Returns list of created documents
    - Failed uploads are skipped with error logged
    """
    if len(files) > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 10 files allowed per batch upload"
        )
    
    uploaded_documents = []
    errors = []
    
    for idx, file in enumerate(files):
        try:
            # Read file content
            file_content = await file.read()
            file_size = len(file_content)
            
            # Validate file size
            if not validate_file_size(file_size):
                errors.append({
                    "filename": file.filename,
                    "error": f"File too large. Maximum size is {format_file_size(settings.MAX_FILE_SIZE)}"
                })
                continue
            
            # Detect actual file type
            detected_mime_type = detect_file_type(file_content, file.filename)
            
            # Validate file type
            if not validate_file_type(detected_mime_type):
                errors.append({
                    "filename": file.filename,
                    "error": f"File type '{detected_mime_type}' not supported"
                })
                continue
            
            # Generate unique filename and storage path
            unique_filename = generate_unique_filename(file.filename)
            storage_path = generate_storage_path(unique_filename)
            
            # Upload to MinIO
            storage_service.upload_file(
                file_data=file_content,
                object_name=storage_path,
                content_type=detected_mime_type,
                metadata={
                    "original_filename": file.filename,
                    "uploaded_by": "system",
                    "batch_upload": "true",
                    "batch_index": str(idx)
                }
            )
            
            # Create document record
            db_document = Document(
                filename=unique_filename,
                original_filename=file.filename,
                file_size=file_size,
                file_type=detected_mime_type,
                storage_path=storage_path,
                status=DocumentStatus.UPLOADED
            )
            
            db.add(db_document)
            db.commit()
            db.refresh(db_document)
            
            logger.info(f"Document uploaded in batch: {db_document.id} - {file.filename}")
            
            # Process extraction
            if process_async:
                # Queue background task
                task = process_document.delay(db_document.id, use_ai=True)
                db_document.task_id = task.id
                db_document.status = DocumentStatus.PROCESSING
                db.commit()
                db.refresh(db_document)
                
                logger.info(f"Queued extraction task {task.id} for document {db_document.id}")
            
            uploaded_documents.append(db_document)
            
        except Exception as e:
            logger.error(f"Error uploading file {file.filename}: {e}")
            errors.append({
                "filename": file.filename,
                "error": str(e)
            })
            continue
    
    # Log summary
    logger.info(
        f"Batch upload completed: {len(uploaded_documents)} successful, {len(errors)} failed"
    )
    
    # If there were errors, log them but still return successful uploads
    if errors:
        logger.warning(f"Batch upload errors: {errors}")
    
    if not uploaded_documents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"All files failed to upload. Errors: {errors}"
        )
    
    return uploaded_documents



@router.post("/process/batch")
def process_documents_batch(
    document_ids: List[int],
    use_ai: bool = True,
    db: Session = Depends(get_db)
):
    """
    Queue multiple documents for reprocessing in batch.
    
    - Maximum 20 documents per batch
    - All documents are queued for background processing
    - Returns list of task IDs
    """
    if len(document_ids) > 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 20 documents allowed per batch"
        )
    
    results = []
    not_found = []
    
    for doc_id in document_ids:
        document = db.query(Document).filter(Document.id == doc_id).first()
        
        if not document:
            not_found.append(doc_id)
            continue
        
        # Queue background task
        task = process_document.delay(document.id, use_ai)
        document.task_id = task.id
        document.status = DocumentStatus.PROCESSING
        document.retry_count = 0
        document.extraction_error = None
        
        db.commit()
        
        results.append({
            "document_id": doc_id,
            "task_id": task.id,
            "status": "queued"
        })
        
        logger.info(f"Queued reprocessing task {task.id} for document {doc_id}")
    
    if not_found:
        logger.warning(f"Documents not found in batch: {not_found}")
    
    return {
        "total_requested": len(document_ids),
        "queued": len(results),
        "not_found": not_found,
        "results": results
    }


@router.post("/status/batch")
def get_documents_status_batch(
    document_ids: List[int],
    db: Session = Depends(get_db)
):
    """
    Get processing status for multiple documents at once.
    
    Useful for checking progress of batch uploads.
    """
    if len(document_ids) > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 50 documents allowed per batch status check"
        )
    
    results = []
    
    for doc_id in document_ids:
        document = db.query(Document).filter(Document.id == doc_id).first()
        
        if document:
            results.append({
                "document_id": document.id,
                "filename": document.original_filename,
                "status": document.status.value,
                "document_type": document.document_type.value if document.document_type else None,
                "task_id": document.task_id,
                "retry_count": document.retry_count,
                "processing_time": document.processing_time,
                "error": document.extraction_error
            })
        else:
            results.append({
                "document_id": doc_id,
                "status": "not_found",
                "error": "Document not found"
            })
    
    # Calculate summary statistics
    status_counts = {}
    for result in results:
        status = result.get("status", "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1
    
    return {
        "total": len(document_ids),
        "summary": status_counts,
        "documents": results
    }



@router.post("/{document_id}/process", response_model=DocumentResponse)
def reprocess_document(
    document_id: int,
    db: Session = Depends(get_db)
):
    """
    Queue a document for reprocessing.
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with id {document_id} not found"
        )
    
    # Queue background task
    task = process_document.delay(document.id)
    document.task_id = task.id
    document.status = DocumentStatus.PROCESSING
    document.retry_count = 0
    document.extraction_error = None
    
    db.commit()
    db.refresh(document)
    
    logger.info(f"Queued reprocessing task {task.id} for document {document_id}")
    
    return document


@router.get("/{document_id}/status")
def get_document_status(
    document_id: int,
    db: Session = Depends(get_db)
):
    """
    Get the current processing status of a document.
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with id {document_id} not found"
        )
    
    return {
        "document_id": document.id,
        "status": document.status,
        "task_id": document.task_id,
        "retry_count": document.retry_count,
        "processing_time": document.processing_time,
        "extraction_method": document.extraction_method,
        "error": document.extraction_error
    }


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: int,
    db: Session = Depends(get_db)
):
    """Get document metadata by ID."""
    document = db.query(Document).filter(Document.id == document_id).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with id {document_id} not found"
        )
    
    return document


@router.get("/{document_id}/download")
def download_document(
    document_id: int,
    db: Session = Depends(get_db)
):
    """Download the actual document file."""
    document = db.query(Document).filter(Document.id == document_id).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with id {document_id} not found"
        )
    
    try:
        file_data = storage_service.download_file(document.storage_path)
        
        return StreamingResponse(
            BytesIO(file_data),
            media_type=document.file_type,
            headers={
                "Content-Disposition": f'attachment; filename="{document.original_filename}"'
            }
        )
        
    except Exception as e:
        logger.error(f"Error downloading document {document_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download document"
        )


@router.get("/", response_model=DocumentList)
def list_documents(
    page: int = 1,
    page_size: int = 10,
    status_filter: Optional[str] = None,  # Changed from DocumentStatus to str
    doc_type: Optional[str] = None,  # Changed from DocumentType to str
    db: Session = Depends(get_db)
):
    """List all documents with pagination and optional status filter."""
    if page < 1:
        page = 1
    if page_size < 1 or page_size > 100:
        page_size = 10
    
    offset = (page - 1) * page_size
    
    query = db.query(Document)
    
    if status_filter:
        query = query.filter(Document.status == status_filter)
    
    if doc_type:
        query = query.filter(Document.document_type == doc_type)
    
    total = query.count()
    
    documents = query\
        .order_by(Document.created_at.desc())\
        .offset(offset)\
        .limit(page_size)\
        .all()
    
    return {
        "total": total,
        "items": documents,
        "page": page,
        "page_size": page_size
    }

@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db)
):
    """Delete a document (both file and metadata)."""
    document = db.query(Document).filter(Document.id == document_id).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with id {document_id} not found"
        )
    
    try:
        storage_service.delete_file(document.storage_path)
        db.delete(document)
        db.commit()
        
        logger.info(f"Document deleted successfully: {document_id}")
        return None
        
    except Exception as e:
        logger.error(f"Error deleting document {document_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document"
        )