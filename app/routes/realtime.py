from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app import models
from app.websocket_manager import manager
from jose import jwt, JWTError
from dotenv import load_dotenv
import os
import json
from datetime import datetime

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

router = APIRouter(tags=["Realtime"])


def get_user_from_token(token: str):
    """Open and close its own DB session safely"""
    db = SessionLocal()
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if not user_id:
            return None
        return db.query(models.User).filter(models.User.id == user_id).first()
    except JWTError:
        return None
    finally:
        db.close()  # always close


def get_unread_count(user_id: int) -> int:
    """Get unread count with its own session"""
    db = SessionLocal()
    try:
        return db.query(models.Notification).filter(
            models.Notification.user_id == user_id,
            models.Notification.is_read == False
        ).count()
    finally:
        db.close()


@router.websocket("/ws/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str):
    # Authenticate without holding a DB session open
    user = get_user_from_token(token)

    if not user:
        await websocket.close(code=4001)
        return

    user_id = user.id
    user_name = user.name

    await manager.connect(websocket, user_id)

    # Send welcome message
    unread = get_unread_count(user_id)
    await manager.send_to_user(user_id, {
        "type": "connected",
        "message": f"Welcome back, {user_name}!",
        "unread_count": unread,
        "online_users": manager.get_online_count()
    })

    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await manager.send_to_user(user_id, {
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    })
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)


@router.get("/online-status/{user_id}")
def check_online(user_id: int):
    return {"user_id": user_id, "is_online": manager.is_online(user_id)}