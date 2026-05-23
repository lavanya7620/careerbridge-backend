from fastapi import WebSocket
from typing import Dict, List
import json

class ConnectionManager:
    def __init__(self):
        # user_id -> list of active connections
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        print(f"User {user_id} connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket, user_id: int):
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        print(f"User {user_id} disconnected.")

    async def send_to_user(self, user_id: int, data: dict):
        """Send message to all connections of a specific user"""
        if user_id in self.active_connections:
            dead = []
            for ws in self.active_connections[user_id]:
                try:
                    await ws.send_text(json.dumps(data))
                except Exception:
                    dead.append(ws)
            for ws in dead:
                self.active_connections[user_id].remove(ws)

    async def broadcast(self, data: dict):
        """Send message to all connected users"""
        for user_id in list(self.active_connections.keys()):
            await self.send_to_user(user_id, data)

    def is_online(self, user_id: int) -> bool:
        return user_id in self.active_connections and \
               len(self.active_connections[user_id]) > 0

    def get_online_count(self) -> int:
        return len(self.active_connections)


# Global instance — shared across all routes
manager = ConnectionManager()