from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
from app.auth import get_current_user, require_role
from app.ai.matcher import calculate_match
from app.ai.skill_gap import get_skill_roadmap
from app.email_service import send_status_email
import asyncio


router = APIRouter(prefix="/applications", tags=["Applications"])


@router.post("/apply/{job_id}")
def apply_to_job(
    job_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check already applied
    existing = db.query(models.Application).filter(
        models.Application.user_id == current_user.id,
        models.Application.job_id == job_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already applied to this job")

    # Get job
    job = db.query(models.Job).filter(models.Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Get student profile + resume
    profile = db.query(models.StudentProfile).filter(
        models.StudentProfile.user_id == current_user.id
    ).first()
    resume = db.query(models.Resume).filter(
        models.Resume.user_id == current_user.id
    ).order_by(models.Resume.created_at.desc()).first()

    resume_text = resume.parsed_text if resume else ""
    candidate_skills = profile.skills if profile else []

    # Run AI matching
    match_result = calculate_match(
        resume_text=resume_text,
        job_description=job.description,
        candidate_skills=candidate_skills,
        job_skills=job.required_skills or []
    )

    # Save application
    application = models.Application(
        user_id=current_user.id,
        job_id=job_id,
        match_score=match_result["match_score"],
        matched_skills=match_result["matched_skills"],
        missing_skills=match_result["missing_skills"],
        status="applied"
    )
    db.add(application)

    # Save skill gap log
    if match_result["missing_skills"]:
        roadmap = get_skill_roadmap(match_result["missing_skills"])
        gap_log = models.SkillGapLog(
            user_id=current_user.id,
            job_id=job_id,
            missing_skills=match_result["missing_skills"],
            suggested_courses=[r["courses"][0]["url"] for r in roadmap]
        )
        db.add(gap_log)

    # Send notification
    notif = models.Notification(
        user_id=current_user.id,
        message=f"Applied to '{job.title}' with {match_result['match_score']:.0f}% match score",
        type="match"
    )
    db.add(notif)
    db.commit()

    return {
        "message": "Application submitted successfully!",
        "match_score": match_result["match_score"],
        "matched_skills": match_result["matched_skills"],
        "missing_skills": match_result["missing_skills"],
        "explanation": match_result["explanation"]
    }


@router.get("/my")
def get_my_applications(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    apps = db.query(models.Application).filter(
        models.Application.user_id == current_user.id
    ).order_by(models.Application.applied_at.desc()).all()

    result = []
    for app in apps:
        job = db.query(models.Job).filter(models.Job.id == app.job_id).first()
        company = db.query(models.Company).filter(
            models.Company.id == job.company_id
        ).first() if job else None

        result.append({
            "id": app.id,
            "job_id": app.job_id,
            "job_title": job.title if job else "Unknown",
            "company_name": company.name if company else "Unknown",
            "match_score": app.match_score,
            "matched_skills": app.matched_skills,
            "missing_skills": app.missing_skills,
            "status": app.status,
            "applied_at": app.applied_at
        })
    return result


@router.get("/skill-gap")
def get_skill_gap(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Get all missing skills from all applications
    apps = db.query(models.Application).filter(
        models.Application.user_id == current_user.id
    ).all()

    all_missing = []
    for app in apps:
        all_missing.extend(app.missing_skills or [])

    # Count frequency
    skill_freq = {}
    for skill in all_missing:
        skill_freq[skill] = skill_freq.get(skill, 0) + 1

    # Sort by frequency
    sorted_skills = sorted(skill_freq.keys(),
                          key=lambda s: skill_freq[s], reverse=True)

    roadmap = get_skill_roadmap(sorted_skills[:10])

    return {
        "missing_skills": sorted_skills,
        "skill_frequency": skill_freq,
        "roadmap": roadmap
    }


# HR: Get applicants for a job
@router.get("/job/{job_id}/candidates")
def get_job_candidates(
    job_id: int,
    current_user=Depends(require_role("hr")),
    db: Session = Depends(get_db)
):
    apps = db.query(models.Application).filter(
        models.Application.job_id == job_id
    ).order_by(models.Application.match_score.desc()).all()

    result = []
    for app in apps:
        user = db.query(models.User).filter(models.User.id == app.user_id).first()
        profile = db.query(models.StudentProfile).filter(
            models.StudentProfile.user_id == app.user_id
        ).first()
        result.append({
            "application_id": app.id,
            "user_id": app.user_id,
            "name": user.name if user else "Unknown",
            "email": user.email if user else "",
            "match_score": app.match_score,
            "matched_skills": app.matched_skills,
            "missing_skills": app.missing_skills,
            "skills": profile.skills if profile else [],
            "status": app.status,
            "applied_at": app.applied_at
        })
    return result


# HR: Update application status
@router.put("/{app_id}/status")
def update_status(
    app_id: int,
    status: str,
    current_user=Depends(require_role("hr")),
    db: Session = Depends(get_db)
):
    valid = ["applied", "shortlisted", "interview", "offered", "rejected"]
    if status not in valid:
        raise HTTPException(status_code=400, detail=f"Invalid status. Use: {valid}")

    app = db.query(models.Application).filter(models.Application.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    app.status = status
    db.commit()

    # Notify student
    job = db.query(models.Job).filter(models.Job.id == app.job_id).first()
    notif = models.Notification(
        user_id=app.user_id,
        message=f"Your application for '{job.title if job else 'a job'}' is now: {status.upper()}",
        type="status"
    )
    db.add(notif)
    db.commit()

    return {"message": f"Status updated to {status}"}

@router.post("/auto-apply")
def run_auto_apply(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Scan all active jobs and auto-apply if match exceeds threshold"""
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Students only")

    profile = db.query(models.StudentProfile).filter(
        models.StudentProfile.user_id == current_user.id
    ).first()
    resume = db.query(models.Resume).filter(
        models.Resume.user_id == current_user.id
    ).order_by(models.Resume.created_at.desc()).first()

    if not resume or not resume.parsed_text:
        raise HTTPException(status_code=400, detail="Upload a resume first")

    candidate_skills = profile.skills if profile else []
    active_jobs = db.query(models.Job).filter(models.Job.is_active == True).all()

    auto_applied = []
    skipped = []

    for job in active_jobs:
        # Skip already applied
        existing = db.query(models.Application).filter(
            models.Application.user_id == current_user.id,
            models.Application.job_id == job.id
        ).first()
        if existing:
            skipped.append(job.id)
            continue

        # Run AI match
        from app.ai.matcher import calculate_match
        match_result = calculate_match(
            resume_text=resume.parsed_text,
            job_description=job.description,
            candidate_skills=candidate_skills,
            job_skills=job.required_skills or []
        )

        # Auto-apply if above threshold
        if match_result["match_score"] >= job.auto_apply_threshold:
            application = models.Application(
                user_id=current_user.id,
                job_id=job.id,
                match_score=match_result["match_score"],
                matched_skills=match_result["matched_skills"],
                missing_skills=match_result["missing_skills"],
                status="applied",
                is_auto_applied=True
            )
            db.add(application)

            notif = models.Notification(
                user_id=current_user.id,
                message=f"Auto-applied to '{job.title}' — {match_result['match_score']:.0f}% match",
                type="match"
            )
            db.add(notif)
            auto_applied.append({
                "job_id": job.id,
                "job_title": job.title,
                "match_score": match_result["match_score"]
            })

    db.commit()

    return {
        "message": f"Auto-apply complete. Applied to {len(auto_applied)} new jobs.",
        "auto_applied": auto_applied,
        "total_scanned": len(active_jobs),
        "already_applied": len(skipped)
    }

@router.get("/cover-letter/{job_id}")
def generate_cover_letter(
    job_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    job = db.query(models.Job).filter(models.Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    profile = db.query(models.StudentProfile).filter(
        models.StudentProfile.user_id == current_user.id
    ).first()
    company = db.query(models.Company).filter(
        models.Company.id == job.company_id
    ).first()

    skills = profile.skills[:6] if profile and profile.skills else []
    skill_str = ", ".join(skills) if skills else "various technical skills"
    company_name = company.name if company else "your company"

    cover_letter = f"""Dear Hiring Manager at {company_name},

I am writing to express my strong interest in the {job.title} position. As a passionate and driven candidate with expertise in {skill_str}, I believe I would be a great fit for this role.

Having reviewed the job requirements carefully, I am confident that my technical background aligns well with what you are looking for. My experience with {", ".join(skills[:3]) if skills else "relevant technologies"} has prepared me to contribute effectively from day one.

What excites me most about this opportunity is the chance to work on {job.description[:100].rstrip()}... I am particularly drawn to {company_name}'s work and believe this role would allow me to grow while making meaningful contributions to your team.

I am eager to bring my problem-solving mindset and collaborative approach to your organization. I would welcome the opportunity to discuss how my background and skills can contribute to {company_name}'s goals.

Thank you for considering my application. I look forward to the opportunity to speak with you.

Sincerely,
{current_user.name}"""

    return {
        "cover_letter": cover_letter,
        "job_title": job.title,
        "company_name": company_name
    }

@router.put("/{app_id}/status")
async def update_status(
    app_id: int,
    status: str,
    current_user=Depends(require_role("hr")),
    db: Session = Depends(get_db)
):
    valid = ["applied", "shortlisted", "interview", "offered", "rejected"]
    if status not in valid:
        raise HTTPException(status_code=400, detail=f"Invalid status")

    app = db.query(models.Application).filter(
        models.Application.id == app_id
    ).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    app.status = status
    db.commit()

    job = db.query(models.Job).filter(models.Job.id == app.job_id).first()
    student = db.query(models.User).filter(models.User.id == app.user_id).first()
    company = db.query(models.Company).filter(
        models.Company.id == job.company_id
    ).first() if job else None

    # Save notification
    notif = models.Notification(
        user_id=app.user_id,
        message=f"Your application for '{job.title if job else 'a job'}' is now: {status.upper()}",
        type="status"
    )
    db.add(notif)
    db.commit()

    # Push WebSocket
    from app.websocket_manager import manager
    await manager.send_to_user(app.user_id, {
        "type": "notification",
        "message": f"Application status updated to {status}",
        "unread_count": db.query(models.Notification).filter(
            models.Notification.user_id == app.user_id,
            models.Notification.is_read == False
        ).count()
    })

    # Send email (non-blocking)
    if student and job:
        asyncio.create_task(send_status_email(
            email=student.email,
            name=student.name,
            job_title=job.title,
            company_name=company.name if company else "Unknown",
            status=status,
            match_score=app.match_score or 0
        ))

    return {"message": f"Status updated to {status}"}

@router.delete("/{app_id}/withdraw")
async def withdraw_application(
    app_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    app = db.query(models.Application).filter(
        models.Application.id == app_id,
        models.Application.user_id == current_user.id
    ).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    if app.status not in ["applied"]:
        raise HTTPException(
            status_code=400,
            detail="Can only withdraw pending applications"
        )
    db.delete(app)
    db.commit()
    return {"message": "Application withdrawn"}

@router.post("/bulk-shortlist/{job_id}")
async def bulk_shortlist(
    job_id: int,
    top_n: int = 5,
    current_user=Depends(require_role("hr")),
    db: Session = Depends(get_db)
):
    """Shortlist top N candidates by match score"""
    apps = db.query(models.Application).filter(
        models.Application.job_id == job_id,
        models.Application.status == "applied"
    ).order_by(models.Application.match_score.desc()).limit(top_n).all()

    if not apps:
        return {"message": "No pending applications found", "shortlisted": 0}

    job = db.query(models.Job).filter(models.Job.id == job_id).first()
    company = db.query(models.Company).filter(
        models.Company.hr_user_id == current_user.id
    ).first()

    shortlisted_count = 0
    for app in apps:
        app.status = "shortlisted"
        student = db.query(models.User).filter(
            models.User.id == app.user_id
        ).first()

        notif = models.Notification(
            user_id=app.user_id,
            message=f"You've been shortlisted for '{job.title if job else 'a job'}'! 🎉",
            type="match"
        )
        db.add(notif)

        # Email
        if student and job:
            from app.email_service import send_status_email
            import asyncio
            asyncio.create_task(send_status_email(
                email=student.email,
                name=student.name,
                job_title=job.title,
                company_name=company.name if company else "Unknown",
                status="shortlisted",
                match_score=app.match_score or 0
            ))

        # WebSocket
        from app.websocket_manager import manager
        await manager.send_to_user(app.user_id, {
            "type": "notification",
            "message": f"You've been shortlisted for {job.title if job else 'a job'}! 🎉"
        })

        shortlisted_count += 1

    db.commit()
    return {
        "message": f"Top {shortlisted_count} candidates shortlisted and notified",
        "shortlisted": shortlisted_count
    }