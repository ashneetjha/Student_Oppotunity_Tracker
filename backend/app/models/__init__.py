from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from backend.app.database import Base

def utcnow():
    return datetime.now(timezone.utc)

# TABLE 4: opportunity_skills (Association Table)
opportunity_skills = Table(
    "opportunity_skills",
    Base.metadata,
    Column("opportunity_id", Integer, ForeignKey("opportunities.opportunity_id", ondelete="CASCADE"), primary_key=True),
    Column("skill_id", Integer, ForeignKey("skills.skill_id", ondelete="CASCADE"), primary_key=True)
)

# TABLE 1: users
class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    college = Column(String(200), nullable=False)
    role = Column(String(20), nullable=False, default="student")  # 'student' | 'admin'
    bio = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    opportunities = relationship("Opportunity", back_populates="creator")
    bookmarks = relationship("Bookmark", back_populates="user", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="user", cascade="all, delete-orphan")

# TABLE 3: skills
class Skill(Base):
    __tablename__ = "skills"

    skill_id = Column(Integer, primary_key=True, index=True)
    skill_name = Column(String(50), unique=True, index=True, nullable=False)

    opportunities = relationship("Opportunity", secondary=opportunity_skills, back_populates="skills")

# TABLE 2: opportunities
class Opportunity(Base):
    __tablename__ = "opportunities"

    opportunity_id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, index=True)
    organization = Column(String(200), nullable=False, index=True)
    type = Column(String(50), nullable=False, index=True)  # Internship, Workshop, Hackathon, Certification, Competition
    description = Column(Text, nullable=False)
    location = Column(String(100), nullable=False, default="Online")
    deadline = Column(String(20), nullable=False)  # ISO Date YYYY-MM-DD
    eligibility = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="Active")  # Active, Closed
    created_by = Column(Integer, ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    creator = relationship("User", back_populates="opportunities")
    skills = relationship("Skill", secondary=opportunity_skills, back_populates="opportunities")
    bookmarks = relationship("Bookmark", back_populates="opportunity", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="opportunity", cascade="all, delete-orphan")

# TABLE 5: bookmarks
class Bookmark(Base):
    __tablename__ = "bookmarks"

    bookmark_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    opportunity_id = Column(Integer, ForeignKey("opportunities.opportunity_id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    user = relationship("User", back_populates="bookmarks")
    opportunity = relationship("Opportunity", back_populates="bookmarks")

# TABLE 6: applications
class Application(Base):
    __tablename__ = "applications"

    application_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    opportunity_id = Column(Integer, ForeignKey("opportunities.opportunity_id", ondelete="CASCADE"), nullable=False)
    status = Column(String(30), nullable=False, default="Interested")  # Interested, Applied, Shortlisted, Completed
    applied_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    user = relationship("User", back_populates="applications")
    opportunity = relationship("Opportunity", back_populates="applications")
