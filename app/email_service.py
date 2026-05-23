from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
import os

# Jinja2 for rendering templates
template_dir = Path(__file__).parent / "email_templates"
jinja_env = Environment(loader=FileSystemLoader(str(template_dir)))


def get_mail_config():
    """Build config lazily so dotenv has time to load"""
    from dotenv import load_dotenv
    load_dotenv()
    username = os.getenv("MAIL_USERNAME")
    password = os.getenv("MAIL_PASSWORD")
    mail_from = os.getenv("MAIL_FROM")

    if not username or not password or not mail_from:
        return None

    return ConnectionConfig(
        MAIL_USERNAME=username,
        MAIL_PASSWORD=password,
        MAIL_FROM=mail_from,
        MAIL_FROM_NAME=os.getenv("MAIL_FROM_NAME", "CareerBridge AI"),
        MAIL_PORT=587,
        MAIL_SERVER="smtp.gmail.com",
        MAIL_STARTTLS=True,
        MAIL_SSL_TLS=False,
        USE_CREDENTIALS=True,
        VALIDATE_CERTS=True,
        TEMPLATE_FOLDER=Path(__file__).parent / "email_templates"
    )


def render_template(template_name: str, context: dict) -> str:
    template = jinja_env.get_template(template_name)
    return template.render(**context)


async def send_email_safe(subject: str, recipients: list, html: str):
    """Send email — silently skip if config missing"""
    conf = get_mail_config()
    if not conf:
        print(f"[EMAIL SKIPPED] No mail config. Subject: {subject}")
        return
    try:
        fm = FastMail(conf)
        message = MessageSchema(
            subject=subject,
            recipients=recipients,
            body=html,
            subtype=MessageType.html
        )
        await fm.send_message(message)
        print(f"[EMAIL SENT] {subject} → {recipients[0]}")
    except Exception as e:
        print(f"[EMAIL ERROR] {e}")


async def send_welcome_email(email: str, name: str):
    html = render_template("welcome.html", {
        "name": name,
        "login_url": "http://localhost:5173/login"
    })
    await send_email_safe(
        subject="Welcome to CareerBridge AI! 🎉",
        recipients=[email],
        html=html
    )


async def send_status_email(
    email: str, name: str, job_title: str,
    company_name: str, status: str, match_score: float
):
    status_map = {
        "shortlisted": ("Shortlisted ⭐", "green"),
        "interview":   ("Interview Scheduled 📅", "blue"),
        "offered":     ("Job Offer Received 🏆", "purple"),
        "rejected":    ("Application Update", "red"),
        "applied":     ("Application Received ✅", "blue")
    }
    label, color = status_map.get(status, ("Status Updated", "blue"))
    from datetime import datetime
    html = render_template("application_status.html", {
        "name": name,
        "job_title": job_title,
        "company_name": company_name,
        "status": status,
        "status_label": label,
        "badge_color": color,
        "match_score": round(match_score or 0),
        "updated_on": datetime.now().strftime("%d %b %Y, %I:%M %p"),
        "dashboard_url": "http://localhost:5173/student/applications"
    })
    await send_email_safe(
        subject=f"Application Update: {label} — {job_title}",
        recipients=[email],
        html=html
    )


async def send_interview_email(
    email: str, name: str, job_title: str, company_name: str,
    interview_date: str, interview_time: str,
    interview_mode: str, meeting_link: str = None, notes: str = None
):
    html = render_template("interview_scheduled.html", {
        "name": name,
        "job_title": job_title,
        "company_name": company_name,
        "interview_date": interview_date,
        "interview_time": interview_time,
        "interview_mode": interview_mode,
        "meeting_link": meeting_link,
        "notes": notes,
        "dashboard_url": "http://localhost:5173/student/applications"
    })
    await send_email_safe(
        subject=f"Interview Scheduled: {job_title} at {company_name}",
        recipients=[email],
        html=html
    )


async def send_job_match_alert(email: str, name: str, jobs: list):
    if not jobs:
        return
    html = render_template("job_match_alert.html", {
        "name": name,
        "job_count": len(jobs),
        "jobs": jobs,
        "jobs_url": "http://localhost:5173/student/jobs"
    })
    await send_email_safe(
        subject=f"🎯 {len(jobs)} New Job Match{'es' if len(jobs) > 1 else ''} Found!",
        recipients=[email],
        html=html
    )


async def send_weekly_digest(
    email: str, name: str, new_matches: int,
    applications: int, profile_views: int,
    resume_score: float, top_missing_skills: list,
    recommended_jobs: list
):
    html = render_template("weekly_digest.html", {
        "name": name,
        "new_matches": new_matches,
        "applications": applications,
        "profile_views": profile_views,
        "resume_score": round(resume_score or 0),
        "top_missing_skills": top_missing_skills[:5],
        "recommended_jobs": recommended_jobs[:3],
        "dashboard_url": "http://localhost:5173/student/dashboard"
    })
    await send_email_safe(
        subject="📊 Your Weekly Career Digest — CareerBridge AI",
        recipients=[email],
        html=html
    )