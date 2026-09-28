from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date
from backend.app.database import get_db
from backend.app.models import Opportunity, Application, Bookmark, User, Skill
from backend.app.schemas import (
    StudentDashboardResponse,
    StudentDashboardStats,
    AdminDashboardResponse,
    AdminDashboardStats,
    ApplicationOut
)
from backend.app.dependencies.auth import get_current_user, require_admin
from backend.app.services.opportunity_service import format_opportunity_out, calculate_days_remaining

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

@router.get("/student", response_model=StudentDashboardResponse)
def get_student_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Bookmarks
    bookmarks = db.query(Bookmark).filter(Bookmark.user_id == current_user.user_id).all()
    user_bookmarks_set = {b.opportunity_id for b in bookmarks}

    # Applications
    apps = db.query(Application).filter(Application.user_id == current_user.user_id).all()
    user_apps_map = {a.opportunity_id: a.status for a in apps}

    total_apps = len(apps)
    interested_cnt = sum(1 for a in apps if a.status == "Interested")
    applied_cnt = sum(1 for a in apps if a.status == "Applied")
    shortlisted_cnt = sum(1 for a in apps if a.status == "Shortlisted")
    completed_cnt = sum(1 for a in apps if a.status == "Completed")

    # All active opportunities sorted by deadline
    active_opps = db.query(Opportunity).filter(Opportunity.status.ilike("Active")).all()
    
    # Calculate days remaining for each
    opps_with_days = []
    for opp in active_opps:
        days = calculate_days_remaining(opp.deadline)
        opps_with_days.append((opp, days))

    # Sort by nearest deadline
    opps_with_days.sort(key=lambda x: x[1])

    upcoming_deadlines_count = sum(1 for _, days in opps_with_days if days <= 30)

    # Top 4 nearest deadlines for dashboard panel
    upcoming_deadlines = [
        format_opportunity_out(
            opp,
            current_user_id=current_user.user_id,
            user_bookmarks_set=user_bookmarks_set,
            user_applications_map=user_apps_map
        )
        for opp, _ in opps_with_days[:4]
    ]

    # Rule-based recommendations (simple matching on popular student skills)
    recommended_list = [
        format_opportunity_out(
            opp,
            current_user_id=current_user.user_id,
            user_bookmarks_set=user_bookmarks_set,
            user_applications_map=user_apps_map
        )
        for opp, _ in opps_with_days[:3]
    ]

    # Recent applications (latest 5)
    recent_apps_sorted = sorted(apps, key=lambda a: a.updated_at, reverse=True)[:5]
    recent_applications = [
        ApplicationOut(
            application_id=a.application_id,
            user_id=a.user_id,
            opportunity_id=a.opportunity_id,
            status=a.status,
            applied_at=a.applied_at,
            updated_at=a.updated_at,
            opportunity=format_opportunity_out(
                a.opportunity,
                current_user_id=current_user.user_id,
                user_bookmarks_set=user_bookmarks_set,
                user_applications_map=user_apps_map
            ) if a.opportunity else None
        )
        for a in recent_apps_sorted
    ]

    stats = StudentDashboardStats(
        bookmarks=len(bookmarks),
        applications=total_apps,
        interested=interested_cnt,
        applied=applied_cnt,
        shortlisted=shortlisted_cnt,
        completed=completed_cnt,
        upcoming_deadlines_count=upcoming_deadlines_count
    )

    return StudentDashboardResponse(
        stats=stats,
        upcoming_deadlines=upcoming_deadlines,
        recent_applications=recent_applications,
        recommended=recommended_list
    )

@router.get("/admin", response_model=AdminDashboardResponse)
def get_admin_dashboard(
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    total_opps = db.query(Opportunity).count()
    total_internships = db.query(Opportunity).filter(Opportunity.type.ilike("Internship")).count()
    total_hackathons = db.query(Opportunity).filter(Opportunity.type.ilike("Hackathon")).count()
    total_workshops = db.query(Opportunity).filter(Opportunity.type.ilike("Workshop")).count()
    total_certifications = db.query(Opportunity).filter(Opportunity.type.ilike("Certification")).count()
    total_competitions = db.query(Opportunity).filter(Opportunity.type.ilike("Competition")).count()

    active_opps = db.query(Opportunity).filter(Opportunity.status.ilike("Active")).count()
    closed_opps = db.query(Opportunity).filter(Opportunity.status.ilike("Closed")).count()

    total_students = db.query(User).filter(User.role == "student").count()
    total_applications = db.query(Application).count()

    stats = AdminDashboardStats(
        total_opportunities=total_opps,
        total_internships=total_internships,
        total_hackathons=total_hackathons,
        total_workshops=total_workshops,
        total_certifications=total_certifications,
        total_competitions=total_competitions,
        active_opportunities=active_opps,
        closed_opportunities=closed_opps,
        total_students=total_students,
        total_applications=total_applications
    )

    recent_opps = db.query(Opportunity).order_by(Opportunity.created_at.desc()).limit(10).all()
    recent_formatted = [
        format_opportunity_out(opp, current_user_id=admin_user.user_id)
        for opp in recent_opps
    ]

    return AdminDashboardResponse(
        stats=stats,
        recent_opportunities=recent_formatted
    )
