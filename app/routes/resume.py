from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
from app.auth import get_current_user
from app.ai.parser import parse_resume
from app.ai.ats_scorer import score_resume
from textblob import TextBlob
import os, shutil

router = APIRouter(prefix="/resume", tags=["Resume"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def upload_resume(
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Validate file type
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    # Save file
    file_path = f"{UPLOAD_DIR}/{current_user.id}_{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Parse resume
    parsed = parse_resume(file_path)

    # ATS score
    ats_result = score_resume(parsed["raw_text"])

    # Sentiment score
    blob = TextBlob(parsed["raw_text"])
    sentiment = round((blob.sentiment.polarity + 1) / 2 * 100, 2)  # 0-100 scale

    # Resume score (simple weighted average)
    resume_score = round((ats_result["ats_score"] * 0.6) + (sentiment * 0.4), 2)

    # Save to database
    resume = models.Resume(
        user_id=current_user.id,
        file_path=file_path,
        parsed_text=parsed["raw_text"],
        resume_score=resume_score,
        ats_score=ats_result["ats_score"],
        sentiment_score=sentiment,
        suggestions=ats_result["suggestions"]
    )
    db.add(resume)

    # Auto-update profile skills from resume
    profile = db.query(models.StudentProfile).filter(
        models.StudentProfile.user_id == current_user.id
    ).first()
    if profile and parsed["skills"]:
        existing = profile.skills or []
        merged = list(set(existing + parsed["skills"]))
        profile.skills = merged

    db.commit()
    db.refresh(resume)

    return {
        "message": "Resume uploaded and analyzed successfully",
        "resume_id": resume.id,
        "parsed_name": parsed["name"],
        "parsed_email": parsed["email"],
        "parsed_skills": parsed["skills"],
        "resume_score": resume_score,
        "ats_score": ats_result["ats_score"],
        "sentiment_score": sentiment,
        "suggestions": ats_result["suggestions"],
        "word_count": parsed["word_count"]
    }

@router.get("/my")
def get_my_resumes(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    resumes = db.query(models.Resume).filter(
        models.Resume.user_id == current_user.id
    ).order_by(models.Resume.created_at.desc()).all()
    return resumes