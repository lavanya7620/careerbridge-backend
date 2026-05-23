from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# ── Auth ──
class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str = "student"  # student / hr / admin

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    user_id: int
    name: str

# ── Profile ──
class ProfileUpdate(BaseModel):
    bio: Optional[str] = None
    location: Optional[str] = None
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    skills: Optional[List[str]] = []
    education: Optional[List[dict]] = []
    experience: Optional[List[dict]] = []
    projects: Optional[List[dict]] = []

# ── Job ──
class JobCreate(BaseModel):
    title: str
    description: str
    required_skills: List[str]
    salary: Optional[str] = None
    location: Optional[str] = None
    job_type: str = "fulltime"
    experience_level: str = "fresher"
    auto_apply_threshold: float = 75.0

class JobResponse(BaseModel):
    id: int
    title: str
    description: str
    required_skills: List[str]
    salary: Optional[str]
    location: Optional[str]
    job_type: str
    experience_level: str
    created_at: datetime
    class Config:
        from_attributes = True

# ── Application ──
class ApplicationResponse(BaseModel):
    id: int
    job_id: int
    match_score: Optional[float]
    matched_skills: List[str]
    missing_skills: List[str]
    status: str
    applied_at: datetime
    class Config:
        from_attributes = True