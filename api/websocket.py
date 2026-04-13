from fastapi import WebSocket, WebSocketDisconnect
from typing import List, Dict
import asyncio
import json
from datetime import datetime

class ConnectionManager:
    """Manage WebSocket connections for real-time updates"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.subscribers: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        # Remove from subscribers
        for category in self.subscribers:
            if websocket in self.subscribers[category]:
                self.subscribers[category].remove(websocket)
    
    async def subscribe(self, websocket: WebSocket, category: str):
        if category not in self.subscribers:
            self.subscribers[category] = []
        self.subscribers[category].append(websocket)
    
    async def broadcast_new_article(self, article: dict, category: str):
        """Broadcast new article to subscribers of that category"""
        message = {
            "type": "new_article",
            "category": category,
            "article": article,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Send to category subscribers
        if category in self.subscribers:
            for connection in self.subscribers[category]:
                try:
                    await connection.send_json(message)
                except:
                    pass
        
        # Send to all connections (optional)
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass
    
    async def broadcast_sentiment_update(self, sentiment_data: dict):
        """Broadcast sentiment updates"""
        message = {
            "type": "sentiment_update",
            "data": sentiment_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()
