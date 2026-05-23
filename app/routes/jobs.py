from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.auth import get_current_user, require_role
from typing import Optional

router = APIRouter(prefix="/jobs", tags=["Jobs"])

@router.post("/")
def create_job(
    job_data: schemas.JobCreate,
    current_user=Depends(require_role("hr")),
    db: Session = Depends(get_db)
):
    # Get or create company
    company = db.query(models.Company).filter(
        models.Company.hr_user_id == current_user.id
    ).first()
    if not company:
        company = models.Company(
            name=f"{current_user.name}'s Company",
            hr_user_id=current_user.id
        )
        db.add(company)
        db.commit()
        db.refresh(company)

    job = models.Job(
        company_id=company.id,
        title=job_data.title,
        description=job_data.description,
        required_skills=job_data.required_skills,
        salary=job_data.salary,
        location=job_data.location,
        job_type=job_data.job_type,
        experience_level=job_data.experience_level,
        auto_apply_threshold=job_data.auto_apply_threshold
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return {"message": "Job posted successfully", "job_id": job.id}


@router.get("/")
def get_jobs(
    search: Optional[str] = Query(None),
    job_type: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    experience_level: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    query = db.query(models.Job).filter(models.Job.is_active == True)

    if search:
        query = query.filter(
            models.Job.title.ilike(f"%{search}%") |
            models.Job.description.ilike(f"%{search}%")
        )
    if job_type:
        query = query.filter(models.Job.job_type == job_type)
    if location:
        query = query.filter(models.Job.location.ilike(f"%{location}%"))
    if experience_level:
        query = query.filter(models.Job.experience_level == experience_level)

    jobs = query.order_by(models.Job.created_at.desc()).all()

    result = []
    for job in jobs:
        company = db.query(models.Company).filter(
            models.Company.id == job.company_id
        ).first()
        result.append({
            "id": job.id,
            "title": job.title,
            "description": job.description[:200] + "...",
            "required_skills": job.required_skills,
            "salary": job.salary,
            "location": job.location,
            "job_type": job.job_type,
            "experience_level": job.experience_level,
            "company_name": company.name if company else "Unknown",
            "created_at": job.created_at
        })
    return result


@router.get("/{job_id}")
def get_job(job_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    job = db.query(models.Job).filter(models.Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    company = db.query(models.Company).filter(models.Company.id == job.company_id).first()
    return {
        "id": job.id,
        "title": job.title,
        "description": job.description,
        "required_skills": job.required_skills,
        "salary": job.salary,
        "location": job.location,
        "job_type": job.job_type,
        "experience_level": job.experience_level,
        "auto_apply_threshold": job.auto_apply_threshold,
        "company_name": company.name if company else "Unknown",
        "created_at": job.created_at
    }


@router.get("/hr/my-jobs")
def get_hr_jobs(
    current_user=Depends(require_role("hr")),
    db: Session = Depends(get_db)
):
    company = db.query(models.Company).filter(
        models.Company.hr_user_id == current_user.id
    ).first()
    if not company:
        return []
    jobs = db.query(models.Job).filter(
        models.Job.company_id == company.id
    ).order_by(models.Job.created_at.desc()).all()

    result = []
    for job in jobs:
        app_count = db.query(models.Application).filter(
            models.Application.job_id == job.id
        ).count()
        result.append({
            "id": job.id,
            "title": job.title,
            "job_type": job.job_type,
            "location": job.location,
            "is_active": job.is_active,
            "applicant_count": app_count,
            "created_at": job.created_at
        })
    return result


@router.delete("/{job_id}")
def delete_job(
    job_id: int,
    current_user=Depends(require_role("hr")),
    db: Session = Depends(get_db)
):
    job = db.query(models.Job).filter(models.Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    job.is_active = False
    db.commit()
    return {"message": "Job removed successfully"}

@router.get("/public/all")
def get_public_jobs(
    search: Optional[str] = Query(None),
    job_type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Public endpoint — no authentication required"""
    query = db.query(models.Job).filter(models.Job.is_active == True)
    if search:
        query = query.filter(
            models.Job.title.ilike(f"%{search}%") |
            models.Job.description.ilike(f"%{search}%")
        )
    if job_type and job_type != "all":
        query = query.filter(models.Job.job_type == job_type)

    jobs = query.order_by(models.Job.created_at.desc()).all()
    result = []
    for job in jobs:
        company = db.query(models.Company).filter(
            models.Company.id == job.company_id
        ).first()
        result.append({
            "id": job.id,
            "title": job.title,
            "description": job.description[:200] + "...",
            "required_skills": job.required_skills,
            "salary": job.salary,
            "location": job.location,
            "job_type": job.job_type,
            "experience_level": job.experience_level,
            "company_name": company.name if company else "Unknown",
            "company_id": job.company_id,
            "created_at": job.created_at
        })
    return result