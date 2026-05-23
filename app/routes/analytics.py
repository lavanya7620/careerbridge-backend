from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.database import get_db
from app import models
from app.auth import get_current_user
from datetime import datetime, timedelta

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/skill-trends")
def get_skill_trends(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Most demanded skills across all active jobs"""
    jobs = db.query(models.Job).filter(models.Job.is_active == True).all()

    skill_count = {}
    for job in jobs:
        for skill in (job.required_skills or []):
            key = skill.lower()
            skill_count[key] = skill_count.get(key, 0) + 1

    sorted_skills = sorted(
        skill_count.items(), key=lambda x: x[1], reverse=True
    )

    return [{
        "skill": s[0].title(),
        "demand_count": s[1],
        "demand_percent": round(s[1] / len(jobs) * 100, 1) if jobs else 0
    } for s in sorted_skills[:15]]


@router.get("/salary-insights")
def get_salary_insights(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Salary ranges by job type"""
    jobs = db.query(models.Job).filter(
        models.Job.is_active == True,
        models.Job.salary != None
    ).all()

    by_type = {}
    for job in jobs:
        jt = job.job_type or "fulltime"
        if jt not in by_type:
            by_type[jt] = []
        by_type[jt].append(job.salary)

    return [{
        "job_type": k,
        "sample_salaries": v[:5],
        "total_jobs": len(v)
    } for k, v in by_type.items()]


@router.get("/market-demand")
def get_market_demand(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Jobs by type + experience level breakdown"""
    jobs = db.query(models.Job).filter(models.Job.is_active == True).all()
    total = len(jobs)

    by_type = {}
    by_level = {}

    for job in jobs:
        t = job.job_type or "fulltime"
        l = job.experience_level or "fresher"
        by_type[t] = by_type.get(t, 0) + 1
        by_level[l] = by_level.get(l, 0) + 1

    return {
        "total_active_jobs": total,
        "by_type": [{"type": k, "count": v, "percent": round(v/total*100, 1) if total else 0}
                    for k, v in sorted(by_type.items(), key=lambda x: x[1], reverse=True)],
        "by_level": [{"level": k, "count": v, "percent": round(v/total*100, 1) if total else 0}
                     for k, v in sorted(by_level.items(), key=lambda x: x[1], reverse=True)]
    }


@router.post("/profile-view/{user_id}")
def record_profile_view(
    user_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Record when someone views a profile"""
    if user_id == current_user.id:
        return {"message": "Own view not recorded"}
    view = models.ProfileView(
        viewed_user_id=user_id,
        viewer_id=current_user.id
    )
    db.add(view)
    db.commit()
    return {"message": "View recorded"}


@router.get("/my-profile-views")
def get_my_profile_views(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """How many times profile was viewed"""
    total = db.query(models.ProfileView).filter(
        models.ProfileView.viewed_user_id == current_user.id
    ).count()

    week_ago = datetime.utcnow() - timedelta(days=7)
    this_week = db.query(models.ProfileView).filter(
        models.ProfileView.viewed_user_id == current_user.id,
        models.ProfileView.viewed_at >= week_ago
    ).count()

    return {"total_views": total, "this_week": this_week}


@router.get("/job-alert-preferences")
def get_alert_prefs(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    pref = db.query(models.JobAlertPreference).filter(
        models.JobAlertPreference.user_id == current_user.id
    ).first()
    if not pref:
        return {
            "is_active": False,
            "min_match_score": 70.0,
            "job_types": [],
            "keywords": []
        }
    return pref


@router.put("/job-alert-preferences")
def update_alert_prefs(
    data: dict,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    pref = db.query(models.JobAlertPreference).filter(
        models.JobAlertPreference.user_id == current_user.id
    ).first()
    if not pref:
        pref = models.JobAlertPreference(user_id=current_user.id)
        db.add(pref)

    pref.is_active = data.get("is_active", True)
    pref.min_match_score = data.get("min_match_score", 70.0)
    pref.job_types = data.get("job_types", [])
    pref.keywords = data.get("keywords", [])
    db.commit()
    return {"message": "Preferences saved"}