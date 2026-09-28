from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc
from typing import List, Optional
from datetime import datetime, date, timedelta
from backend.app.database import get_db
from backend.app.models import Opportunity, Skill, User, Bookmark, Application
from backend.app.schemas import OpportunityCreate, OpportunityUpdate, OpportunityOut
from backend.app.dependencies.auth import get_current_user_optional, require_admin
from backend.app.services.opportunity_service import format_opportunity_out, calculate_days_remaining

router = APIRouter(prefix="/api/opportunities", tags=["Opportunities"])

def get_or_create_skill(db: Session, skill_name: str) -> Skill:
    normalized = skill_name.strip()
    skill = db.query(Skill).filter(Skill.skill_name.ilike(normalized)).first()
    if not skill:
        skill = Skill(skill_name=normalized)
        db.add(skill)
        db.commit()
        db.refresh(skill)
    return skill

@router.get("", response_model=List[OpportunityOut])
def list_opportunities(
    search: Optional[str] = Query(None, description="Search by title, organization, description, or skill"),
    type: Optional[str] = Query(None, description="Opportunity type"),
    skill: Optional[str] = Query(None, description="Required skill name"),
    deadline: Optional[int] = Query(None, description="Max days remaining (e.g. 7 or 30)"),
    status_filter: Optional[str] = Query(None, alias="status", description="Status (Active/Closed)"),
    sort: Optional[str] = Query(None, description="Sort order: newest, deadline_asc, deadline_desc"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    query = db.query(Opportunity)

    # Filter status
    if status_filter:
        query = query.filter(Opportunity.status.ilike(status_filter.strip()))

    # Filter type
    if type and type.strip():
        query = query.filter(Opportunity.type.ilike(type.strip()))

    # Filter skill
    if skill and skill.strip():
        query = query.filter(Opportunity.skills.any(Skill.skill_name.ilike(skill.strip())))

    # Search keyword
    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Opportunity.title.ilike(term),
                Opportunity.organization.ilike(term),
                Opportunity.description.ilike(term),
                Opportunity.skills.any(Skill.skill_name.ilike(term))
            )
        )

    # Sort
    if sort == "newest":
        query = query.order_by(desc(Opportunity.created_at))
    elif sort == "deadline_desc":
        query = query.order_by(desc(Opportunity.deadline))
    else:
        # Default deadline ascending
        query = query.order_by(asc(Opportunity.deadline))

    results = query.all()

    # Apply in-memory deadline filter if days parameter provided
    if deadline and deadline > 0:
        results = [o for o in results if calculate_days_remaining(o.deadline) <= deadline]

    # Pre-fetch user's bookmarks and applications if logged in
    user_bookmarks_set = set()
    user_apps_map = {}
    if current_user:
        bookmarks = db.query(Bookmark).filter(Bookmark.user_id == current_user.user_id).all()
        user_bookmarks_set = {b.opportunity_id for b in bookmarks}
        apps = db.query(Application).filter(Application.user_id == current_user.user_id).all()
        user_apps_map = {a.opportunity_id: a.status for a in apps}

    return [
        format_opportunity_out(
            o,
            current_user_id=current_user.user_id if current_user else None,
            user_bookmarks_set=user_bookmarks_set,
            user_applications_map=user_apps_map
        )
        for o in results
    ]

@router.get("/{opportunity_id}", response_model=OpportunityOut)
def get_opportunity(
    opportunity_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    opp = db.query(Opportunity).filter(Opportunity.opportunity_id == opportunity_id).first()
    if not opp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Opportunity with ID {opportunity_id} not found"
        )

    user_bookmarks_set = None
    user_apps_map = None
    if current_user:
        user_bookmarks_set = {
            b.opportunity_id for b in db.query(Bookmark).filter(Bookmark.user_id == current_user.user_id).all()
        }
        user_apps_map = {
            a.opportunity_id: a.status for a in db.query(Application).filter(Application.user_id == current_user.user_id).all()
        }

    return format_opportunity_out(
        opp,
        current_user_id=current_user.user_id if current_user else None,
        user_bookmarks_set=user_bookmarks_set,
        user_applications_map=user_apps_map
    )

@router.post("", response_model=OpportunityOut, status_code=status.HTTP_201_CREATED)
def create_opportunity(
    opp_data: OpportunityCreate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    skills_objects = []
    for s_name in opp_data.skills:
        if s_name.strip():
            skills_objects.append(get_or_create_skill(db, s_name.strip()))

    new_opp = Opportunity(
        title=opp_data.title.strip(),
        organization=opp_data.organization.strip(),
        type=opp_data.type.strip(),
        description=opp_data.description.strip(),
        location=opp_data.location.strip() if opp_data.location else "Online",
        deadline=opp_data.deadline.strip(),
        eligibility=opp_data.eligibility.strip() if opp_data.eligibility else "All students eligible",
        status=opp_data.status.strip() if opp_data.status else "Active",
        created_by=admin_user.user_id,
        skills=skills_objects
    )
    db.add(new_opp)
    db.commit()
    db.refresh(new_opp)

    return format_opportunity_out(new_opp, current_user_id=admin_user.user_id)

@router.put("/{opportunity_id}", response_model=OpportunityOut)
def update_opportunity(
    opportunity_id: int,
    opp_data: OpportunityUpdate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    opp = db.query(Opportunity).filter(Opportunity.opportunity_id == opportunity_id).first()
    if not opp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Opportunity with ID {opportunity_id} not found"
        )

    if opp_data.title is not None:
        opp.title = opp_data.title.strip()
    if opp_data.organization is not None:
        opp.organization = opp_data.organization.strip()
    if opp_data.type is not None:
        opp.type = opp_data.type.strip()
    if opp_data.description is not None:
        opp.description = opp_data.description.strip()
    if opp_data.location is not None:
        opp.location = opp_data.location.strip()
    if opp_data.deadline is not None:
        opp.deadline = opp_data.deadline.strip()
    if opp_data.eligibility is not None:
        opp.eligibility = opp_data.eligibility.strip()
    if opp_data.status is not None:
        opp.status = opp_data.status.strip()

    if opp_data.skills is not None:
        skills_objects = []
        for s_name in opp_data.skills:
            if s_name.strip():
                skills_objects.append(get_or_create_skill(db, s_name.strip()))
        opp.skills = skills_objects

    db.commit()
    db.refresh(opp)
    return format_opportunity_out(opp, current_user_id=admin_user.user_id)

@router.delete("/{opportunity_id}", status_code=status.HTTP_200_OK)
def delete_opportunity(
    opportunity_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    opp = db.query(Opportunity).filter(Opportunity.opportunity_id == opportunity_id).first()
    if not opp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Opportunity with ID {opportunity_id} not found"
        )

    db.delete(opp)
    db.commit()
    return {"message": f"Opportunity {opportunity_id} successfully deleted", "opportunity_id": opportunity_id}
