from celery import Task
from app.celery_app import celery_app
from app.database import SessionLocal
from app.models.document import Document, DocumentStatus
from app.services.storage import storage_service
from app.services.extraction import extraction_service
from app.services.ai_service import ai_service
import logging
import time

logger = logging.getLogger(__name__)


class DatabaseTask(Task):
    """Base task with database session handling."""
    
    def after_return(self, *args, **kwargs):
        """Clean up after task completion."""
        pass


@celery_app.task(bind=True, base=DatabaseTask, name='app.tasks.extraction_tasks.process_document')
def process_document(self, document_id: int, use_ai: bool = True):
    """
    Background task to extract text and process with AI.
    
    Args:
        document_id: ID of the document to process
        use_ai: Whether to use AI for classification and extraction
    """
    db = SessionLocal()
    start_time = time.time()
    
    try:
        # Get document
        document = db.query(Document).filter(Document.id == document_id).first()
        
        if not document:
            logger.error(f"Document {document_id} not found")
            return {"status": "error", "message": "Document not found"}
        
        # Update status to processing
        document.status = DocumentStatus.PROCESSING
        document.task_id = self.request.id
        db.commit()
        
        logger.info(f"Starting processing for document {document_id} (task: {self.request.id})")
        
        # Download file from storage
        file_data = storage_service.download_file(document.storage_path)
        
        # Step 1: Extract text
        extracted_text, page_count, method, error = extraction_service.extract_text(
            file_data, document.file_type
        )
        
        if error:
            # Extraction failed
            document.status = DocumentStatus.FAILED
            document.extraction_error = error
            document.processing_time = time.time() - start_time
            db.commit()
            
            logger.error(f"Extraction failed for document {document_id}: {error}")
            raise Exception(f"Extraction failed: {error}")
        
        # Save extracted text
        document.extracted_text = extracted_text
        document.page_count = page_count
        document.extraction_method = method
        db.commit()
        
        logger.info(f"Text extraction completed for document {document_id}")
        
        # Step 2: AI Processing (if enabled and text available)
        if use_ai and extracted_text and len(extracted_text.strip()) > 50:
            logger.info(f"Starting AI processing for document {document_id}")
            
            try:
                ai_result = ai_service.process_document_with_ai(extracted_text)
                
                document.document_type = ai_result["document_type"]
                document.document_type_confidence = ai_result["document_type_confidence"]
                document.extracted_data = ai_result["extracted_data"]
                document.summary = ai_result["summary"]
                document.ai_processing_cost = ai_result["ai_processing_cost"]
                
                logger.info(
                    f"AI processing completed for document {document_id}: "
                    f"type={ai_result['document_type']}, "
                    f"confidence={ai_result['document_type_confidence']}, "
                    f"cost=${ai_result['ai_processing_cost']:.4f}"
                )
                
            except Exception as ai_error:
                logger.error(f"AI processing failed for document {document_id}: {ai_error}")
                # Don't fail the whole task if just AI fails
                document.extraction_error = f"AI processing error: {str(ai_error)}"
        
        # Mark as completed
        document.status = DocumentStatus.COMPLETED
        document.processing_time = time.time() - start_time
        document.extraction_error = None
        db.commit()
        
        logger.info(
            f"Processing completed for document {document_id} "
            f"in {document.processing_time:.2f}s"
        )
        
        return {
            "status": "success",
            "document_id": document_id,
            "document_type": document.document_type,
            "extraction_method": method,
            "page_count": page_count,
            "processing_time": document.processing_time,
            "ai_cost": document.ai_processing_cost
        }
    
    except Exception as e:
        # Update retry count
        document = db.query(Document).filter(Document.id == document_id).first()
        if document:
            document.retry_count += 1
            document.extraction_error = str(e)
            document.processing_time = time.time() - start_time
            
            # If max retries reached, mark as failed
            if document.retry_count >= 3:
                document.status = DocumentStatus.FAILED
                logger.error(f"Max retries reached for document {document_id}")
            
            db.commit()
        
        logger.error(f"Error processing document {document_id}: {e}")
        
        # Retry the task
        if document and document.retry_count < 3:
            raise self.retry(exc=e, countdown=60 * document.retry_count)
        else:
            raise
    
    finally:
        db.close()


@celery_app.task(name='app.tasks.extraction_tasks.process_document_batch')
def process_document_batch(document_ids: list[int], use_ai: bool = True):
    """
    Process multiple documents in batch.
    
    Args:
        document_ids: List of document IDs to process
        use_ai: Whether to use AI processing
    """
    results = []
    
    for doc_id in document_ids:
        result = process_document.delay(doc_id, use_ai)
        results.append({
            "document_id": doc_id,
            "task_id": result.id
        })
    
    return results