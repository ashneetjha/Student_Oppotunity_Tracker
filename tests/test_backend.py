import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from backend.app.main import app
from backend.app.database import Base, get_db
from backend.app.models import User, Opportunity, Skill
from backend.app.utils.security import hash_password

# Setup in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    # Seed admin and student
    admin = User(
        name="Admin Test",
        email="admin@test.com",
        password_hash=hash_password("Admin@123"),
        college="Tech Admin Uni",
        role="admin"
    )
    student = User(
        name="Student Test",
        email="student@test.com",
        password_hash=hash_password("Student@123"),
        college="Tech Student Uni",
        role="student"
    )
    skill_py = Skill(skill_name="Python")
    skill_react = Skill(skill_name="React")
    opp = Opportunity(
        title="Software Intern",
        organization="Google",
        type="Internship",
        description="Great internship opportunity",
        location="Remote",
        deadline="2026-10-15",
        status="Active",
        skills=[skill_py, skill_react]
    )
    db.add_all([admin, student, skill_py, skill_react, opp])
    db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)

client = TestClient(app)

def test_health_check():
    res = client.get("/")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"

    res_health = client.get("/api/health")
    assert res_health.status_code == 200
    assert res_health.json()["database"] == "connected"

def test_auth_register_and_duplicate():
    # Register new user
    res = client.post("/api/auth/register", json={
        "name": "New User",
        "email": "newuser@test.com",
        "password": "Password@123",
        "college": "Global Tech College"
    })
    assert res.status_code == 201
    data = res.json()
    assert "access_token" in data
    assert data["user"]["email"] == "newuser@test.com"

    # Try duplicate registration
    res_dup = client.post("/api/auth/register", json={
        "name": "New User",
        "email": "newuser@test.com",
        "password": "Password@123",
        "college": "Global Tech College"
    })
    assert res_dup.status_code == 400
    assert "already exists" in res_dup.json()["detail"]

def test_auth_login_and_me():
    # Login student
    res = client.post("/api/auth/login", json={
        "email": "student@test.com",
        "password": "Student@123"
    })
    assert res.status_code == 200
    token = res.json()["access_token"]
    assert token

    # Check /me with token
    headers = {"Authorization": f"Bearer {token}"}
    res_me = client.get("/api/auth/me", headers=headers)
    assert res_me.status_code == 200
    assert res_me.json()["email"] == "student@test.com"

def test_list_and_filter_opportunities():
    res = client.get("/api/opportunities")
    assert res.status_code == 200
    opps = res.json()
    assert len(opps) >= 1
    assert opps[0]["title"] == "Software Intern"

    # Search filter
    res_search = client.get("/api/opportunities?search=Google")
    assert res_search.status_code == 200
    assert len(res_search.json()) >= 1

    # Skill filter
    res_skill = client.get("/api/opportunities?skill=Python")
    assert res_skill.status_code == 200
    assert len(res_skill.json()) >= 1

    # Type filter
    res_type = client.get("/api/opportunities?type=Internship")
    assert res_type.status_code == 200
    assert len(res_type.json()) >= 1

def test_opportunity_detail_and_not_found():
    res = client.get("/api/opportunities/1")
    assert res.status_code == 200
    assert res.json()["title"] == "Software Intern"

    res_nf = client.get("/api/opportunities/9999")
    assert res_nf.status_code == 404

def test_bookmarks_flow():
    # Login student
    res_login = client.post("/api/auth/login", json={
        "email": "student@test.com",
        "password": "Student@123"
    })
    token = res_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Add bookmark
    res_add = client.post("/api/bookmarks/1", headers=headers)
    assert res_add.status_code == 201

    # List bookmarks
    res_list = client.get("/api/bookmarks", headers=headers)
    assert res_list.status_code == 200
    bms = res_list.json()
    assert len(bms) >= 1
    assert bms[0]["opportunity_id"] == 1

    # Remove bookmark
    res_del = client.delete("/api/bookmarks/1", headers=headers)
    assert res_del.status_code == 200

    # Verify removed
    res_list2 = client.get("/api/bookmarks", headers=headers)
    assert len(res_list2.json()) == 0

def test_applications_flow():
    # Login student
    res_login = client.post("/api/auth/login", json={
        "email": "student@test.com",
        "password": "Student@123"
    })
    token = res_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Apply
    res_apply = client.post("/api/applications/1", json={"status": "Applied"}, headers=headers)
    assert res_apply.status_code == 201
    app_data = res_apply.json()
    app_id = app_data["application_id"]
    assert app_data["status"] == "Applied"

    # Update status
    res_update = client.put(f"/api/applications/{app_id}", json={"status": "Shortlisted"}, headers=headers)
    assert res_update.status_code == 200
    assert res_update.json()["status"] == "Shortlisted"

    # Invalid status rejection
    res_invalid = client.put(f"/api/applications/{app_id}", json={"status": "RandomStatus"}, headers=headers)
    assert res_invalid.status_code == 400

def test_student_dashboard():
    res_login = client.post("/api/auth/login", json={
        "email": "student@test.com",
        "password": "Student@123"
    })
    token = res_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/dashboard/student", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "stats" in data
    assert "upcoming_deadlines" in data
    assert "recent_applications" in data
    assert data["stats"]["applications"] >= 1

def test_admin_crud_and_dashboard():
    # Login student and attempt admin action -> 403
    res_stud = client.post("/api/auth/login", json={
        "email": "student@test.com",
        "password": "Student@123"
    })
    stud_token = res_stud.json()["access_token"]
    res_unauth = client.post("/api/opportunities", json={
        "title": "Unauthorized Opp",
        "organization": "Test",
        "type": "Workshop",
        "description": "...",
        "deadline": "2026-10-30"
    }, headers={"Authorization": f"Bearer {stud_token}"})
    assert res_unauth.status_code == 403

    # Login admin
    res_admin = client.post("/api/auth/login", json={
        "email": "admin@test.com",
        "password": "Admin@123"
    })
    admin_token = res_admin.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Admin Create Opportunity
    res_create = client.post("/api/opportunities", json={
        "title": "Cloud Workshop",
        "organization": "AWS Cloud",
        "type": "Workshop",
        "description": "Learn cloud hands on",
        "location": "Online",
        "deadline": "2026-11-10",
        "skills": ["AWS", "Cloud"]
    }, headers=admin_headers)
    assert res_create.status_code == 201
    created_id = res_create.json()["opportunity_id"]

    # Admin Update Opportunity
    res_update = client.put(f"/api/opportunities/{created_id}", json={
        "title": "Advanced Cloud Workshop"
    }, headers=admin_headers)
    assert res_update.status_code == 200
    assert res_update.json()["title"] == "Advanced Cloud Workshop"

    # Admin Dashboard
    res_dash = client.get("/api/dashboard/admin", headers=admin_headers)
    assert res_dash.status_code == 200
    assert res_dash.json()["stats"]["total_opportunities"] >= 2

    # Admin Delete Opportunity
    res_del = client.delete(f"/api/opportunities/{created_id}", headers=admin_headers)
    assert res_del.status_code == 200
    assert res_del.json()["opportunity_id"] == created_id

    # Verify deleted
    res_verify = client.get(f"/api/opportunities/{created_id}")
    assert res_verify.status_code == 404

def test_ai_placeholder():
    res = client.get("/api/ai/recommendations")
    assert res.status_code == 200
    assert res.json()["enabled"] is False
    assert "reserved for the next phase" in res.json()["message"]
