from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from backend.app.database import get_db
from backend.app.models import User, Opportunity
from backend.app.dependencies.auth import get_current_user_optional

router = APIRouter(prefix="/api/ai", tags=["AI Placeholder"])

@router.get("/recommendations")
def get_recommendations():
    """
    Extension point for future AI recommendation engine.
    Currently disabled intentionally as AI is reserved for the next phase.
    """
    return {
        "enabled": False,
        "message": "AI functionality is reserved for the next phase.",
        "results": []
    }

@router.post("/match")
def match_opportunity():
    """
    Extension point for future LLM-based profile and resume matching.
    """
    return {
        "enabled": False,
        "message": "AI functionality is reserved for the next phase.",
        "results": []
    }

@router.post("/summarize")
def summarize_opportunity():
    """
    Extension point for future opportunity summarization.
    """
    return {
        "enabled": False,
        "message": "AI functionality is reserved for the next phase.",
        "results": []
    }
