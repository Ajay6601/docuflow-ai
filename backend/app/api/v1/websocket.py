from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.websocket.manager import manager
import logging
import uuid

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    Main WebSocket endpoint for real-time updates.
    
    Usage:
    - Connect to: ws://localhost:8000/api/v1/ws
    - Receive real-time updates about document processing
    """
    # Generate unique connection ID
    connection_id = str(uuid.uuid4())
    
    await manager.connect(websocket, connection_id)
    
    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_json()
            
            message_type = data.get("type")
            
            if message_type == "subscribe":
                # Subscribe to specific document updates
                document_id = data.get("document_id")
                if document_id:
                    manager.subscribe_to_document(document_id, connection_id)
                    await manager.send_personal_message(
                        {
                            "type": "subscription",
                            "status": "subscribed",
                            "document_id": document_id
                        },
                        connection_id
                    )
            
            elif message_type == "unsubscribe":
                # Unsubscribe from document updates
                document_id = data.get("document_id")
                if document_id:
                    manager.unsubscribe_from_document(document_id, connection_id)
                    await manager.send_personal_message(
                        {
                            "type": "subscription",
                            "status": "unsubscribed",
                            "document_id": document_id
                        },
                        connection_id
                    )
            
            elif message_type == "ping":
                # Respond to ping with pong
                await manager.send_personal_message(
                    {"type": "pong", "timestamp": data.get("timestamp")},
                    connection_id
                )
            
            else:
                # Echo unknown messages
                await manager.send_personal_message(
                    {"type": "error", "message": f"Unknown message type: {message_type}"},
                    connection_id
                )
    
    except WebSocketDisconnect:
        manager.disconnect(connection_id)
        logger.info(f"Client disconnected: {connection_id}")
    
    except Exception as e:
        logger.error(f"WebSocket error for {connection_id}: {e}")
        manager.disconnect(connection_id)


@router.websocket("/ws/{document_id}")
async def document_websocket_endpoint(websocket: WebSocket, document_id: int):
    """
    WebSocket endpoint for specific document updates.
    
    Usage:
    - Connect to: ws://localhost:8000/api/v1/ws/123
    - Automatically subscribes to updates for document 123
    """
    connection_id = str(uuid.uuid4())
    
    await manager.connect(websocket, connection_id)
    
    # Auto-subscribe to this document
    manager.subscribe_to_document(document_id, connection_id)
    
    await manager.send_personal_message(
        {
            "type": "subscription",
            "status": "subscribed",
            "document_id": document_id,
            "message": f"Subscribed to updates for document {document_id}"
        },
        connection_id
    )
    
    try:
        while True:
            # Keep connection alive and handle client messages
            data = await websocket.receive_json()
            
            if data.get("type") == "ping":
                await manager.send_personal_message(
                    {"type": "pong", "timestamp": data.get("timestamp")},
                    connection_id
                )
    
    except WebSocketDisconnect:
        manager.disconnect(connection_id)
        logger.info(f"Client disconnected from document {document_id}: {connection_id}")
    
    except Exception as e:
        logger.error(f"WebSocket error for document {document_id}: {e}")
        manager.disconnect(connection_id)