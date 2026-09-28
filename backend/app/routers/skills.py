from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from backend.app.database import get_db
from backend.app.models import Skill, User
from backend.app.schemas import SkillOut, SkillCreate
from backend.app.dependencies.auth import require_admin

router = APIRouter(prefix="/api/skills", tags=["Skills"])

@router.get("", response_model=List[SkillOut])
def list_skills(db: Session = Depends(get_db)):
    return db.query(Skill).order_by(Skill.skill_name.asc()).all()

@router.post("", response_model=SkillOut, status_code=status.HTTP_201_CREATED)
def create_skill(
    skill_data: SkillCreate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    name = skill_data.skill_name.strip()
    existing = db.query(Skill).filter(Skill.skill_name.ilike(name)).first()
    if existing:
        return existing
    new_skill = Skill(skill_name=name)
    db.add(new_skill)
    db.commit()
    db.refresh(new_skill)
    return new_skill
