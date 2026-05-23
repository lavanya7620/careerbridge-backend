from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
from app.auth import get_current_user
from app.ai.matcher import calculate_match
from app.websocket_manager import manager

router = APIRouter(prefix="/live-match", tags=["Live Match"])


@router.post("/scan")
async def scan_new_jobs(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Scan latest jobs and notify user of strong matches in real-time"""
    profile = db.query(models.StudentProfile).filter(
        models.StudentProfile.user_id == current_user.id
    ).first()
    resume = db.query(models.Resume).filter(
        models.Resume.user_id == current_user.id
    ).order_by(models.Resume.created_at.desc()).first()

    if not resume or not resume.parsed_text:
        return {"message": "Upload a resume first", "matches": []}

    candidate_skills = profile.skills if profile else []

    # Get jobs not yet applied to
    applied_ids = [
        a.job_id for a in db.query(models.Application).filter(
            models.Application.user_id == current_user.id
        ).all()
    ]

    new_jobs = db.query(models.Job).filter(
        models.Job.is_active == True,
        ~models.Job.id.in_(applied_ids) if applied_ids else True
    ).order_by(models.Job.created_at.desc()).limit(20).all()

    strong_matches = []

    for job in new_jobs:
        result = calculate_match(
            resume_text=resume.parsed_text,
            job_description=job.description,
            candidate_skills=candidate_skills,
            job_skills=job.required_skills or []
        )

        if result["match_score"] >= 70:
            company = db.query(models.Company).filter(
                models.Company.id == job.company_id
            ).first()

            strong_matches.append({
                "job_id": job.id,
                "job_title": job.title,
                "company_name": company.name if company else "Unknown",
                "match_score": result["match_score"],
                "matched_skills": result["matched_skills"]
            })

            # Save notification in DB
            notif = models.Notification(
                user_id=current_user.id,
                message=f"New job match! '{job.title}' — {result['match_score']:.0f}% match",
                type="match"
            )
            db.add(notif)

            # Push real-time WebSocket notification
            await manager.send_to_user(current_user.id, {
                "type": "job_match",
                "job_id": job.id,
                "job_title": job.title,
                "company_name": company.name if company else "Unknown",
                "match_score": result["match_score"],
                "message": f"New strong match found: {job.title} ({result['match_score']:.0f}%)"
            })

    db.commit()

    strong_matches.sort(key=lambda x: x["match_score"], reverse=True)

    return {
        "message": f"Scan complete. Found {len(strong_matches)} strong matches.",
        "matches": strong_matches,
        "total_scanned": len(new_jobs)
    }