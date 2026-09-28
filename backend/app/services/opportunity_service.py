from datetime import datetime, date
from typing import List, Optional
from backend.app.models import Opportunity, Skill, Bookmark, Application, User
from backend.app.schemas import OpportunityOut

def calculate_days_remaining(deadline_str: str) -> int:
    try:
        # Handles YYYY-MM-DD
        d = datetime.strptime(deadline_str.strip()[:10], "%Y-%m-%d").date()
        today = date.today()
        diff = (d - today).days
        return max(diff, 0)
    except Exception:
        return 0

def format_opportunity_out(
    opp: Opportunity,
    current_user_id: Optional[int] = None,
    user_bookmarks_set: Optional[set] = None,
    user_applications_map: Optional[dict] = None
) -> OpportunityOut:
    skills_list = [s.skill_name for s in opp.skills] if opp.skills else []
    logo_char = opp.organization[0].upper() if opp.organization else "O"
    days_left = calculate_days_remaining(opp.deadline)

    is_bookmarked = False
    if user_bookmarks_set is not None:
        is_bookmarked = opp.opportunity_id in user_bookmarks_set
    elif current_user_id is not None:
        is_bookmarked = any(b.user_id == current_user_id for b in opp.bookmarks)

    app_status = None
    if user_applications_map is not None:
        app_status = user_applications_map.get(opp.opportunity_id)
    elif current_user_id is not None:
        for a in opp.applications:
            if a.user_id == current_user_id:
                app_status = a.status
                break

    return OpportunityOut(
        opportunity_id=opp.opportunity_id,
        id=opp.opportunity_id,
        title=opp.title,
        organization=opp.organization,
        org=opp.organization,
        type=opp.type,
        description=opp.description,
        desc=opp.description,
        location=opp.location,
        deadline=opp.deadline,
        days=days_left,
        eligibility=opp.eligibility,
        status=opp.status,
        skills=skills_list,
        logo=logo_char,
        created_by=opp.created_by,
        created_at=opp.created_at,
        is_bookmarked=is_bookmarked,
        application_status=app_status
    )
