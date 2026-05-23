from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
from app.auth import get_current_user, require_role
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/company", tags=["Company"])

class CompanyUpdate(BaseModel):
    name: str
    description: Optional[str] = None
    website: Optional[str] = None

@router.get("/my")
def get_my_company(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Allow any role to fetch their company
    company = db.query(models.Company).filter(
        models.Company.hr_user_id == current_user.id
    ).first()
    if not company:
        return {}
    return {
        "id": company.id,
        "name": company.name,
        "description": company.description,
        "website": company.website,
    }

@router.put("/my")
def update_my_company(
    data: CompanyUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    company = db.query(models.Company).filter(
        models.Company.hr_user_id == current_user.id
    ).first()
    if not company:
        company = models.Company(hr_user_id=current_user.id)
        db.add(company)

    company.name = data.name
    company.description = data.description
    company.website = data.website
    db.commit()
    db.refresh(company)
    return {"message": "Company profile updated"}

@router.get("/all")
def get_all_companies(db: Session = Depends(get_db)):
    companies = db.query(models.Company).all()
    result = []
    for c in companies:
        job_count = db.query(models.Job).filter(
            models.Job.company_id == c.id,
            models.Job.is_active == True
        ).count()
        result.append({
            "id": c.id,
            "name": c.name,
            "description": c.description,
            "website": c.website,
            "active_jobs": job_count
        })
    return result

@router.get("/{company_id}")
def get_company(company_id: int, db: Session = Depends(get_db)):
    company = db.query(models.Company).filter(
        models.Company.id == company_id
    ).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    jobs = db.query(models.Job).filter(
        models.Job.company_id == company_id,
        models.Job.is_active == True
    ).order_by(models.Job.created_at.desc()).all()

    return {
        "id": company.id,
        "name": company.name,
        "description": company.description,
        "website": company.website,
        "jobs": [{
            "id": j.id,
            "title": j.title,
            "job_type": j.job_type,
            "location": j.location,
            "salary": j.salary,
            "required_skills": j.required_skills,
            "created_at": j.created_at
        } for j in jobs]
    }