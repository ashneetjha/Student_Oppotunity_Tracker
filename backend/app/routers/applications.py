from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone
from backend.app.database import get_db
from backend.app.models import Application, Opportunity, User, Bookmark
from backend.app.schemas import ApplicationCreate, ApplicationStatusUpdate, ApplicationOut
from backend.app.dependencies.auth import get_current_user
from backend.app.services.opportunity_service import format_opportunity_out

router = APIRouter(prefix="/api/applications", tags=["Applications"])

VALID_STATUSES = {"Interested", "Applied", "Shortlisted", "Completed"}

@router.get("", response_model=List[ApplicationOut])
def list_applications(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status (Interested/Applied/Shortlisted/Completed)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Application).filter(Application.user_id == current_user.user_id)
    if status_filter and status_filter.strip() and status_filter.strip().lower() != "all":
        query = query.filter(Application.status.ilike(status_filter.strip()))

    apps = query.order_by(Application.updated_at.desc()).all()

    user_bookmarks_set = {
        b.opportunity_id for b in db.query(Bookmark).filter(Bookmark.user_id == current_user.user_id).all()
    }
    user_apps_map = {a.opportunity_id: a.status for a in apps}

    result = []
    for app in apps:
        opp_out = None
        if app.opportunity:
            opp_out = format_opportunity_out(
                app.opportunity,
                current_user_id=current_user.user_id,
                user_bookmarks_set=user_bookmarks_set,
                user_applications_map=user_apps_map
            )
        result.append(
            ApplicationOut(
                application_id=app.application_id,
                user_id=app.user_id,
                opportunity_id=app.opportunity_id,
                status=app.status,
                applied_at=app.applied_at,
                updated_at=app.updated_at,
                opportunity=opp_out
            )
        )
    return result

@router.post("/{opportunity_id}", response_model=ApplicationOut, status_code=status.HTTP_201_CREATED)
def create_or_update_application(
    opportunity_id: int,
    app_data: ApplicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    opp = db.query(Opportunity).filter(Opportunity.opportunity_id == opportunity_id).first()
    if not opp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Opportunity {opportunity_id} not found"
        )

    status_val = app_data.status.strip() if app_data.status else "Applied"
    if status_val not in VALID_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status '{status_val}'. Valid statuses are: {', '.join(sorted(VALID_STATUSES))}"
        )

    app = db.query(Application).filter(
        Application.user_id == current_user.user_id,
        Application.opportunity_id == opportunity_id
    ).first()

    now = datetime.now(timezone.utc)
    if app:
        app.status = status_val
        app.updated_at = now
    else:
        app = Application(
            user_id=current_user.user_id,
            opportunity_id=opportunity_id,
            status=status_val,
            applied_at=now,
            updated_at=now
        )
        db.add(app)

    db.commit()
    db.refresh(app)

    opp_out = format_opportunity_out(opp, current_user_id=current_user.user_id)
    return ApplicationOut(
        application_id=app.application_id,
        user_id=app.user_id,
        opportunity_id=app.opportunity_id,
        status=app.status,
        applied_at=app.applied_at,
        updated_at=app.updated_at,
        opportunity=opp_out
    )

@router.put("/{application_id}", response_model=ApplicationOut)
def update_application_status(
    application_id: int,
    status_update: ApplicationStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    app = db.query(Application).filter(Application.application_id == application_id).first()
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application {application_id} not found"
        )

    # Prevent another user from modifying this application
    if app.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to modify another user's application"
        )

    status_val = status_update.status.strip()
    if status_val not in VALID_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status '{status_val}'. Valid statuses are: {', '.join(sorted(VALID_STATUSES))}"
        )

    app.status = status_val
    app.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(app)

    opp_out = format_opportunity_out(app.opportunity, current_user_id=current_user.user_id) if app.opportunity else None
    return ApplicationOut(
        application_id=app.application_id,
        user_id=app.user_id,
        opportunity_id=app.opportunity_id,
        status=app.status,
        applied_at=app.applied_at,
        updated_at=app.updated_at,
        opportunity=opp_out
    )
