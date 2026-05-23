from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, default="student")  # student / hr / admin
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    profile = relationship("StudentProfile", back_populates="user", uselist=False)
    resumes = relationship("Resume", back_populates="user")
    applications = relationship("Application", back_populates="user")
    notifications = relationship("Notification", back_populates="user")


class StudentProfile(Base):
    __tablename__ = "student_profiles"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    bio = Column(Text, nullable=True)
    location = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    linkedin = Column(String, nullable=True)
    github = Column(String, nullable=True)
    skills = Column(JSON, default=[])        # ["Python", "React", ...]
    education = Column(JSON, default=[])     # [{degree, college, year, cgpa}]
    experience = Column(JSON, default=[])    # [{company, role, duration, desc}]
    projects = Column(JSON, default=[])      # [{title, desc, tech, link}]

    user = relationship("User", back_populates="profile")


class Company(Base):
    __tablename__ = "companies"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    website = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    hr_user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    jobs = relationship("Job", back_populates="company")


class Job(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"))
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    required_skills = Column(JSON, default=[])   # ["Python", "Docker", ...]
    salary = Column(String, nullable=True)
    location = Column(String, nullable=True)
    job_type = Column(String, default="fulltime") # fulltime/parttime/remote/internship
    experience_level = Column(String, default="fresher")
    deadline = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    auto_apply_threshold = Column(Float, default=75.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    company = relationship("Company", back_populates="jobs")
    applications = relationship("Application", back_populates="job")


class Resume(Base):
    __tablename__ = "resumes"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    file_path = Column(String, nullable=True)
    parsed_text = Column(Text, nullable=True)
    resume_score = Column(Float, nullable=True)
    ats_score = Column(Float, nullable=True)
    sentiment_score = Column(Float, nullable=True)
    suggestions = Column(JSON, default=[])
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="resumes")


class Application(Base):
    __tablename__ = "applications"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    job_id = Column(Integer, ForeignKey("jobs.id"))
    match_score = Column(Float, nullable=True)
    matched_skills = Column(JSON, default=[])
    missing_skills = Column(JSON, default=[])
    status = Column(String, default="applied")  # applied/shortlisted/interview/offered/rejected
    is_auto_applied = Column(Boolean, default=False)
    applied_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="applications")
    job = relationship("Job", back_populates="applications")


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    message = Column(String, nullable=False)
    type = Column(String, default="info")   # info/match/status/alert
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="notifications")


class SkillGapLog(Base):
    __tablename__ = "skill_gap_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    job_id = Column(Integer, ForeignKey("jobs.id"))
    missing_skills = Column(JSON, default=[])
    suggested_courses = Column(JSON, default=[])
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class SavedJob(Base):
    __tablename__ = "saved_jobs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    job_id = Column(Integer, ForeignKey("jobs.id"))
    saved_at = Column(DateTime(timezone=True), server_default=func.now())

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"))
    sender_id = Column(Integer, ForeignKey("users.id"))
    receiver_id = Column(Integer, ForeignKey("users.id"))
    content = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())

class InterviewSchedule(Base):
    __tablename__ = "interview_schedules"
    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"))
    job_id = Column(Integer, ForeignKey("jobs.id"))
    student_id = Column(Integer, ForeignKey("users.id"))
    hr_id = Column(Integer, ForeignKey("users.id"))
    interview_date = Column(String, nullable=False)
    interview_time = Column(String, nullable=False)
    interview_mode = Column(String, default="online")
    meeting_link = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    status = Column(String, default="scheduled")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ProfileView(Base):
    __tablename__ = "profile_views"
    id = Column(Integer, primary_key=True, index=True)
    viewed_user_id = Column(Integer, ForeignKey("users.id"))
    viewer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    viewed_at = Column(DateTime(timezone=True), server_default=func.now())

class JobAlertPreference(Base):
    __tablename__ = "job_alert_preferences"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    is_active = Column(Boolean, default=True)
    min_match_score = Column(Float, default=70.0)
    job_types = Column(JSON, default=[])
    keywords = Column(JSON, default=[])
    updated_at = Column(DateTime(timezone=True), server_default=func.now())