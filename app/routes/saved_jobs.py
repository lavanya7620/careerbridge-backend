from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
from app.auth import get_current_user

router = APIRouter(prefix="/saved-jobs", tags=["Saved Jobs"])

@router.post("/{job_id}")
def save_job(
    job_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    existing = db.query(models.SavedJob).filter(
        models.SavedJob.user_id == current_user.id,
        models.SavedJob.job_id == job_id
    ).first()
    if existing:
        db.delete(existing)
        db.commit()
        return {"message": "Job unsaved", "saved": False}

    saved = models.SavedJob(user_id=current_user.id, job_id=job_id)
    db.add(saved)
    db.commit()
    return {"message": "Job saved", "saved": True}

@router.get("/")
def get_saved_jobs(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    saved = db.query(models.SavedJob).filter(
        models.SavedJob.user_id == current_user.id
    ).order_by(models.SavedJob.saved_at.desc()).all()

    result = []
    for s in saved:
        job = db.query(models.Job).filter(models.Job.id == s.job_id).first()
        company = db.query(models.Company).filter(
            models.Company.id == job.company_id
        ).first() if job else None
        if job:
            result.append({
                "saved_id": s.id,
                "job_id": job.id,
                "title": job.title,
                "company_name": company.name if company else "Unknown",
                "company_id": company.id if company else None,
                "job_type": job.job_type,
                "location": job.location,
                "salary": job.salary,
                "required_skills": job.required_skills,
                "saved_at": s.saved_at
            })
    return result

@router.get("/ids")
def get_saved_job_ids(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    saved = db.query(models.SavedJob).filter(
        models.SavedJob.user_id == current_user.id
    ).all()
    return [s.job_id for s in saved]