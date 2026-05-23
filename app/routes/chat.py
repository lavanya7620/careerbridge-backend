from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
from app.auth import get_current_user
from app.websocket_manager import manager
from pydantic import BaseModel
import asyncio

router = APIRouter(prefix="/chat", tags=["Chat"])


class SendMessage(BaseModel):
    content: str


@router.get("/application/{app_id}")
def get_chat(
    app_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    app = db.query(models.Application).filter(
        models.Application.id == app_id
    ).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    # Only student or HR involved can view
    job = db.query(models.Job).filter(models.Job.id == app.job_id).first()
    company = db.query(models.Company).filter(
        models.Company.id == job.company_id
    ).first() if job else None

    is_student = app.user_id == current_user.id
    is_hr = company and company.hr_user_id == current_user.id

    if not is_student and not is_hr:
        raise HTTPException(status_code=403, detail="Access denied")

    # Mark messages as read
    db.query(models.Message).filter(
        models.Message.application_id == app_id,
        models.Message.receiver_id == current_user.id,
        models.Message.is_read == False
    ).update({"is_read": True})
    db.commit()

    messages = db.query(models.Message).filter(
        models.Message.application_id == app_id
    ).order_by(models.Message.sent_at.asc()).all()

    result = []
    for m in messages:
        sender = db.query(models.User).filter(
            models.User.id == m.sender_id
        ).first()
        result.append({
            "id": m.id,
            "content": m.content,
            "sender_id": m.sender_id,
            "sender_name": sender.name if sender else "Unknown",
            "sender_role": sender.role if sender else "",
            "is_mine": m.sender_id == current_user.id,
            "is_read": m.is_read,
            "sent_at": m.sent_at
        })
    return result


@router.post("/application/{app_id}")
async def send_message(
    app_id: int,
    data: SendMessage,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not data.content.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    app = db.query(models.Application).filter(
        models.Application.id == app_id
    ).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    job = db.query(models.Job).filter(models.Job.id == app.job_id).first()
    company = db.query(models.Company).filter(
        models.Company.id == job.company_id
    ).first() if job else None

    is_student = app.user_id == current_user.id
    is_hr = company and company.hr_user_id == current_user.id

    if not is_student and not is_hr:
        raise HTTPException(status_code=403, detail="Access denied")

    # Determine receiver
    if is_student:
        receiver_id = company.hr_user_id if company else None
    else:
        receiver_id = app.user_id

    if not receiver_id:
        raise HTTPException(status_code=400, detail="Cannot determine receiver")

    # Save message
    message = models.Message(
        application_id=app_id,
        sender_id=current_user.id,
        receiver_id=receiver_id,
        content=data.content.strip()
    )
    db.add(message)

    # Save notification
    notif = models.Notification(
        user_id=receiver_id,
        message=f"New message from {current_user.name}: {data.content[:60]}",
        type="info"
    )
    db.add(notif)
    db.commit()
    db.refresh(message)

    # Send real-time via WebSocket
    await manager.send_to_user(receiver_id, {
        "type": "new_message",
        "application_id": app_id,
        "sender_name": current_user.name,
        "sender_role": current_user.role,
        "content": data.content,
        "sent_at": message.sent_at.isoformat()
    })

    # Also push notification event
    await manager.send_to_user(receiver_id, {
        "type": "notification",
        "message": f"New message from {current_user.name}",
        "unread_count": db.query(models.Notification).filter(
            models.Notification.user_id == receiver_id,
            models.Notification.is_read == False
        ).count()
    })

    return {
        "id": message.id,
        "content": message.content,
        "sender_name": current_user.name,
        "sent_at": message.sent_at
    }


@router.get("/unread-count")
def unread_messages(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    count = db.query(models.Message).filter(
        models.Message.receiver_id == current_user.id,
        models.Message.is_read == False
    ).count()
    return {"count": count}