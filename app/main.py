from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.database import Base, engine
from app import models
from app.routes import (
    auth, profile, resume, jobs,
    notifications, applications, admin,
    company, saved_jobs, leaderboard,
    realtime, chat, live_match,
    interviews, analytics
)
import os

Base.metadata.create_all(bind=engine)

app = FastAPI(title="CareerBridge AI", version="1.0.0")

# Allow both local and production frontend
origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    os.getenv("FRONTEND_URL", ""),
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o for o in origins if o],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("uploads", exist_ok=True)

try:
    app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
except Exception:
    pass

app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(resume.router)
app.include_router(jobs.router)
app.include_router(notifications.router)
app.include_router(applications.router)
app.include_router(admin.router)
app.include_router(company.router)
app.include_router(saved_jobs.router)
app.include_router(leaderboard.router)
app.include_router(realtime.router)
app.include_router(chat.router)
app.include_router(live_match.router)
app.include_router(interviews.router)
app.include_router(analytics.router)

@app.get("/")
def root():
    return {"message": "CareerBridge AI backend running!"}