from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
from app.auth import get_current_user

router = APIRouter(prefix="/leaderboard", tags=["Leaderboard"])

@router.get("/")
def get_leaderboard(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    students = db.query(models.User).filter(
        models.User.role == "student",
        models.User.is_active == True
    ).all()

    leaderboard = []
    for student in students:
        resume = db.query(models.Resume).filter(
            models.Resume.user_id == student.id
        ).order_by(models.Resume.created_at.desc()).first()

        profile = db.query(models.StudentProfile).filter(
            models.StudentProfile.user_id == student.id
        ).first()

        app_count = db.query(models.Application).filter(
            models.Application.user_id == student.id
        ).count()

        shortlisted = db.query(models.Application).filter(
            models.Application.user_id == student.id,
            models.Application.status.in_(["shortlisted", "interview", "offered"])
        ).count()

        resume_score = resume.resume_score if resume else 0
        skill_count = len(profile.skills) if profile and profile.skills else 0

        # Composite score: 50% resume, 30% shortlist rate, 20% skill count
        shortlist_rate = (shortlisted / app_count * 100) if app_count > 0 else 0
        skill_score = min(skill_count * 5, 100)
        composite = round(
            (resume_score * 0.5) +
            (shortlist_rate * 0.3) +
            (skill_score * 0.2), 1
        )

        leaderboard.append({
            "user_id": student.id,
            "name": student.name,
            "resume_score": round(resume_score, 1) if resume_score else 0,
            "skill_count": skill_count,
            "applications": app_count,
            "shortlisted": shortlisted,
            "composite_score": composite,
            "is_current_user": student.id == current_user.id
        })

    leaderboard.sort(key=lambda x: x["composite_score"], reverse=True)

    for i, entry in enumerate(leaderboard):
        entry["rank"] = i + 1

    return leaderboard[:20]