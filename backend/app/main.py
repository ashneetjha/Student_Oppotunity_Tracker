from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.config import settings
from backend.app.database import engine, Base
from backend.app.routers import (
    auth,
    opportunities,
    bookmarks,
    applications,
    dashboard,
    skills,
    ai_placeholder
)

# Safe database initialization: creates tables if they don't exist
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="OpportunityHub API",
    description="Backend REST API for Student Opportunity Tracker Hackathon Prototype",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Hackathon friendly for multiple dev origins / live-server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router)
app.include_router(opportunities.router)
app.include_router(bookmarks.router)
app.include_router(applications.router)
app.include_router(dashboard.router)
app.include_router(skills.router)
app.include_router(ai_placeholder.router)

@app.get("/", tags=["Health"])
def root():
    return {
        "status": "healthy",
        "service": "OpportunityHub API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/api/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "database": "connected"
    }
