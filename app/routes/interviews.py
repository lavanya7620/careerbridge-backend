from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
from app.auth import get_current_user, require_role
from app.email_service import send_interview_email
from pydantic import BaseModel
from typing import Optional
import asyncio

router = APIRouter(prefix="/interviews", tags=["Interviews"])

class ScheduleInterview(BaseModel):
    application_id: int
    interview_date: str
    interview_time: str
    interview_mode: str = "online"
    meeting_link: Optional[str] = None
    notes: Optional[str] = None

@router.post("/schedule")
async def schedule_interview(
    data: ScheduleInterview,
    current_user=Depends(require_role("hr")),
    db: Session = Depends(get_db)
):
    app = db.query(models.Application).filter(
        models.Application.id == data.application_id
    ).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    job = db.query(models.Job).filter(models.Job.id == app.job_id).first()
    student = db.query(models.User).filter(models.User.id == app.user_id).first()
    company = db.query(models.Company).filter(
        models.Company.hr_user_id == current_user.id
    ).first()

    # Save schedule
    schedule = models.InterviewSchedule(
        application_id=data.application_id,
        job_id=app.job_id,
        student_id=app.user_id,
        hr_id=current_user.id,
        interview_date=data.interview_date,
        interview_time=data.interview_time,
        interview_mode=data.interview_mode,
        meeting_link=data.meeting_link,
        notes=data.notes
    )
    db.add(schedule)

    # Update application status
    app.status = "interview"
    db.commit()
    db.refresh(schedule)

    # Notification
    notif = models.Notification(
        user_id=app.user_id,
        message=f"Interview scheduled for '{job.title if job else 'a job'}' on {data.interview_date} at {data.interview_time}",
        type="status"
    )
    db.add(notif)
    db.commit()

    # WebSocket push
    from app.websocket_manager import manager
    await manager.send_to_user(app.user_id, {
        "type": "notification",
        "message": f"Interview scheduled: {data.interview_date} at {data.interview_time}",
    })

    # Send email
    if student and job:
        asyncio.create_task(send_interview_email(
            email=student.email,
            name=student.name,
            job_title=job.title,
            company_name=company.name if company else "Unknown",
            interview_date=data.interview_date,
            interview_time=data.interview_time,
            interview_mode=data.interview_mode,
            meeting_link=data.meeting_link,
            notes=data.notes
        ))

    return {"message": "Interview scheduled and email sent!", "schedule_id": schedule.id}


@router.get("/my")
def get_my_interviews(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role == "student":
        schedules = db.query(models.InterviewSchedule).filter(
            models.InterviewSchedule.student_id == current_user.id
        ).order_by(models.InterviewSchedule.created_at.desc()).all()
    else:
        schedules = db.query(models.InterviewSchedule).filter(
            models.InterviewSchedule.hr_id == current_user.id
        ).order_by(models.InterviewSchedule.created_at.desc()).all()

    result = []
    for s in schedules:
        job = db.query(models.Job).filter(models.Job.id == s.job_id).first()
        student = db.query(models.User).filter(
            models.User.id == s.student_id
        ).first()
        result.append({
            "id": s.id,
            "job_title": job.title if job else "Unknown",
            "student_name": student.name if student else "Unknown",
            "interview_date": s.interview_date,
            "interview_time": s.interview_time,
            "interview_mode": s.interview_mode,
            "meeting_link": s.meeting_link,
            "notes": s.notes,
            "status": s.status
        })
    return result