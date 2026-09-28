from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from backend.app.database import get_db
from backend.app.models import Bookmark, Opportunity, User, Application
from backend.app.schemas import OpportunityOut
from backend.app.dependencies.auth import get_current_user
from backend.app.services.opportunity_service import format_opportunity_out

router = APIRouter(prefix="/api/bookmarks", tags=["Bookmarks"])

@router.get("", response_model=List[OpportunityOut])
def list_bookmarks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    bookmarks = db.query(Bookmark).filter(Bookmark.user_id == current_user.user_id).all()
    user_bookmarks_set = {b.opportunity_id for b in bookmarks}
    apps = db.query(Application).filter(Application.user_id == current_user.user_id).all()
    user_apps_map = {a.opportunity_id: a.status for a in apps}

    results = []
    for b in bookmarks:
        if b.opportunity:
            results.append(
                format_opportunity_out(
                    b.opportunity,
                    current_user_id=current_user.user_id,
                    user_bookmarks_set=user_bookmarks_set,
                    user_applications_map=user_apps_map
                )
            )
    return results

@router.post("/{opportunity_id}", status_code=status.HTTP_201_CREATED)
def add_bookmark(
    opportunity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    opp = db.query(Opportunity).filter(Opportunity.opportunity_id == opportunity_id).first()
    if not opp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Opportunity {opportunity_id} not found"
        )

    existing = db.query(Bookmark).filter(
        Bookmark.user_id == current_user.user_id,
        Bookmark.opportunity_id == opportunity_id
    ).first()
    if existing:
        return {"message": "Already bookmarked", "is_bookmarked": True}

    bookmark = Bookmark(user_id=current_user.user_id, opportunity_id=opportunity_id)
    db.add(bookmark)
    db.commit()
    return {"message": "Opportunity bookmarked successfully", "is_bookmarked": True}

@router.delete("/{opportunity_id}", status_code=status.HTTP_200_OK)
def remove_bookmark(
    opportunity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    bookmark = db.query(Bookmark).filter(
        Bookmark.user_id == current_user.user_id,
        Bookmark.opportunity_id == opportunity_id
    ).first()
    if bookmark:
        db.delete(bookmark)
        db.commit()
    return {"message": "Bookmark removed", "is_bookmarked": False}

@router.post("/{opportunity_id}/toggle", status_code=status.HTTP_200_OK)
def toggle_bookmark(
    opportunity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    opp = db.query(Opportunity).filter(Opportunity.opportunity_id == opportunity_id).first()
    if not opp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Opportunity {opportunity_id} not found"
        )

    bookmark = db.query(Bookmark).filter(
        Bookmark.user_id == current_user.user_id,
        Bookmark.opportunity_id == opportunity_id
    ).first()

    if bookmark:
        db.delete(bookmark)
        db.commit()
        return {"is_bookmarked": False, "message": "Bookmark removed"}
    else:
        new_bm = Bookmark(user_id=current_user.user_id, opportunity_id=opportunity_id)
        db.add(new_bm)
        db.commit()
        return {"is_bookmarked": True, "message": "Bookmarked successfully"}
