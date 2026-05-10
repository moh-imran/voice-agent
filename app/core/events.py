import asyncio
import json
import time
from typing import List, Dict, Any
from fastapi import WebSocket
from app.engine.context import ContextManager

class EventManager:
    _instance = None
    REDIS_KEY = "system_events"
    MAX_EVENTS = 50
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EventManager, cls).__new__(cls)
            cls._instance.connections: List[WebSocket] = []
        return cls._instance

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.connections:
            self.connections.remove(websocket)

    async def broadcast(self, event_type: str, data: Dict[str, Any]):
        event_obj = {
            "type": event_type,
            "data": data,
            "timestamp": time.time()
        }
        message = json.dumps(event_obj)
        print(f"[EventManager] Broadasting: {event_type}")
        
        # Persist to Redis
        try:
            redis = ContextManager.get_instance().redis
            redis.lpush(self.REDIS_KEY, message)
            redis.ltrim(self.REDIS_KEY, 0, self.MAX_EVENTS - 1)
            print(f"[EventManager] Saved to Redis: {self.REDIS_KEY}")
        except Exception as e:
            print(f"[EventManager] Redis Error: {e}")

        # Broadcast to all live sessions
        active_connections = list(self.connections)
        for connection in active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                self.disconnect(connection)

    def get_history(self) -> List[Dict[str, Any]]:
        try:
            redis = ContextManager.get_instance().redis
            events = redis.lrange(self.REDIS_KEY, 0, -1)
            print(f"[EventManager] Fetched {len(events)} history items")
            return [json.loads(e) for e in events]
        except Exception as e:
            print(f"[EventManager] History Fetch Error: {e}")
            return []

# Global singleton
event_manager = EventManager()

async def emit_event(event_type: str, data: Dict[str, Any]):
    await event_manager.broadcast(event_type, data)
