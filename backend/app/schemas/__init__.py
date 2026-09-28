from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# --- Auth Schemas ---
class UserRegister(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)
    college: str = Field(..., min_length=2, max_length=200)
    role: Optional[str] = "student"
    bio: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    college: Optional[str] = None
    bio: Optional[str] = None

class UserOut(BaseModel):
    user_id: int
    name: str
    email: str
    college: str
    role: str
    bio: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut

# --- Skill Schemas ---
class SkillCreate(BaseModel):
    skill_name: str = Field(..., min_length=1, max_length=50)

class SkillOut(BaseModel):
    skill_id: int
    skill_name: str

    class Config:
        from_attributes = True

# --- Opportunity Schemas ---
class OpportunityBase(BaseModel):
    title: str = Field(..., min_length=2, max_length=200)
    organization: str = Field(..., min_length=1, max_length=200)
    type: str = Field(..., min_length=2, max_length=50)  # Internship, Workshop, Hackathon, Certification, Competition
    description: str = Field(..., min_length=5)
    location: Optional[str] = "Online"
    deadline: str  # YYYY-MM-DD
    eligibility: Optional[str] = "All students eligible"
    status: Optional[str] = "Active"
    skills: List[str] = []

class OpportunityCreate(OpportunityBase):
    pass

class OpportunityUpdate(BaseModel):
    title: Optional[str] = None
    organization: Optional[str] = None
    type: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    deadline: Optional[str] = None
    eligibility: Optional[str] = None
    status: Optional[str] = None
    skills: Optional[List[str]] = None

class OpportunityOut(BaseModel):
    # Field names matching both frontend expectations (id, org, desc, days, logo) and backend contracts
    opportunity_id: int
    id: int
    title: str
    organization: str
    org: str
    type: str
    description: str
    desc: str
    location: str
    deadline: str
    days: int
    eligibility: Optional[str] = None
    status: str
    skills: List[str]
    logo: str
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None
    is_bookmarked: Optional[bool] = False
    application_status: Optional[str] = None

    class Config:
        from_attributes = True

# --- Bookmark Schemas ---
class BookmarkOut(BaseModel):
    bookmark_id: int
    user_id: int
    opportunity_id: int
    created_at: datetime
    opportunity: Optional[OpportunityOut] = None

    class Config:
        from_attributes = True

# --- Application Schemas ---
class ApplicationCreate(BaseModel):
    status: Optional[str] = "Interested"

class ApplicationStatusUpdate(BaseModel):
    status: str  # Interested, Applied, Shortlisted, Completed

class ApplicationOut(BaseModel):
    application_id: int
    user_id: int
    opportunity_id: int
    status: str
    applied_at: datetime
    updated_at: datetime
    opportunity: Optional[OpportunityOut] = None

    class Config:
        from_attributes = True

# --- Dashboard Schemas ---
class StudentDashboardStats(BaseModel):
    bookmarks: int
    applications: int
    interested: int
    applied: int
    shortlisted: int
    completed: int
    upcoming_deadlines_count: int

class StudentDashboardResponse(BaseModel):
    stats: StudentDashboardStats
    upcoming_deadlines: List[OpportunityOut]
    recent_applications: List[ApplicationOut]
    recommended: List[OpportunityOut]

class AdminDashboardStats(BaseModel):
    total_opportunities: int
    total_internships: int
    total_hackathons: int
    total_workshops: int
    total_certifications: int
    total_competitions: int
    active_opportunities: int
    closed_opportunities: int
    total_students: int
    total_applications: int

class AdminDashboardResponse(BaseModel):
    stats: AdminDashboardStats
    recent_opportunities: List[OpportunityOut]
