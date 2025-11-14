import asyncio
from app.websocket.manager import manager
from app.models.document import DocumentStatus
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for sending WebSocket notifications."""
    
    @staticmethod
    async def notify_document_status(
        document_id: int,
        status: DocumentStatus,
        message: str = None,
        progress: int = None,
        metadata: dict = None
    ):
        """
        Notify about document status change.
        
        Args:
            document_id: Document ID
            status: New status
            message: Optional message
            progress: Optional progress percentage (0-100)
            metadata: Optional additional data
        """
        notification = {
            "type": "document_status",
            "document_id": document_id,
            "status": status.value,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        if message:
            notification["message"] = message
        
        if progress is not None:
            notification["progress"] = progress
        
        if metadata:
            notification["metadata"] = metadata
        
        # Broadcast to document subscribers
        await manager.broadcast_to_document(document_id, notification)
        
        # Also broadcast to general subscribers
        await manager.broadcast(notification)
        
        logger.info(f"Notified status change for document {document_id}: {status.value}")
    
    @staticmethod
    async def notify_extraction_started(document_id: int):
        """Notify that extraction has started."""
        await NotificationService.notify_document_status(
            document_id=document_id,
            status=DocumentStatus.PROCESSING,
            message="Text extraction started",
            progress=10
        )
    
    @staticmethod
    async def notify_extraction_completed(document_id: int, method: str, page_count: int = None):
        """Notify that extraction has completed."""
        metadata = {"extraction_method": method}
        if page_count:
            metadata["page_count"] = page_count
        
        await NotificationService.notify_document_status(
            document_id=document_id,
            status=DocumentStatus.PROCESSING,
            message="Text extraction completed",
            progress=40,
            metadata=metadata
        )
    
    @staticmethod
    async def notify_ai_processing_started(document_id: int):
        """Notify that AI processing has started."""
        await NotificationService.notify_document_status(
            document_id=document_id,
            status=DocumentStatus.PROCESSING,
            message="AI processing started",
            progress=50
        )
    
    @staticmethod
    async def notify_ai_classification_completed(
        document_id: int,
        document_type: str,
        confidence: float
    ):
        """Notify that AI classification completed."""
        await NotificationService.notify_document_status(
            document_id=document_id,
            status=DocumentStatus.PROCESSING,
            message=f"Document classified as {document_type}",
            progress=70,
            metadata={
                "document_type": document_type,
                "confidence": confidence
            }
        )
    
    @staticmethod
    async def notify_processing_completed(
        document_id: int,
        processing_time: float,
        document_type: str = None
    ):
        """Notify that processing is fully completed."""
        metadata = {"processing_time": processing_time}
        if document_type:
            metadata["document_type"] = document_type
        
        await NotificationService.notify_document_status(
            document_id=document_id,
            status=DocumentStatus.COMPLETED,
            message="Processing completed successfully",
            progress=100,
            metadata=metadata
        )
    
    @staticmethod
    async def notify_processing_failed(document_id: int, error: str):
        """Notify that processing failed."""
        await NotificationService.notify_document_status(
            document_id=document_id,
            status=DocumentStatus.FAILED,
            message=f"Processing failed: {error}",
            progress=0,
            metadata={"error": error}
        )


# Singleton instance
notification_service = NotificationService()