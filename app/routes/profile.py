from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.auth import get_current_user

router = APIRouter(prefix="/profile", tags=["Profile"])

@router.get("/")
def get_profile(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(models.StudentProfile).filter(
        models.StudentProfile.user_id == current_user.id
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {
        "user_id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "bio": profile.bio,
        "location": profile.location,
        "phone": profile.phone,
        "linkedin": profile.linkedin,
        "github": profile.github,
        "skills": profile.skills or [],
        "education": profile.education or [],
        "experience": profile.experience or [],
        "projects": profile.projects or []
    }

@router.put("/")
def update_profile(
    data: schemas.ProfileUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = db.query(models.StudentProfile).filter(
        models.StudentProfile.user_id == current_user.id
    ).first()
    if not profile:
        profile = models.StudentProfile(user_id=current_user.id)
        db.add(profile)

    # Update fields
    for field, value in data.dict(exclude_unset=True).items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)
    return {"message": "Profile updated successfully"}

@router.post("/skills")
def update_skills(
    skills: list[str],
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = db.query(models.StudentProfile).filter(
        models.StudentProfile.user_id == current_user.id
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    profile.skills = skills
    db.commit()
    return {"message": "Skills updated", "skills": skills}

@router.get("/stats")
def get_student_stats(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    total_applications = db.query(models.Application).filter(
        models.Application.user_id == current_user.id
    ).count()

    shortlisted = db.query(models.Application).filter(
        models.Application.user_id == current_user.id,
        models.Application.status == "shortlisted"
    ).count()

    interviews = db.query(models.Application).filter(
        models.Application.user_id == current_user.id,
        models.Application.status == "interview"
    ).count()

    offers = db.query(models.Application).filter(
        models.Application.user_id == current_user.id,
        models.Application.status == "offered"
    ).count()

    latest_resume = db.query(models.Resume).filter(
        models.Resume.user_id == current_user.id
    ).order_by(models.Resume.created_at.desc()).first()

    profile = db.query(models.StudentProfile).filter(
        models.StudentProfile.user_id == current_user.id
    ).first()

    return {
        "total_applications": total_applications,
        "shortlisted": shortlisted,
        "interviews": interviews,
        "offers": offers,
        "resume_score": latest_resume.resume_score if latest_resume else None,
        "ats_score": latest_resume.ats_score if latest_resume else None,
        "skills_count": len(profile.skills) if profile and profile.skills else 0,
        "profile_complete": bool(
            profile and profile.bio and profile.skills and profile.education
        )
    }

@router.get("/career-suggestions")
def career_suggestions(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = db.query(models.StudentProfile).filter(
        models.StudentProfile.user_id == current_user.id
    ).first()
    resume = db.query(models.Resume).filter(
        models.Resume.user_id == current_user.id
    ).order_by(models.Resume.created_at.desc()).first()

    from app.ai.career_suggestions import get_career_suggestions
    suggestions = get_career_suggestions(
        candidate_skills=profile.skills if profile else [],
        resume_text=resume.parsed_text if resume else ""
    )
    return suggestions

@router.get("/onboarding-status")
def onboarding_status(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = db.query(models.StudentProfile).filter(
        models.StudentProfile.user_id == current_user.id
    ).first()
    resume = db.query(models.Resume).filter(
        models.Resume.user_id == current_user.id
    ).first()

    steps = [
        {
            "id": "profile",
            "label": "Complete your profile",
            "description": "Add bio, location and contact info",
            "done": bool(profile and profile.bio and profile.location)
        },
        {
            "id": "skills",
            "label": "Add your skills",
            "description": "Add at least 5 skills",
            "done": bool(profile and profile.skills and len(profile.skills) >= 5)
        },
        {
            "id": "education",
            "label": "Add education",
            "description": "Add your degree and college",
            "done": bool(profile and profile.education and len(profile.education) > 0)
        },
        {
            "id": "resume",
            "label": "Upload your resume",
            "description": "Get AI resume analysis",
            "done": bool(resume)
        },
        {
            "id": "apply",
            "label": "Apply to your first job",
            "description": "Get your AI match score",
            "done": bool(
                db.query(models.Application).filter(
                    models.Application.user_id == current_user.id
                ).first()
            )
        }
    ]

    completed = sum(1 for s in steps if s["done"])
    return {
        "steps": steps,
        "completed": completed,
        "total": len(steps),
        "percent": round(completed / len(steps) * 100),
        "is_complete": completed == len(steps)
    }