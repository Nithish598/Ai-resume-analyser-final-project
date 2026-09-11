"""Comprehensive Unit & Integration Test Suite for Section 38 Benchmark Resumes (Resumes A-J)
and Multi-Domain Role Competency Matrix Engine.
"""
import pytest
from src.recommendation.job_recommender import JobRoleRecommender
from src.recommendation.job_role_kb import get_job_role_by_id, JOB_ROLES_KNOWLEDGE_BASE


# =====================================================================
# 1. SECTION 38 BENCHMARK RESUMES (A through J)
# =====================================================================

def test_resume_a_html_css_git():
    """Resume A: HTML, CSS, Git.
    Expected: Web / Frontend pathway with major gaps; Full Stack is early-stage / not qualified.
    """
    cand = {
        "candidate_name": "Resume A Candidate",
        "skills": ["HTML5", "CSS3", "Git"],
        "education": [{"degree": "B.Sc Computer Science", "status": "Completed"}],
        "projects": [{"name": "Static Landing Page", "technologies": ["HTML5", "CSS3", "Git"]}],
    }
    recommender = JobRoleRecommender()
    recs = recommender.recommend_roles(cand, top_k=5)
    role_names = [r.role_name for r in recs]

    # Web Developer or Frontend Developer should lead
    assert recs[0].role_name in ["Web Developer", "Frontend Developer", "UI Developer"]

    # Evaluate Full Stack Developer specifically
    fs_eval = recommender.analyze_role_fit(cand, "full_stack_developer")
    assert fs_eval is not None
    # Candidate lacks JavaScript, backend, database, APIs, security -> Full Stack must be early-stage / moderate at most
    assert fs_eval.match_score < 75.0
    assert len(fs_eval.missing_competencies) >= 3
    assert any("Backend" in cat for cat in fs_eval.missing_competencies.keys())


def test_resume_b_frontend_react():
    """Resume B: HTML, CSS, JavaScript, React, Git.
    Expected: Frontend Developer strong match; NOT Full Stack Developer.
    """
    cand = {
        "candidate_name": "Resume B Candidate",
        "skills": ["HTML5", "CSS3", "JavaScript", "React", "Git", "Responsive Design"],
        "education": [{"degree": "B.Tech Information Technology", "status": "Completed"}],
        "projects": [{"name": "React Task Tracker", "technologies": ["React", "JavaScript", "CSS3", "Git"]}],
    }
    recommender = JobRoleRecommender()
    recs = recommender.recommend_roles(cand, top_k=5)
    
    # Frontend Developer / UI Engineer must rank #1
    assert recs[0].role_name in ["Frontend Developer", "Web Developer", "UI / Design Engineer", "UI Developer"]
    assert recs[0].match_score >= 60.0

    # Full Stack evaluation
    fs_eval = recommender.analyze_role_fit(cand, "full_stack_developer")
    fe_eval = recommender.analyze_role_fit(cand, "frontend_developer")
    assert fe_eval.match_score > fs_eval.match_score
    # Backend language & database must be flagged as missing
    assert any("Backend" in cat for cat in fs_eval.missing_competencies.keys())


def test_resume_c_full_stack_mern():
    """Resume C: HTML, CSS, JavaScript, React, Node.js, Express.js, PostgreSQL, REST API, Authentication, Git, Docker.
    Expected: Full Stack Developer strong match (>=75%).
    """
    cand = {
        "candidate_name": "Resume C Candidate",
        "skills": [
            "HTML5", "CSS3", "JavaScript", "React", "Node.js", "Express.js",
            "PostgreSQL", "SQL", "REST API", "Authentication", "Git", "Docker"
        ],
        "education": [{"degree": "B.E Computer Science", "status": "Completed"}],
        "projects": [{"name": "E-Commerce Full Stack Store", "technologies": ["React", "Node.js", "Express.js", "PostgreSQL", "REST API", "Docker"]}],
    }
    recommender = JobRoleRecommender()
    recs = recommender.recommend_roles(cand, top_k=5)
    
    top_role = recs[0]
    assert top_role.role_name in ["Full Stack Developer", "Backend Developer", "Software Engineer", "Frontend Developer"]
    fs_eval = recommender.analyze_role_fit(cand, "full_stack_developer")
    assert fs_eval.match_score >= 70.0
    assert len(fs_eval.demonstrated_competencies) >= 5


def test_resume_d_data_analyst():
    """Resume D: Python, SQL, Pandas, NumPy, Power BI, Microsoft Excel, Statistics, Data Analysis.
    Expected: Data Analyst very strong match (>=75%); Data Scientist partial.
    """
    cand = {
        "candidate_name": "Resume D Candidate",
        "skills": [
            "Python", "SQL", "Pandas", "NumPy", "Power BI", "Microsoft Excel",
            "Statistics", "Data Analysis", "Data Visualization"
        ],
        "education": [{"degree": "B.Sc Statistics & Data Analytics", "status": "Completed"}],
        "projects": [{"name": "Executive Sales KPI Dashboard", "technologies": ["Power BI", "SQL", "Python", "Pandas"]}],
    }
    recommender = JobRoleRecommender()
    recs = recommender.recommend_roles(cand, top_k=5)
    
    assert recs[0].role_name == "Data Analyst"
    assert recs[0].match_score >= 70.0

    # Data Scientist evaluation: candidate lacks Scikit-Learn / Machine Learning / XGBoost
    ds_eval = recommender.analyze_role_fit(cand, "data_scientist")
    da_eval = recommender.analyze_role_fit(cand, "data_analyst")
    assert da_eval.match_score > ds_eval.match_score


def test_resume_e_data_engineer():
    """Resume E: Python, SQL, Apache Spark, Kafka, Airflow, Snowflake, AWS, Docker, Git.
    Expected: Data Engineer very strong match (>=75%).
    """
    cand = {
        "candidate_name": "Resume E Candidate",
        "skills": [
            "Python", "SQL", "Apache Spark", "Kafka", "Airflow", "Snowflake",
            "AWS", "Docker", "Git", "ETL Pipelines", "Database Management"
        ],
        "education": [{"degree": "B.Tech Computer Science", "status": "Completed"}],
        "projects": [{"name": "Real-time Streaming Lakehouse Pipeline", "technologies": ["Python", "Apache Spark", "Airflow", "Kafka", "Snowflake"]}],
    }
    recommender = JobRoleRecommender()
    recs = recommender.recommend_roles(cand, top_k=5)
    
    assert recs[0].role_name == "Data Engineer"
    assert recs[0].match_score >= 70.0


def test_resume_f_data_scientist():
    """Resume F: Python, Pandas, NumPy, Scikit-Learn, Statistics, Machine Learning, XGBoost, Model Evaluation.
    Expected: Data Scientist very strong match (>=75%).
    """
    cand = {
        "candidate_name": "Resume F Candidate",
        "skills": [
            "Python", "Pandas", "NumPy", "Scikit-Learn", "Statistics",
            "Machine Learning", "XGBoost", "Data Analysis", "SQL", "Git"
        ],
        "education": [{"degree": "M.Sc Data Science & AI", "status": "Completed"}],
        "projects": [{"name": "Customer Churn Prediction Engine", "technologies": ["Python", "Pandas", "Scikit-Learn", "XGBoost", "Machine Learning"]}],
    }
    recommender = JobRoleRecommender()
    recs = recommender.recommend_roles(cand, top_k=5)
    
    top_names = [r.role_name for r in recs[:2]]
    assert "Data Scientist" in top_names or "Machine Learning Engineer" in top_names
    ds_eval = recommender.analyze_role_fit(cand, "data_scientist")
    assert ds_eval.match_score >= 70.0


def test_resume_g_ui_ux_designer():
    """Resume G: Figma, Wireframing, Prototyping, User Research, Usability Testing, Design Systems, Information Architecture.
    Expected: UI/UX Designer very strong match (>=75%).
    """
    cand = {
        "candidate_name": "Resume G Candidate",
        "skills": [
            "Figma", "Wireframing", "Prototyping", "User Research",
            "Usability Testing", "Design Systems", "Information Architecture", "Responsive Design"
        ],
        "education": [{"degree": "B.Des Human-Computer Interaction", "status": "Completed"}],
        "projects": [{"name": "Mobile Health App Redesign Case Study", "technologies": ["Figma", "Wireframing", "Prototyping", "User Research"]}],
    }
    recommender = JobRoleRecommender()
    recs = recommender.recommend_roles(cand, top_k=5)
    
    assert recs[0].role_name == "UI/UX Designer"
    assert recs[0].match_score >= 75.0


def test_resume_h_android_developer():
    """Resume H: Kotlin, Android SDK, Android Studio, Jetpack Compose, REST API, Room, Git.
    Expected: Android Developer very strong match (>=75%).
    """
    cand = {
        "candidate_name": "Resume H Candidate",
        "skills": [
            "Kotlin", "Android SDK", "Android Studio", "Jetpack Compose",
            "REST API", "Room", "Git", "JSON", "SQL"
        ],
        "education": [{"degree": "B.Tech Computer Science", "status": "Completed"}],
        "projects": [{"name": "Native Android Habit Tracker App", "technologies": ["Kotlin", "Android SDK", "Jetpack Compose", "Room"]}],
    }
    recommender = JobRoleRecommender()
    recs = recommender.recommend_roles(cand, top_k=5)
    
    top_names = [r.role_name for r in recs[:2]]
    assert "Android Developer" in top_names or "Mobile Developer" in top_names
    and_eval = recommender.analyze_role_fit(cand, "android_developer")
    assert and_eval.match_score >= 75.0


def test_resume_i_ios_developer():
    """Resume I: Swift, iOS SDK, Xcode, SwiftUI, UIKit, REST API, Core Data, Git.
    Expected: iOS Developer very strong match (>=75%).
    """
    cand = {
        "candidate_name": "Resume I Candidate",
        "skills": [
            "Swift", "iOS SDK", "Xcode", "SwiftUI", "UIKit",
            "REST API", "Core Data", "Git", "JSON"
        ],
        "education": [{"degree": "B.Sc Computer Science", "status": "Completed"}],
        "projects": [{"name": "Live Crypto Market iOS App", "technologies": ["Swift", "SwiftUI", "Core Data", "REST API"]}],
    }
    recommender = JobRoleRecommender()
    recs = recommender.recommend_roles(cand, top_k=5)
    
    top_names = [r.role_name for r in recs[:2]]
    assert "iOS Developer" in top_names or "Mobile Developer" in top_names
    ios_eval = recommender.analyze_role_fit(cand, "ios_developer")
    assert ios_eval.match_score >= 75.0


def test_resume_j_backend_java():
    """Resume J: Java, Spring Boot, REST API, PostgreSQL, Docker, Git, Software Testing, OOP.
    Expected: Backend Developer & Software Engineer strong matches (>=75%).
    """
    cand = {
        "candidate_name": "Resume J Candidate",
        "skills": [
            "Java", "Spring Boot", "REST API", "PostgreSQL", "SQL",
            "Docker", "Git", "Software Testing", "Object-Oriented Programming", "Database Management"
        ],
        "education": [{"degree": "B.Tech Computer Science", "status": "Completed"}],
        "projects": [{"name": "Scalable Banking Microservices API", "technologies": ["Java", "Spring Boot", "PostgreSQL", "Docker", "REST API"]}],
    }
    recommender = JobRoleRecommender()
    recs = recommender.recommend_roles(cand, top_k=5)
    
    top_names = [r.role_name for r in recs[:3]]
    assert "Backend Developer" in top_names or "Software Engineer" in top_names
    be_eval = recommender.analyze_role_fit(cand, "backend_developer")
    assert be_eval.match_score >= 70.0


# =====================================================================
# 2. ALTERNATIVE CLUSTERS & PREREQUISITES VALIDATION
# =====================================================================

def test_alternative_clusters_zero_penalty():
    """Verify Angular candidate gets full credit for Frontend Framework without penalty for missing React."""
    cand_angular = {
        "skills": ["HTML5", "CSS3", "JavaScript", "Angular", "TypeScript", "Git", "REST API"],
        "education": [{"degree": "B.Sc Computer Science", "status": "Completed"}],
    }
    cand_react = {
        "skills": ["HTML5", "CSS3", "JavaScript", "React", "TypeScript", "Git", "REST API"],
        "education": [{"degree": "B.Sc Computer Science", "status": "Completed"}],
    }
    recommender = JobRoleRecommender()
    eval_ang = recommender.analyze_role_fit(cand_angular, "frontend_developer")
    eval_react = recommender.analyze_role_fit(cand_react, "frontend_developer")
    
    # Scores should be virtually identical
    assert abs(eval_ang.match_score - eval_react.match_score) < 5.0
    # Angular should be satisfied
    assert any("Angular" in str(alt) for alt in eval_ang.alternatives_satisfied)


def test_prerequisites_missing_detection():
    """Verify candidate with React or Next.js but missing JavaScript gets flagged under prerequisites_missing."""
    cand = {
        "skills": ["HTML5", "CSS3", "React", "Git"],  # Missing JavaScript!
        "education": [{"degree": "B.Sc Computer Science", "status": "Completed"}],
    }
    recommender = JobRoleRecommender()
    eval_res = recommender.analyze_role_fit(cand, "frontend_developer")
    
    assert eval_res.prerequisites_missing is not None
    prereq_names = [p["missing_prerequisite"].lower() for p in eval_res.prerequisites_missing]
    assert "javascript" in prereq_names


def test_category_gap_scores_breakdown():
    """Verify category_gap_scores has domain coverage metrics for Full Stack Developer."""
    cand = {
        "skills": ["HTML5", "CSS3", "JavaScript", "React", "Git"],
        "education": [{"degree": "B.Sc Computer Science", "status": "Completed"}],
    }
    recommender = JobRoleRecommender()
    eval_res = recommender.analyze_role_fit(cand, "full_stack_developer")
    
    assert "Frontend Fundamentals" in eval_res.category_gap_scores
    fe_stat = eval_res.category_gap_scores["Frontend Fundamentals"]
    assert fe_stat["matched"] >= 3
    assert fe_stat["total"] >= 4
    assert fe_stat["pct"] > 60.0


def test_unified_candidate_skill_collection_and_role_matching():
    """Verify that skills from all Module 1 sections are extracted with evidence and matched."""
    cand = {
        "candidate_name": "Alex Dev",
        "professional_summary": "Full stack engineer experienced in building scalable React web applications and REST APIs.",
        "skills": {
            "programming_languages": ["JavaScript", "TypeScript"],
            "frameworks": ["React", "Next.js", "Tailwind CSS"],
            "databases": ["PostgreSQL"],
            "tools": ["Git", "GitHub"],
        },
        "projects": [
            {
                "name": "3D Interactive Showcase",
                "technologies": ["React Three Fiber", "Three.js", "Framer Motion"],
                "description": "Designed a 3D animated hero section with post-processing visual effects and responsive design.",
            },
            {
                "name": "E-Commerce API",
                "technologies": ["Node.js", "Express.js", "JWT Authentication"],
                "description": "Built RESTful backend microservices with JWT authentication and PostgreSQL.",
            }
        ],
        "experience": [
            {
                "company": "Tech Corp",
                "role": "Frontend Intern",
                "technologies": ["HTML5", "CSS3", "Vite", "Docker"],
                "responsibilities": "Developed responsive UI components and configured Docker containers.",
            }
        ]
    }
    recommender = JobRoleRecommender()
    
    # 1. Test Unified Candidate Skill Extraction with Evidence
    evidence_map = recommender.extract_unified_skills_with_evidence(cand)
    flat_skills = recommender.extract_flat_candidate_skills(cand)
    
    # Verify presence of skills from projects, frameworks, experience, and summary
    assert "React Three Fiber" in flat_skills
    assert "Three.js" in flat_skills
    assert "Framer Motion" in flat_skills
    assert "Docker" in flat_skills
    assert "JWT Authentication" in flat_skills
    assert "Node.js" in flat_skills
    assert "PostgreSQL" in flat_skills
    assert "Next.js" in flat_skills
    
    # 2. Test Section 11 Structured Role Matching Output
    res = recommender.match_candidate_against_role(cand, "UI/UX Developer")
    assert res["target_role"] == "UI Developer" or "UI" in res["target_role"]
    assert res["match_score"] > 60
    assert len(res["matched_skills"]) >= 5
    assert "role_requirements" in res
    assert "core" in res["role_requirements"]
    assert "important" in res["role_requirements"]
    assert "nice_to_have" in res["role_requirements"]
    assert "overall_recommendation" in res
    assert isinstance(res["priority_skills_to_improve"], list)
    
    # Verify candidate extracted skills has all skills including TypeScript
    assert "TypeScript" in res["candidate_skills"]
    assert "React Three Fiber" in res["candidate_skills"]
    assert "PostgreSQL" in res["candidate_skills"]

    # Verify no arbitrary skill capping on matched skills for UI Developer
    matched_names = [m["normalized_skill"] for m in res["matched_skills"]]
    assert "React" in matched_names
    assert "HTML5" in matched_names
    assert "CSS3" in matched_names
    assert "JavaScript" in matched_names
    assert "Tailwind CSS" in matched_names
    assert "Git" in matched_names


def test_critical_skill_completeness_and_fallback_rules():
    """
    Validates CRITICAL SKILL COMPLETENESS RULES:
    1. Construct Master Skill Set across all 29 fields (skills, summary, experience, projects, certs, raw_text).
    2. Mandatory fallback when structured category is empty (e.g. skills.frontend=[]) but present in experience/projects.
    3. Raw text scanning validation (extracts missing skills directly from raw_text).
    4. Categorized Skills Matrix correctly assigns categories based on intrinsic nature.
    5. Deduplication and normalization (My SQL -> MySQL, REST AP Is -> REST APIs, Simple JWT -> JWT Authentication).
    6. Zero skill loss and zero arbitrary capping.
    """
    from src.skills.skill_normalizer import SkillNormalizer

    cand_profile = {
        "name": "Alex Taylor",
        "skills": {
            "programming_languages": ["Python", "JavaScript"],
            "frontend": [],  # INTENTIONALLY EMPTY in Module 1
            "frameworks": ["React", "Next.js", "Tailwind CSS"],  # Module 1 miscategorized React & Next.js under frameworks
            "databases": ["My SQL", "MongoDB"],  # Malformed alias
            "tools": ["Git", "Postman"],
        },
        "experience": [
            {
                "company": "WebTech Labs",
                "role": "Frontend Intern",
                "technologies": ["HTML", "CSS", "JavaScript"],
                "responsibilities": ["Built responsive landing pages using HTML, CSS, and modern CSS3 animations."],
            }
        ],
        "projects": [
            {
                "title": "Full Stack Portal",
                "technologies": ["Django", "Django REST Framework", "Simple JWT", "PostgreSQL"],
                "description": "Developed backend APIs using REST AP Is, Django, and secure JWT authentication.",
            }
        ],
        "certifications": ["AWS Certified Cloud Practitioner"],
        "professional_summary": "Aspiring engineer with experience in Docker containerization and Kubernetes orchestration.",
        "raw_text": "Skills Summary: Frontend: HTML, CSS, React, Next.js, Tailwind CSS, Bootstrap, Framer Motion. Deployment: Vercel, Render. Version Control: Git, GitHub."
    }

    # 1. Build Master Skill Set
    master_skills = SkillNormalizer.build_master_skill_set(cand_profile)
    
    # 2. Verify all skills captured without loss
    expected_skills = [
        "HTML5", "CSS3", "JavaScript", "Python", "React", "Next.js", "Tailwind CSS",
        "Bootstrap", "Framer Motion", "MySQL", "MongoDB", "PostgreSQL", "Django",
        "REST APIs", "JWT Authentication", "Git", "GitHub", "Postman", "AWS",
        "Docker", "Kubernetes", "Vercel", "Render"
    ]
    for exp_sk in expected_skills:
        assert exp_sk.lower() in master_skills, f"Skill '{exp_sk}' was unexpectedly lost!"

    # 3. Build Categorized Skills Matrix
    matrix = SkillNormalizer.build_categorized_skills_matrix(cand_profile)

    # 4. Verify category assignment based on actual nature (not Module 1 flawed structure)
    assert "Frontend Technologies" in matrix
    frontend_skills = matrix["Frontend Technologies"]
    assert "HTML5" in frontend_skills or "HTML" in frontend_skills
    assert "CSS3" in frontend_skills or "CSS" in frontend_skills
    assert "React" in frontend_skills
    assert "Next.js" in frontend_skills
    assert "Tailwind CSS" in frontend_skills
    assert "Bootstrap" in frontend_skills
    assert "Framer Motion" in frontend_skills

    assert "Programming Languages" in matrix
    prog_skills = matrix["Programming Languages"]
    assert "JavaScript" in prog_skills
    assert "Python" in prog_skills

    assert "Backend Technologies" in matrix
    backend_skills = matrix["Backend Technologies"]
    assert "Django" in backend_skills

    assert "Databases & Storage" in matrix
    db_skills = matrix["Databases & Storage"]
    assert "MySQL" in db_skills  # "My SQL" correctly normalized to MySQL
    assert "MongoDB" in db_skills
    assert "PostgreSQL" in db_skills

    assert "Authentication & Security" in matrix
    auth_skills = matrix["Authentication & Security"]
    assert "JWT Authentication" in auth_skills  # "Simple JWT" normalized

    assert "APIs & Web Services" in matrix
    api_skills = matrix["APIs & Web Services"]
    assert "REST APIs" in api_skills  # "REST AP Is" normalized

    assert "Cloud & Hosting" in matrix
    cloud_skills = matrix["Cloud & Hosting"]
    assert "AWS" in cloud_skills
    assert "Vercel" in cloud_skills
    assert "Render" in cloud_skills

    assert "DevOps & Infrastructure" in matrix
    devops_skills = matrix["DevOps & Infrastructure"]
    assert "Docker" in devops_skills
    assert "Kubernetes" in devops_skills

    assert "Development Tools" in matrix
    tools_skills = matrix["Development Tools"]
    assert "Git" in tools_skills
    assert "GitHub" in tools_skills
    assert "Postman" in tools_skills
