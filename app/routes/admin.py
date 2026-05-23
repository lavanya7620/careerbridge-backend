from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
from app.auth import require_role

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.get("/stats")
def get_stats(
    current_user=Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    total_users = db.query(models.User).count()
    students = db.query(models.User).filter(models.User.role == "student").count()
    hrs = db.query(models.User).filter(models.User.role == "hr").count()
    total_jobs = db.query(models.Job).count()
    active_jobs = db.query(models.Job).filter(models.Job.is_active == True).count()
    total_apps = db.query(models.Application).count()
    shortlisted = db.query(models.Application).filter(
        models.Application.status == "shortlisted"
    ).count()
    offered = db.query(models.Application).filter(
        models.Application.status == "offered"
    ).count()
    return {
        "total_users": total_users,
        "students": students,
        "hr_users": hrs,
        "total_jobs": total_jobs,
        "active_jobs": active_jobs,
        "total_applications": total_apps,
        "shortlisted": shortlisted,
        "offers": offered
    }

@router.get("/users")
def get_all_users(
    current_user=Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    users = db.query(models.User).order_by(
        models.User.created_at.desc()
    ).all()
    return [{
        "id": u.id,
        "name": u.name,
        "email": u.email,
        "role": u.role,
        "is_active": u.is_active,
        "created_at": u.created_at
    } for u in users]

@router.put("/users/{user_id}/toggle")
def toggle_user(
    user_id: int,
    current_user=Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = not user.is_active
    db.commit()
    return {"message": f"User {'activated' if user.is_active else 'deactivated'}",
            "is_active": user.is_active}

@router.get("/jobs")
def get_all_jobs(
    current_user=Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    jobs = db.query(models.Job).order_by(models.Job.created_at.desc()).all()
    result = []
    for job in jobs:
        company = db.query(models.Company).filter(
            models.Company.id == job.company_id
        ).first()
        app_count = db.query(models.Application).filter(
            models.Application.job_id == job.id
        ).count()
        result.append({
            "id": job.id,
            "title": job.title,
            "company_name": company.name if company else "Unknown",
            "job_type": job.job_type,
            "is_active": job.is_active,
            "applicant_count": app_count,
            "created_at": job.created_at
        })
    return result

@router.delete("/jobs/{job_id}")
def admin_delete_job(
    job_id: int,
    current_user=Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    job = db.query(models.Job).filter(models.Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    job.is_active = False
    db.commit()
    return {"message": "Job removed"}