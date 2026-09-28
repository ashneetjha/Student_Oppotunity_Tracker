# OpportunityHub — Student Opportunity Tracker

OpportunityHub is a comprehensive, centralized opportunity discovery and tracking platform built for students and university administrators. It enables students to find internships, hackathons, workshops, certifications, and competitions, track application statuses, bookmark opportunities, and monitor upcoming deadlines. Administrators can publish, update, and manage opportunities through an integrated management portal.

---

## 🛠️ Technology Stack

- **Frontend:** HTML5, Modern Vanilla CSS, Responsive Grid/Flexbox Layouts, Modular Vanilla JavaScript ES6 Client.
- **Backend:** Python 3.11+, FastAPI, Uvicorn (ASGI server).
- **Database:** SQLAlchemy 2.0 ORM with SQLite (PostgreSQL compatible without schema changes).
- **Security & Auth:** JWT (JSON Web Tokens via PyJWT) with native Bcrypt password hashing.
- **Data Validation:** Pydantic v2 schemas and request models.
- **API Documentation:** Interactive OpenAPI & Swagger UI.

---

## 🚀 How to Run the Application

### 1. Start the Backend API Server

Open a terminal in the project root:

```bash
# Navigate to the project root
cd /path/to/Student_Opportunity_Tracker_Frontend

# Create and activate virtual environment (if not already created)
python3 -m venv backend/venv
source backend/venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Seed the database with demo users and realistic opportunities
PYTHONPATH=. python backend/seed.py

# Launch the FastAPI server with Uvicorn
PYTHONPATH=. uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

- API Base URL: `http://127.0.0.1:8000`
- Interactive Swagger API Documentation: `http://127.0.0.1:8000/docs`
- OpenAPI JSON Spec: `http://127.0.0.1:8000/openapi.json`

---

### 2. Start the Frontend

You can serve the frontend via any static file server (VS Code Live Server or Python HTTP Server):

```bash
# In another terminal window in the project root:
python3 -m http.server 3000
```

Open your browser to:
👉 **`http://localhost:3000/index.html`** or **`http://localhost:3000/login.html`**

---

## 🔑 Demo Accounts

| Role | Email | Password | Access / Features |
| :--- | :--- | :--- | :--- |
| **Student** | `student@example.com` | `Student@123` | Dashboard, Browse, Search, Filters, Bookmarks, Apply, Deadlines, Profile |
| **Student 2** | `student2@example.com` | `Student@123` | Secondary student account for multi-user testing |
| **Admin** | `admin@example.com` | `Admin@123` | Admin Portal, Add/Edit/Delete Opportunities, Admin Analytics |

---

## 🧪 Running Automated Tests

Run the complete backend test suite using pytest:

```bash
source backend/venv/bin/activate
PYTHONPATH=. pytest tests/test_backend.py -v
```

All 10 test modules cover health checks, user registration, JWT authentication, opportunity filtering, bookmarking, status transitions, student dashboard metrics, and admin CRUD security.

---

## 📁 Repository Structure

```
├── admin.html               # Admin management portal & opportunity CRUD
├── applications.html        # Student application status tracker & tabs
├── bookmarks.html           # Bookmarked opportunities view
├── dashboard.html           # Personalized student dashboard & KPI widgets
├── deadlines.html           # Upcoming deadline tracker sorted by urgency
├── explore.html             # Multi-filter search & opportunity discovery
├── index.html               # Landing page with hero section & platform stats
├── login.html               # User authentication login page
├── opportunity.html         # Opportunity detailed view & application action
├── profile.html             # Student profile management
├── register.html            # New student registration form
├── css/
│   └── style.css            # Unified responsive stylesheet
├── js/
│   └── app.js               # Central frontend API client & state controller
├── backend/
│   ├── .env                 # Active local environment configuration
│   ├── .env.example         # Template configuration
│   ├── requirements.txt     # Python backend dependencies
│   ├── seed.py              # Database seeding script with realistic data
│   └── app/
│       ├── main.py          # FastAPI application & middleware configuration
│       ├── config.py        # Pydantic Settings & CORS rules
│       ├── database.py      # SQLAlchemy engine & session factory
│       ├── models/          # 6 Database tables (User, Opportunity, Skill, etc.)
│       ├── schemas/         # Pydantic request & response models
│       ├── routers/         # REST API routers (auth, opps, bookmarks, apps, etc.)
│       ├── services/        # Business logic & opportunity formatting
│       ├── dependencies/    # JWT token verification & role enforcement
│       └── utils/           # Bcrypt password hashing & JWT utilities
└── tests/
    └── test_backend.py      # Pytest automated test suite
```

---

## 🔮 Future AI Roadmap

AI functionality is intentionally kept as an extensible placeholder for this prototype:
- `GET /api/ai/recommendations` — Placeholder for intelligent skill matching & candidate ranking.
- `POST /api/ai/match` — Extension point for LLM-powered resume vs. opportunity evaluation.
- `POST /api/ai/summarize` — Extension point for automated opportunity synopsis.
