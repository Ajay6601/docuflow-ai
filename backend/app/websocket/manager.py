from fastapi import WebSocket
from typing import Dict, List, Set
import json
import logging
import asyncio

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and broadcasts messages."""
    
    def __init__(self):
        # Store active connections: {connection_id: websocket}
        self.active_connections: Dict[str, WebSocket] = {}
        
        # Store subscriptions: {document_id: set of connection_ids}
        self.document_subscriptions: Dict[int, Set[str]] = {}
        
        # Store general subscribers (get all updates)
        self.general_subscribers: Set[str] = set()
    
    async def connect(self, websocket: WebSocket, connection_id: str):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        self.general_subscribers.add(connection_id)
        
        logger.info(f"WebSocket connected: {connection_id} (total: {len(self.active_connections)})")
        
        # Send welcome message
        await self.send_personal_message(
            {
                "type": "connection",
                "status": "connected",
                "connection_id": connection_id,
                "message": "Successfully connected to DocuFlow AI"
            },
            connection_id
        )
    
    def disconnect(self, connection_id: str):
        """Remove a WebSocket connection."""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        
        # Remove from general subscribers
        if connection_id in self.general_subscribers:
            self.general_subscribers.remove(connection_id)
        
        # Remove from document subscriptions
        for doc_id, subscribers in self.document_subscriptions.items():
            if connection_id in subscribers:
                subscribers.remove(connection_id)
        
        logger.info(f"WebSocket disconnected: {connection_id} (remaining: {len(self.active_connections)})")
    
    async def send_personal_message(self, message: dict, connection_id: str):
        """Send a message to a specific connection."""
        if connection_id in self.active_connections:
            try:
                websocket = self.active_connections[connection_id]
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to {connection_id}: {e}")
                self.disconnect(connection_id)
    
    async def broadcast(self, message: dict):
        """Broadcast a message to all connected clients."""
        disconnected = []
        
        for connection_id in self.general_subscribers:
            try:
                websocket = self.active_connections[connection_id]
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to {connection_id}: {e}")
                disconnected.append(connection_id)
        
        # Clean up disconnected clients
        for connection_id in disconnected:
            self.disconnect(connection_id)
    
    async def broadcast_to_document(self, document_id: int, message: dict):
        """Broadcast a message to all clients subscribed to a specific document."""
        if document_id not in self.document_subscriptions:
            return
        
        disconnected = []
        subscribers = self.document_subscriptions[document_id].copy()
        
        for connection_id in subscribers:
            try:
                websocket = self.active_connections[connection_id]
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to {connection_id} for document {document_id}: {e}")
                disconnected.append(connection_id)
        
        # Clean up disconnected clients
        for connection_id in disconnected:
            self.disconnect(connection_id)
    
    def subscribe_to_document(self, document_id: int, connection_id: str):
        """Subscribe a connection to updates for a specific document."""
        if document_id not in self.document_subscriptions:
            self.document_subscriptions[document_id] = set()
        
        self.document_subscriptions[document_id].add(connection_id)
        logger.info(f"Connection {connection_id} subscribed to document {document_id}")
    
    def unsubscribe_from_document(self, document_id: int, connection_id: str):
        """Unsubscribe a connection from document updates."""
        if document_id in self.document_subscriptions:
            if connection_id in self.document_subscriptions[document_id]:
                self.document_subscriptions[document_id].remove(connection_id)
                logger.info(f"Connection {connection_id} unsubscribed from document {document_id}")


# Global connection manager instance
manager = ConnectionManager()