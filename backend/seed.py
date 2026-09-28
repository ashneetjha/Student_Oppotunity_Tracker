from datetime import datetime, date, timedelta, timezone
from backend.app.database import SessionLocal, engine, Base
from backend.app.models import User, Opportunity, Skill, Bookmark, Application, opportunity_skills
from backend.app.utils.security import hash_password

def seed_database():
    print("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Check if already seeded
        existing_users = db.query(User).count()
        if existing_users > 0:
            print(f"Database already contains {existing_users} users. Clearing existing data for fresh seed...")
            db.query(Application).delete()
            db.query(Bookmark).delete()
            db.execute(opportunity_skills.delete())
            db.query(Opportunity).delete()
            db.query(Skill).delete()
            db.query(User).delete()
            db.commit()

        print("Seeding Users...")
        admin = User(
            name="Admin User",
            email="admin@example.com",
            password_hash=hash_password("Admin@123"),
            college="OpportunityHub Global",
            role="admin",
            bio="Administrator of OpportunityHub platform."
        )
        student1 = User(
            name="Alex Johnson",
            email="student@example.com",
            password_hash=hash_password("Student@123"),
            college="SRM Institute of Science and Technology",
            role="student",
            bio="Computer Science student interested in software engineering, AI, and cloud computing."
        )
        student2 = User(
            name="Sarah Connor",
            email="student2@example.com",
            password_hash=hash_password("Student@123"),
            college="Indian Institute of Technology",
            role="student",
            bio="Data Science student passionate about machine learning competitions and workshops."
        )

        db.add_all([admin, student1, student2])
        db.commit()
        db.refresh(admin)
        db.refresh(student1)
        db.refresh(student2)

        print("Seeding Skills...")
        skills_data = [
            "Python", "JavaScript", "React", "Node.js", "SQL",
            "C++", "Java", "Spring", "AWS", "Cloud",
            "DevOps", "AI/ML", "DSA", "Algorithms", "UI/UX",
            "Figma", "Design", "Security", "Linux", "Networking",
            "Business", "Pitching", "Innovation", "GCP", "Frontend"
        ]
        skill_map = {}
        for s_name in skills_data:
            skill = Skill(skill_name=s_name)
            db.add(skill)
            skill_map[s_name] = skill
        db.commit()

        for s_name in skills_data:
            db.refresh(skill_map[s_name])

        print("Seeding 22 Opportunities (5 Internships, 4 Hackathons, 4 Workshops, 4 Certifications, 5 Competitions)...")
        opps_raw = [
            # 5 Internships
            {
                "title": "Software Engineering Intern",
                "organization": "Google",
                "type": "Internship",
                "deadline": "2026-10-09",
                "skills": ["JavaScript", "React", "SQL"],
                "location": "Bengaluru / Hybrid",
                "desc": "Work with world-class engineering teams to build scalable web products and solve real-world technical problems.",
                "eligibility": "B.Tech/BE Computer Science 2026/2027 graduates",
                "status": "Active"
            },
            {
                "title": "Data Science Internship",
                "organization": "Microsoft",
                "type": "Internship",
                "deadline": "2026-10-28",
                "skills": ["Python", "SQL", "AI/ML"],
                "location": "Hyderabad / Hybrid",
                "desc": "Apply data science and machine learning techniques to real products and business problems with expert mentors.",
                "eligibility": "Pre-final or final year students with strong statistical knowledge",
                "status": "Active"
            },
            {
                "title": "Java Developer Internship",
                "organization": "Infosys",
                "type": "Internship",
                "deadline": "2026-10-18",
                "skills": ["Java", "Spring", "SQL"],
                "location": "Pune / Hybrid",
                "desc": "Gain hands-on experience building enterprise-grade backend microservices using Java and Spring Boot.",
                "eligibility": "Open to all engineering undergraduates with OOP knowledge",
                "status": "Active"
            },
            {
                "title": "Frontend Engineering Intern",
                "organization": "Meta",
                "type": "Internship",
                "deadline": "2026-11-05",
                "skills": ["JavaScript", "React", "Frontend", "UI/UX"],
                "location": "Remote / Bengaluru",
                "desc": "Build highly responsive and interactive web experiences for millions of creators and community members.",
                "eligibility": "Undergraduate students with portfolio or web projects",
                "status": "Active"
            },
            {
                "title": "Cloud DevOps Intern",
                "organization": "Amazon Web Services",
                "type": "Internship",
                "deadline": "2026-11-15",
                "skills": ["Cloud", "AWS", "DevOps", "Linux"],
                "location": "Hyderabad / Hybrid",
                "desc": "Collaborate with cloud infrastructure teams to automate CI/CD pipelines and optimize container deployments.",
                "eligibility": "Students familiar with Linux fundamentals and scripting",
                "status": "Active"
            },

            # 4 Hackathons
            {
                "title": "AI Innovation Hackathon",
                "organization": "TechFest",
                "type": "Hackathon",
                "deadline": "2026-10-02",
                "skills": ["Python", "AI/ML", "React"],
                "location": "Online",
                "desc": "Build innovative AI solutions for real-world healthcare and education challenges and compete with student teams nationwide.",
                "eligibility": "Teams of 2 to 4 college students",
                "status": "Active"
            },
            {
                "title": "Global Web3 & FinTech Hackathon",
                "organization": "HackNation",
                "type": "Hackathon",
                "deadline": "2026-10-14",
                "skills": ["JavaScript", "Node.js", "Security"],
                "location": "Online",
                "desc": "Create secure and transparent decentralized applications and modern financial tools over a 48-hour sprint.",
                "eligibility": "Open to all student developers worldwide",
                "status": "Active"
            },
            {
                "title": "Smart Cities Student Hackathon",
                "organization": "National Smart Mission",
                "type": "Hackathon",
                "deadline": "2026-10-25",
                "skills": ["Python", "Cloud", "Algorithms"],
                "location": "Delhi / Hybrid",
                "desc": "Tackle urban transit, energy efficiency, and municipal waste management problems with software prototypes.",
                "eligibility": "Registered college students",
                "status": "Active"
            },
            {
                "title": "HealthTech Next Hackathon",
                "organization": "MedTech Alliance",
                "type": "Hackathon",
                "deadline": "2026-11-12",
                "skills": ["Python", "AI/ML", "React"],
                "location": "Online",
                "desc": "Build accessible patient diagnostic and appointment scheduling assistive tools with mentorship.",
                "eligibility": "College teams up to 4 members",
                "status": "Active"
            },

            # 4 Workshops
            {
                "title": "Cloud Computing Workshop",
                "organization": "AWS Academy",
                "type": "Workshop",
                "deadline": "2026-10-15",
                "skills": ["Cloud", "AWS", "DevOps"],
                "location": "Online",
                "desc": "Learn cloud fundamentals, containerized deployments, serverless functions, and modern cloud development practices.",
                "eligibility": "Any enrolled college student",
                "status": "Active"
            },
            {
                "title": "Cybersecurity Bootcamp",
                "organization": "SecureTech",
                "type": "Workshop",
                "deadline": "2026-11-03",
                "skills": ["Security", "Linux", "Networking"],
                "location": "Chennai",
                "desc": "Hands-on introduction to ethical hacking, network analysis, vulnerability assessment, and defense strategies.",
                "eligibility": "Basic understanding of operating systems and networking",
                "status": "Active"
            },
            {
                "title": "React Developer Workshop",
                "organization": "Frontend Masters",
                "type": "Workshop",
                "deadline": "2026-10-07",
                "skills": ["React", "JavaScript", "Frontend"],
                "location": "Online",
                "desc": "Deepen your React skills through practical component architecture, custom hooks, and state management exercises.",
                "eligibility": "Familiarity with HTML, CSS, and basic JavaScript",
                "status": "Active"
            },
            {
                "title": "Machine Learning Hands-on Workshop",
                "organization": "DeepLearning Hub",
                "type": "Workshop",
                "deadline": "2026-10-22",
                "skills": ["Python", "AI/ML", "Algorithms"],
                "location": "Online",
                "desc": "Practical deep-dive into model training, evaluation metrics, and deploying Scikit-Learn models.",
                "eligibility": "Basic knowledge of Python syntax",
                "status": "Active"
            },

            # 4 Certifications
            {
                "title": "Full Stack Web Development",
                "organization": "Coursera",
                "type": "Certification",
                "deadline": "2026-10-21",
                "skills": ["JavaScript", "React", "Node.js", "SQL"],
                "location": "Online",
                "desc": "Earn a professional certificate covering frontend design, backend API development, and SQL databases.",
                "eligibility": "Self-paced, accessible to all students",
                "status": "Active"
            },
            {
                "title": "Google Cloud Essentials",
                "organization": "Google Cloud",
                "type": "Certification",
                "deadline": "2026-11-10",
                "skills": ["Cloud", "GCP", "DevOps"],
                "location": "Online",
                "desc": "Build foundational cloud knowledge and validate it with an industry-recognized certificate.",
                "eligibility": "Students interested in cloud computing careers",
                "status": "Active"
            },
            {
                "title": "Professional Python Developer Certificate",
                "organization": "Python Institute",
                "type": "Certification",
                "deadline": "2026-11-20",
                "skills": ["Python", "DSA", "Algorithms"],
                "location": "Online",
                "desc": "Validate advanced Python syntax, object-oriented design patterns, and algorithmic performance.",
                "eligibility": "Students who complete the mock assessment",
                "status": "Active"
            },
            {
                "title": "Certified Associate in Software Architecture",
                "organization": "TechGuild",
                "type": "Certification",
                "deadline": "2026-11-30",
                "skills": ["Java", "Spring", "DevOps"],
                "location": "Online",
                "desc": "Demonstrate understanding of microservices, distributed caching, and scalable system design.",
                "eligibility": "Final-year college students",
                "status": "Active"
            },

            # 5 Competitions
            {
                "title": "National Coding Challenge",
                "organization": "CodeNation",
                "type": "Competition",
                "deadline": "2026-10-12",
                "skills": ["C++", "DSA", "Algorithms"],
                "location": "Online",
                "desc": "Test your problem-solving and competitive programming skills against developer students nationwide.",
                "eligibility": "All enrolled college and university students",
                "status": "Active"
            },
            {
                "title": "UI/UX Design Sprint",
                "organization": "DesignLab",
                "type": "Competition",
                "deadline": "2026-10-05",
                "skills": ["UI/UX", "Figma", "Design"],
                "location": "Online",
                "desc": "Design an intuitive user experience for a real product challenge during a fast-paced 72-hour sprint.",
                "eligibility": "Individual student designers and duos",
                "status": "Active"
            },
            {
                "title": "Startup Pitch Challenge",
                "organization": "InnovateX",
                "type": "Competition",
                "deadline": "2026-10-30",
                "skills": ["Business", "Pitching", "Innovation"],
                "location": "Online",
                "desc": "Present your early-stage startup idea to mentors and venture judges to win incubation grant support.",
                "eligibility": "Student-founded early ventures and ideas",
                "status": "Active"
            },
            {
                "title": "Algorithmic Masterclass Contest",
                "organization": "AlgoExpert Guild",
                "type": "Competition",
                "deadline": "2026-11-08",
                "skills": ["Algorithms", "DSA", "C++", "Python"],
                "location": "Online",
                "desc": "Compete across dynamic programming, graph traversal, and combinatorics problem sets.",
                "eligibility": "Undergraduate engineering students",
                "status": "Active"
            },
            {
                "title": "Creative App Development Challenge",
                "organization": "AppCraft",
                "type": "Competition",
                "deadline": "2026-11-22",
                "skills": ["React", "JavaScript", "UI/UX"],
                "location": "Online",
                "desc": "Showcase your most useful open-source web application solving everyday student productivity problems.",
                "eligibility": "Any individual student or student team",
                "status": "Active"
            }
        ]

        created_opps = []
        for o_raw in opps_raw:
            opp_skills = [skill_map[s] for s in o_raw["skills"] if s in skill_map]
            opp = Opportunity(
                title=o_raw["title"],
                organization=o_raw["organization"],
                type=o_raw["type"],
                deadline=o_raw["deadline"],
                location=o_raw["location"],
                description=o_raw["desc"],
                eligibility=o_raw["eligibility"],
                status=o_raw["status"],
                created_by=admin.user_id,
                skills=opp_skills
            )
            db.add(opp)
            created_opps.append(opp)
        db.commit()

        for opp in created_opps:
            db.refresh(opp)

        print("Seeding Bookmarks & Applications for student@example.com (Alex Johnson)...")
        # Bookmarks for Alex: opps 0, 1, 3, 5, 8
        bookmark_indices = [0, 1, 3, 5, 8]
        for idx in bookmark_indices:
            bm = Bookmark(user_id=student1.user_id, opportunity_id=created_opps[idx].opportunity_id)
            db.add(bm)

        # Applications for Alex with different realistic statuses matching frontend:
        # Interested (2), Applied (3), Shortlisted (2), Completed (1) -> Total 8!
        app_assignments = [
            (0, "Applied"),       # Google Software Engineering Intern
            (1, "Shortlisted"),   # Microsoft Data Science Intern
            (3, "Interested"),    # Coursera Full Stack Web Dev
            (4, "Applied"),       # CodeNation National Coding Challenge
            (5, "Applied"),       # TechFest AI Hackathon
            (6, "Interested"),    # DesignLab UI/UX
            (2, "Completed"),     # Infosys Java Developer
            (9, "Shortlisted")    # AWS Cloud Computing
        ]
        now = datetime.now(timezone.utc)
        for idx, status in app_assignments:
            app = Application(
                user_id=student1.user_id,
                opportunity_id=created_opps[idx].opportunity_id,
                status=status,
                applied_at=now - timedelta(days=idx * 2 + 1),
                updated_at=now - timedelta(days=idx)
            )
            db.add(app)

        # Bookmarks & Applications for student2@example.com (Sarah Connor)
        bm2 = Bookmark(user_id=student2.user_id, opportunity_id=created_opps[1].opportunity_id)
        bm3 = Bookmark(user_id=student2.user_id, opportunity_id=created_opps[5].opportunity_id)
        db.add_all([bm2, bm3])

        app_sarah = Application(
            user_id=student2.user_id,
            opportunity_id=created_opps[1].opportunity_id,
            status="Applied",
            applied_at=now - timedelta(days=2),
            updated_at=now
        )
        db.add(app_sarah)

        db.commit()
        print("Database seeded successfully!")
        print("Demo Accounts:")
        print("  Admin: admin@example.com / Admin@123")
        print("  Student: student@example.com / Student@123")
        print("  Student 2: student2@example.com / Student@123")
        print(f"Total Opportunities: {len(created_opps)}")
        print(f"Total Skills: {len(skills_data)}")

    except Exception as e:
        db.rollback()
        print(f"Error during seeding: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
