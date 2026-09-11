"""Structured Role-Requirement Knowledge Base & Taxonomy.

Defines 12 comprehensive role matrices with prioritized skill tiers:
- CORE (weight 1.0): Absolute technical must-haves
- IMPORTANT (weight 0.75): High-value competencies expected in production
- RECOMMENDED (weight 0.50): Valuable additions that elevate capability
- OPTIONAL (weight 0.25): Advanced / emerging / bonus technologies
- PROFESSIONAL: Methodologies and soft skills (Agile, SDLC, Communication) isolated from technical gaps

Features:
- Categorized skill taxonomy across 12 domains
- Skill normalization and synonym disambiguation
- Skill relationship and partial credit mapping
- Short, concise 1-sentence why-needed and how-to-improve guides
- Dynamic enrichment from 'job_roles.csv' without modifying the file
"""
import os
import re
from typing import Dict, List, Any, Optional, Set, Tuple
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JOB_ROLES_CSV = os.path.join(BASE_DIR, "AI Resume Analyzer – Job Role Prediction Dataset", "job_roles.csv")


# 12 Taxonomy Categories
TAXONOMY_CATEGORIES = [
    "Programming Languages",
    "Frontend",
    "Backend",
    "Databases",
    "DevOps / Cloud",
    "Testing",
    "Security",
    "CS Fundamentals",
    "Architecture",
    "Professional Methodologies",
    "Soft Skills",
    "Optional / Emerging",
]


# Canonical skill normalizer mapping common synonyms/variations to canonical keys
SKILL_SYNONYMS: Dict[str, str] = {
    "js": "javascript",
    "javascript": "javascript",
    "ts": "typescript",
    "typescript": "typescript",
    "py": "python",
    "python": "python",
    "python3": "python",
    "python 3": "python",
    "html": "html",
    "html5": "html",
    "css": "css",
    "css3": "css",
    "html/css": "html",
    "react": "react",
    "react.js": "react",
    "reactjs": "react",
    "react js": "react",
    "react native": "react native",
    "next.js": "next.js",
    "nextjs": "next.js",
    "next js": "next.js",
    "node": "node.js",
    "node.js": "node.js",
    "nodejs": "node.js",
    "node js": "node.js",
    "express": "express.js",
    "express.js": "express.js",
    "expressjs": "express.js",
    "vue": "vue.js",
    "vue.js": "vue.js",
    "vuejs": "vue.js",
    "angular": "angular",
    "angularjs": "angular",
    "rest": "rest apis",
    "rest api": "rest apis",
    "rest apis": "rest apis",
    "restful api": "rest apis",
    "restful apis": "rest apis",
    "restapi": "rest apis",
    "restapis": "rest apis",
    "restapi's": "rest apis",
    "rest api's": "rest apis",
    "rest-api": "rest apis",
    "rest-apis": "rest apis",
    "rest_api": "rest apis",
    "rest_apis": "rest apis",
    "web api": "rest apis",
    "web apis": "rest apis",
    "web api's": "rest apis",
    "web-api": "rest apis",
    "web-apis": "rest apis",
    "api development": "rest apis",
    "api integration": "api integration",
    "apis": "rest apis",
    "api's": "rest apis",
    "graphql": "graphql",
    "sql": "sql",
    "mysql": "mysql",
    "postgresql": "postgresql",
    "postgres": "postgresql",
    "mongodb": "mongodb",
    "mongo": "mongodb",
    "redis": "redis",
    "git": "git",
    "github": "git",
    "git/github": "git",
    "linux": "linux",
    "docker": "docker",
    "kubernetes": "kubernetes",
    "k8s": "kubernetes",
    "ci/cd": "ci/cd",
    "cicd": "ci/cd",
    "ci / cd": "ci/cd",
    "aws": "aws",
    "amazon web services": "aws",
    "gcp": "gcp",
    "google cloud": "gcp",
    "azure": "azure",
    "authentication": "authentication",
    "authorization": "authorization",
    "auth": "authentication",
    "web security": "web security",
    "security": "web security",
    "owasp": "web security",
    "testing": "testing",
    "software testing": "testing",
    "unit testing": "testing",
    "integration testing": "testing",
    "test automation": "test automation",
    "selenium": "selenium",
    "playwright": "playwright",
    "cypress": "cypress",
    "jest": "jest",
    "pytest": "pytest",
    "junit": "junit",
    "data structures": "dsa",
    "algorithms": "dsa",
    "dsa": "dsa",
    "data structures & algorithms": "dsa",
    "data structures and algorithms": "dsa",
    "oop": "oop",
    "object oriented programming": "oop",
    "object-oriented programming": "oop",
    "system design": "system design",
    "system design basics": "system design",
    "database design": "database design",
    "database": "database design",
    "databases": "database design",
    "dbms": "database design",
    "debugging": "debugging",
    "devtools": "browser devtools",
    "browser devtools": "browser devtools",
    "npm": "npm",
    "responsive design": "responsive design",
    "accessibility": "accessibility",
    "web accessibility": "accessibility",
    "wcag": "accessibility",
    "performance optimization": "performance optimization",
    "agile": "agile/scrum",
    "scrum": "agile/scrum",
    "agile/scrum": "agile/scrum",
    "sdlc": "sdlc",
    "ui development": "ui development",
    "ui design": "ui design",
    "ux design": "ux design",
    "ui/ux": "ui/ux design",
    "ui/ux design": "ui/ux design",
    "figma": "figma",
    "figma basics": "figma",
    "wireframing": "wireframing",
    "prototyping": "prototyping",
    "user research": "user research",
    "ux research": "user research",
    "information architecture": "information architecture",
    "interaction design": "interaction design",
    "visual design": "visual design",
    "typography": "typography",
    "color theory": "color theory",
    "design systems": "design systems",
    "usability testing": "usability testing",
    "user flows": "user flows",
    "ux documentation": "ux documentation",
    "django": "django",
    "flask": "flask",
    "fastapi": "fastapi",
    "spring boot": "spring boot",
    "spring": "spring boot",
    "java": "java",
    "c++": "c++",
    "c#": "c#",
    ".net": "c#",
    "php": "php",
    "scala": "scala",
    "kotlin": "kotlin",
    "swift": "swift",
    "flutter": "flutter",
    "dart": "flutter",
    "android sdk": "android sdk",
    "android": "android sdk",
    "ios sdk": "ios sdk",
    "ios": "ios sdk",
    "orm": "orm",
    "cloud": "cloud basics",
    "cloud basics": "cloud basics",
    "cloud platforms": "cloud platforms",
    "deployment": "deployment",
    "problem solving": "problem solving",
    "software design": "software design",
    "design patterns": "software design",
    "excel": "excel",
    "microsoft excel": "excel",
    "ms excel": "excel",
    "pandas": "pandas",
    "numpy": "numpy",
    "data cleaning": "data cleaning",
    "eda": "eda",
    "exploratory data analysis": "eda",
    "statistics": "statistics",
    "statistical analysis": "statistics",
    "probability": "probability",
    "data visualization": "data visualization",
    "power bi": "power bi",
    "powerbi": "power bi",
    "tableau": "tableau",
    "reporting": "reporting",
    "data interpretation": "data interpretation",
    "business intelligence": "business intelligence",
    "bi": "business intelligence",
    "data modeling": "data modeling",
    "etl": "etl/elt",
    "elt": "etl/elt",
    "etl/elt": "etl/elt",
    "data pipelines": "data pipelines",
    "apache spark": "apache spark",
    "spark": "apache spark",
    "pyspark": "apache spark",
    "hadoop": "hadoop basics",
    "hadoop basics": "hadoop basics",
    "airflow": "airflow",
    "apache airflow": "airflow",
    "kafka": "kafka",
    "apache kafka": "kafka",
    "data warehouses": "data warehouses",
    "data warehousing": "data warehouses",
    "snowflake": "data warehouses",
    "bigquery": "data warehouses",
    "redshift": "data warehouses",
    "distributed systems": "distributed systems",
    "machine learning": "machine learning",
    "ml": "machine learning",
    "deep learning": "deep learning",
    "dl": "deep learning",
    "scikit-learn": "scikit-learn",
    "sklearn": "scikit-learn",
    "tensorflow": "tensorflow",
    "pytorch": "pytorch",
    "feature engineering": "feature engineering",
    "model evaluation": "model evaluation",
    "jupyter": "jupyter",
    "jupyter notebook": "jupyter",
    "experimentation": "experimentation",
    "nlp": "nlp",
    "natural language processing": "nlp",
    "computer vision": "computer vision",
    "cv": "computer vision",
    "mlops": "mlops basics",
    "mlops basics": "mlops basics",
    "microservices": "microservices",
    "ai-assisted development": "ai-assisted development",
    "generative ai": "generative ai",
    "genai": "generative ai",
    "communication": "communication",
    "teamwork": "team collaboration",
    "team collaboration": "team collaboration",
    "time management": "time management",
    "leadership": "leadership",
    "code review": "code review",
}


# Canonical human-readable display names for skills (Requirement 6)
CANONICAL_SKILL_DISPLAY: Dict[str, str] = {
    "rest apis": "REST APIs",
    "python": "Python",
    "django": "Django",
    "flask": "Flask",
    "fastapi": "FastAPI",
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "html": "HTML5",
    "css": "CSS3",
    "react": "React",
    "react native": "React Native",
    "next.js": "Next.js",
    "node.js": "Node.js",
    "express.js": "Express.js",
    "vue.js": "Vue.js",
    "angular": "Angular",
    "graphql": "GraphQL",
    "sql": "SQL",
    "mysql": "MySQL",
    "postgresql": "PostgreSQL",
    "mongodb": "MongoDB",
    "redis": "Redis",
    "git": "Git",
    "linux": "Linux",
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "ci/cd": "CI/CD",
    "aws": "AWS",
    "gcp": "GCP",
    "azure": "Azure",
    "dsa": "Data Structures & Algorithms",
    "oop": "Object-Oriented Programming (OOP)",
    "sdlc": "SDLC",
    "agile/scrum": "Agile / Scrum",
    "pandas": "Pandas",
    "numpy": "NumPy",
    "scikit-learn": "Scikit-Learn",
    "tensorflow": "TensorFlow",
    "pytorch": "PyTorch",
    "power bi": "Power BI",
    "tableau": "Tableau",
    "excel": "Microsoft Excel",
    "figma": "Figma",
    "selenium": "Selenium",
    "playwright": "Playwright",
    "cypress": "Cypress",
    "jest": "Jest",
    "pytest": "pytest",
    "junit": "JUnit",
    "spring boot": "Spring Boot",
    "java": "Java",
    "c++": "C++",
    "c#": "C#",
    "php": "PHP",
    "scala": "Scala",
    "kotlin": "Kotlin",
    "swift": "Swift",
    "flutter": "Flutter",
    "android sdk": "Android SDK",
    "ios sdk": "iOS SDK",
    "orm": "ORM",
    "apache spark": "Apache Spark",
    "airflow": "Apache Airflow",
    "kafka": "Apache Kafka",
    "snowflake": "Snowflake",
    "hadoop basics": "Hadoop",
    "data warehouses": "Data Warehousing",
    "data pipelines": "Data Pipelines",
    "etl/elt": "ETL / ELT",
    "data modeling": "Data Modeling",
    "data visualization": "Data Visualization",
    "data cleaning": "Data Cleaning",
    "eda": "Exploratory Data Analysis (EDA)",
    "statistics": "Statistics",
    "probability": "Probability",
    "machine learning": "Machine Learning",
    "deep learning": "Deep Learning",
    "nlp": "Natural Language Processing (NLP)",
    "computer vision": "Computer Vision",
    "generative ai": "Generative AI",
    "ai-assisted development": "AI-Assisted Development",
    "mlops basics": "MLOps",
    "feature engineering": "Feature Engineering",
    "model evaluation": "Model Evaluation",
    "wireframing": "Wireframing",
    "prototyping": "Prototyping",
    "user research": "User Research",
    "information architecture": "Information Architecture",
    "interaction design": "Interaction Design",
    "visual design": "Visual Design",
    "typography": "Typography",
    "color theory": "Color Theory",
    "design systems": "Design Systems",
    "usability testing": "Usability Testing",
    "user flows": "User Flows",
    "ux documentation": "UX Documentation",
    "ui development": "UI Development",
    "ui design": "UI Design",
    "ux design": "UX Design",
    "ui/ux design": "UI/UX Design",
    "responsive design": "Responsive Design",
    "accessibility": "Web Accessibility",
    "web security": "Web Security",
    "authentication": "Authentication",
    "authorization": "Authorization",
    "database design": "Database Design",
    "system design": "System Design",
    "software design": "Software Design",
    "problem solving": "Problem Solving",
    "debugging": "Debugging",
    "browser devtools": "Browser DevTools",
    "npm": "npm",
    "performance optimization": "Performance Optimization",
    "cloud basics": "Cloud Computing Basics",
    "cloud platforms": "Cloud Platforms",
    "deployment": "Deployment",
    "microservices": "Microservices",
    "distributed systems": "Distributed Systems",
    "business intelligence": "Business Intelligence",
    "reporting": "Reporting",
    "data interpretation": "Data Interpretation",
    "jupyter": "Jupyter Notebook",
    "experimentation": "Experimentation",
    "communication": "Communication",
    "team collaboration": "Team Collaboration",
    "time management": "Time Management",
    "leadership": "Leadership",
    "code review": "Code Review",
}

# Precompute collapsed alphanumeric lookup (stripping all punctuation/spaces)
COLLAPSED_SKILL_SYNONYMS: Dict[str, str] = {}
for _k, _v in SKILL_SYNONYMS.items():
    _coll = re.sub(r'[^a-z0-9]', '', _k)
    if _coll and _coll not in COLLAPSED_SKILL_SYNONYMS:
        COLLAPSED_SKILL_SYNONYMS[_coll] = _v


def normalize_skill_name(skill: str) -> str:
    """
    Robust, reusable skill normalizer.
    
    Handles:
    - Case insensitivity (REST API -> rest apis)
    - Punctuation, smart quotes, apostrophes (restapi's, REST API's -> rest apis)
    - Hyphens, slashes, underscores (rest-api, rest_api -> rest apis)
    - Concatenation variations (restapi, restapis -> rest apis)
    - Singular / plural forms (api vs apis, microservice vs microservices)
    - Common noise suffixes (development, programming, basics, framework)
    - Preserves all valid skills (Python, Django, Flask, SQL, Git, etc.)
    """
    if not skill:
        return ""
    
    s_raw = str(skill).strip()
    if not s_raw:
        return ""

    # 1. Normalize unicode smart quotes and apostrophes
    s = s_raw.lower()
    s = s.replace("’", "'").replace("‘", "'").replace("`", "'").replace("´", "'")
    s = s.replace("“", '"').replace("”", '"')
    
    # Strip leading bullets, numbers, dashes, asterisks (e.g. "• restapi's", "1. Python", "- Django")
    s = re.sub(r"^[\s*•\-\–\—\+\d\.\)]+", "", s).strip()
    # Strip enclosing quotes, brackets, parentheses
    s = re.sub(r"[\(\)\[\]\{\}]", " ", s)
    s = s.strip("'\".,;:")
    s = re.sub(r"\s+", " ", s).strip()

    if not s:
        return ""

    # 2. Direct exact match in SKILL_SYNONYMS
    if s in SKILL_SYNONYMS:
        return SKILL_SYNONYMS[s]

    # 3. Apostrophe handling (e.g. restapi's -> restapi or restapis, api's -> api or apis)
    s_no_apos_s = re.sub(r"['’]s\b", "", s).strip()
    if s_no_apos_s in SKILL_SYNONYMS:
        return SKILL_SYNONYMS[s_no_apos_s]

    s_plural_s = re.sub(r"['’]s\b", "s", s).strip()
    if s_plural_s in SKILL_SYNONYMS:
        return SKILL_SYNONYMS[s_plural_s]

    s_no_apos = s.replace("'", "").strip()
    if s_no_apos in SKILL_SYNONYMS:
        return SKILL_SYNONYMS[s_no_apos]

    # 4. Normalize separators (hyphens, underscores, slashes to space)
    s_spaced = re.sub(r'[-_/]', ' ', s)
    s_spaced = re.sub(r'\s+', ' ', s_spaced).strip()
    if s_spaced in SKILL_SYNONYMS:
        return SKILL_SYNONYMS[s_spaced]

    s_spaced_no_apos = re.sub(r"['’]s\b", "", s_spaced).strip()
    if s_spaced_no_apos in SKILL_SYNONYMS:
        return SKILL_SYNONYMS[s_spaced_no_apos]

    # 5. Collapsed alphanumeric lookup (handles restapi, restapis, fast-api, reactjs, etc.)
    s_collapsed = re.sub(r'[^a-z0-9]', '', s)
    if s_collapsed in COLLAPSED_SKILL_SYNONYMS:
        return COLLAPSED_SKILL_SYNONYMS[s_collapsed]

    s_coll_no_s = re.sub(r'[^a-z0-9]', '', s_no_apos_s)
    if s_coll_no_s in COLLAPSED_SKILL_SYNONYMS:
        return COLLAPSED_SKILL_SYNONYMS[s_coll_no_s]

    # 6. Singular / Plural variation
    if s.endswith("s") and len(s) > 3 and not s.endswith("ss"):
        sing = s[:-1]
        if sing in SKILL_SYNONYMS:
            return SKILL_SYNONYMS[sing]
        sing_coll = re.sub(r'[^a-z0-9]', '', sing)
        if sing_coll in COLLAPSED_SKILL_SYNONYMS:
            return COLLAPSED_SKILL_SYNONYMS[sing_coll]
    else:
        plur = s + "s"
        if plur in SKILL_SYNONYMS:
            return SKILL_SYNONYMS[plur]
        plur_coll = re.sub(r'[^a-z0-9]', '', plur)
        if plur_coll in COLLAPSED_SKILL_SYNONYMS:
            return COLLAPSED_SKILL_SYNONYMS[plur_coll]

    # 7. Strip trailing noise words e.g. "REST API development" -> "REST API"
    s_clean = re.sub(r"\s+(?:development|integration|framework|library|basics|fundamentals|programming|language|tools?|skills?)$", "", s).strip()
    if s_clean in SKILL_SYNONYMS:
        return SKILL_SYNONYMS[s_clean]
    s_clean_no_apos = re.sub(r"['’]s\b", "", s_clean).strip()
    if s_clean_no_apos in SKILL_SYNONYMS:
        return SKILL_SYNONYMS[s_clean_no_apos]

    # 8. Return cleaned lowercase fallback
    return s


def to_canonical_display_name(skill: str) -> str:
    """Return the professional canonical display name for a skill (e.g. 'restapi\\'s' -> 'REST APIs')."""
    if not skill:
        return ""
    norm = normalize_skill_name(skill)
    if norm in CANONICAL_SKILL_DISPLAY:
        return CANONICAL_SKILL_DISPLAY[norm]
    # Acronym and capitalization fallback
    clean = norm.replace('_', ' ')
    acronyms = {"sql", "html", "css", "api", "apis", "rest", "rest apis", "dsa", "oop", "sdlc", "aws", "gcp", "eda", "etl"}
    words = clean.split()
    return " ".join([w.upper() if w.lower() in acronyms else w.capitalize() for w in words])


# Skill Relationship Graph: If candidate has source skill, gives partial familiarity credit (0.5) to target skill
SKILL_RELATIONSHIPS: Dict[str, List[str]] = {
    "react": ["next.js", "ui development"],
    "javascript": ["typescript"],
    "html": ["responsive design"],
    "css": ["responsive design"],
    "python": ["data analysis"],
    "sql": ["database design"],
    "figma": ["wireframing", "prototyping", "visual design"],
    "machine learning": ["deep learning", "feature engineering"],
    "selenium": ["playwright", "test automation"],
    "playwright": ["test automation"],
    "jest": ["testing"],
    "docker": ["ci/cd"],
}


# Concise 1-sentence explanations for why each skill is needed and how to improve it
SKILL_EXPLANATIONS: Dict[str, Dict[str, str]] = {
    "javascript": {
        "why": "Essential for client-side interactivity, DOM manipulation, and dynamic web application logic.",
        "how": "Practice ES6+ syntax, asynchronous programming (Promises/async-await), and build interactive web widgets."
    },
    "typescript": {
        "why": "Provides static typing that prevents runtime bugs and significantly improves large codebase maintainability.",
        "how": "Migrate existing JavaScript modules to TypeScript by defining strict interfaces, generics, and return types."
    },
    "html": {
        "why": "Provides the semantic backbone and structural foundation for all accessible web interfaces.",
        "how": "Build responsive web pages following semantic HTML5 tags and accessibility standards (WCAG)."
    },
    "css": {
        "why": "Controls responsive styling, flexible layouts, and cross-device presentation.",
        "how": "Master CSS Flexbox, CSS Grid layouts, media queries, and responsive component styling."
    },
    "react": {
        "why": "The industry-standard library for building modular, reusable component-based web applications.",
        "how": "Build small React projects practicing components, hooks (useState, useEffect), state, and routing."
    },
    "next.js": {
        "why": "Enables server-side rendering, static site generation, and production-grade full-stack web architectures.",
        "how": "Build a full-stack Next.js application leveraging App Router, server components, and API routes."
    },
    "vue.js": {
        "why": "A progressive framework offering an approachable reactivity system and component architecture.",
        "how": "Build a single-page app utilizing Vue 3 Composition API, reactive state, and Pinia store."
    },
    "angular": {
        "why": "Comprehensive enterprise frontend framework featuring built-in dependency injection and TypeScript.",
        "how": "Learn Angular modules, components, services, RxJS observables, and routing."
    },
    "node.js": {
        "why": "Enables JavaScript-based backend development and high-concurrency event-driven microservices.",
        "how": "Build backend HTTP services in Node.js with Express, implementing routing, middleware, and file I/O."
    },
    "express.js": {
        "why": "Minimalist web framework for building fast REST APIs and backend server routes in Node.js.",
        "how": "Create CRUD REST API endpoints with request validation, middleware, and JSON response formatting."
    },
    "rest apis": {
        "why": "Allows client and server systems to communicate and exchange structured JSON payloads reliably.",
        "how": "Design and build RESTful endpoints using standard HTTP verbs, status codes, and test with Postman."
    },
    "graphql": {
        "why": "Allows clients to request precisely the data they need, reducing network over-fetching.",
        "how": "Define GraphQL schemas, queries, and mutations using Apollo Server or GraphQL Yoga."
    },
    "sql": {
        "why": "Essential for querying, joining, aggregating, and manipulating relational database records.",
        "how": "Practice complex SQL joins, subqueries, indexing, and aggregation on PostgreSQL or MySQL datasets."
    },
    "postgresql": {
        "why": "Robust enterprise relational database known for ACID compliance, indexing, and JSON support.",
        "how": "Model relational schemas, practice normalization, create indices, and write optimized queries in PostgreSQL."
    },
    "mysql": {
        "why": "Popular open-source relational database powering enterprise web systems and content platforms.",
        "how": "Set up a local MySQL instance, write schema migrations, and connect it with backend applications."
    },
    "mongodb": {
        "why": "Leading document-oriented NoSQL database for flexible, rapidly evolving JSON data models.",
        "how": "Build a CRUD application using MongoDB and Mongoose/PyMongo, practicing aggregation pipelines."
    },
    "redis": {
        "why": "In-memory key-value store used for sub-millisecond caching, session storage, and rate limiting.",
        "how": "Integrate Redis into an API to cache frequent database query results and manage user sessions."
    },
    "git": {
        "why": "Industry-standard version control system for tracking changes and collaborating in engineering teams.",
        "how": "Practice branching, merging, rebasing, resolving conflicts, and managing repositories on GitHub."
    },
    "linux": {
        "why": "The dominant operating system powering cloud servers, containers, and deployment infrastructure.",
        "how": "Learn basic bash shell navigation, file permissions, process management, and SSH server access."
    },
    "docker": {
        "why": "Containerizes applications ensuring consistent, reproducible environments across dev and production.",
        "how": "Write Dockerfiles, build container images, and orchestrate multi-container setups using Docker Compose."
    },
    "ci/cd": {
        "why": "Automates testing, building, and zero-downtime deployment pipelines for reliable software releases.",
        "how": "Configure GitHub Actions workflows to automatically run tests and linting on every pull request."
    },
    "aws": {
        "why": "Leading cloud provider offering scalable compute, storage, databases, and serverless infrastructure.",
        "how": "Deploy applications using AWS services like S3, EC2, Lambda, and RDS."
    },
    "authentication": {
        "why": "Ensures only verified users can access system resources and protects sensitive user data.",
        "how": "Implement JWT (JSON Web Tokens) or OAuth2 authentication flows with password hashing."
    },
    "authorization": {
        "why": "Enforces role-based access control (RBAC) ensuring users only perform authorized operations.",
        "how": "Create middleware that verifies user roles before granting endpoint access."
    },
    "web security": {
        "why": "Protects applications from common vulnerabilities like SQL injection, XSS, CSRF, and data leaks.",
        "how": "Implement OWASP top-10 security practices, CORS policies, secure headers, and input sanitization."
    },
    "testing": {
        "why": "Guarantees software correctness, catches regressions early, and supports confident refactoring.",
        "how": "Write unit and integration tests covering happy paths, edge cases, and error states."
    },
    "test automation": {
        "why": "Automates repetitive test execution to validate software stability across multiple builds rapidly.",
        "how": "Build an automated testing suite using Selenium or Playwright covering end-to-end user workflows."
    },
    "selenium": {
        "why": "Widely adopted framework for cross-browser web automation and regression testing.",
        "how": "Write WebDriver scripts in Python or Java to automate browser navigation, form inputs, and assertions."
    },
    "playwright": {
        "why": "Modern end-to-end browser automation framework for validating user flows across browsers.",
        "how": "Write automated end-to-end tests for login, form submissions, and UI navigation in Playwright."
    },
    "jest": {
        "why": "Standard testing framework for JavaScript and React applications providing fast mock testing.",
        "how": "Write unit tests for utility functions and React components with snapshot and DOM assertions."
    },
    "dsa": {
        "why": "Fundamental for algorithmic problem-solving, optimal time/space complexity, and scalability.",
        "how": "Practice arrays, linked lists, trees, graphs, dynamic programming, and sorting on LeetCode."
    },
    "oop": {
        "why": "Organizes code into modular, reusable, and maintainable classes via encapsulation and polymorphism.",
        "how": "Design object-oriented class hierarchies following SOLID design principles in Python or Java."
    },
    "system design": {
        "why": "Crucial for architecting scalable, fault-tolerant, high-concurrency distributed systems.",
        "how": "Study load balancing, caching, horizontal scaling, database sharding, and microservice patterns."
    },
    "database design": {
        "why": "Ensures clean data modeling, relational integrity, optimal indexing, and minimal redundancy.",
        "how": "Practice Entity-Relationship (ER) diagramming, table normalization (3NF), and indexing strategies."
    },
    "debugging": {
        "why": "Enables rapid isolation and resolution of software defects, runtime exceptions, and bottlenecks.",
        "how": "Use interactive debuggers (PDB / browser DevTools) and analyze stack traces and log outputs systematically."
    },
    "browser devtools": {
        "why": "Essential for inspecting DOM elements, debugging scripts, and profiling network performance in real-time.",
        "how": "Inspect network waterfall charts, console errors, responsive viewports, and CSS rules in DevTools."
    },
    "api integration": {
        "why": "Allows frontend applications to fetch dynamic data from backend endpoints and external services.",
        "how": "Write asynchronous fetch/axios service layers with robust error handling and loading indicators."
    },
    "responsive design": {
        "why": "Ensures digital interfaces adapt smoothly to smartphones, tablets, laptops, and desktop viewports.",
        "how": "Implement mobile-first CSS media queries, fluid typography, and flexible grid layouts."
    },
    "accessibility": {
        "why": "Guarantees digital products can be navigated by users with visual or motor impairments (WCAG).",
        "how": "Add ARIA labels, semantic tags, keyboard navigation, and high-contrast color styling."
    },
    "performance optimization": {
        "why": "Improves application loading speed, user retention, and backend compute efficiency.",
        "how": "Optimize bundle sizes, lazy load assets, memoize expensive calculations, and implement caching."
    },
    "python": {
        "why": "Versatile programming language widely used in backend APIs, data pipelines, automation, and AI/ML.",
        "how": "Practice Pythonic idioms, list comprehensions, OOP, type hints, and standard libraries."
    },
    "java": {
        "why": "Enterprise-standard strongly typed language powering high-scale banking and backend microservices.",
        "how": "Build backend services in Java practicing collections, streams, concurrency, and Spring Boot."
    },
    "c++": {
        "why": "High-performance language essential for low-latency systems, game engines, and embedded software.",
        "how": "Practice memory management, pointers, references, STL containers, and algorithms in modern C++."
    },
    "kotlin": {
        "why": "The modern, expressive programming language officially recommended for native Android development.",
        "how": "Build Android apps utilizing Kotlin coroutines, null safety, and Jetpack Compose UI."
    },
    "swift": {
        "why": "Fast and safe programming language powering native iOS, iPadOS, and macOS applications.",
        "how": "Build iOS apps in Xcode practicing Swift fundamentals, optionals, and SwiftUI."
    },
    "flutter": {
        "why": "Cross-platform UI toolkit for building natively compiled mobile, web, and desktop apps from one codebase.",
        "how": "Build a cross-platform mobile application practicing Flutter widgets, state management, and navigation."
    },
    "react native": {
        "why": "Enables writing cross-platform native iOS and Android mobile apps using React and JavaScript.",
        "how": "Build a React Native app integrating native device sensors, navigation, and API calls."
    },
    "android sdk": {
        "why": "Provides the essential framework libraries and APIs for building native Android applications.",
        "how": "Develop native Android activities, fragments, services, and permissions in Android Studio."
    },
    "ios sdk": {
        "why": "Provides the core platform APIs and frameworks required for native iOS application engineering.",
        "how": "Develop iOS applications leveraging UIKit/SwiftUI, view controllers, and Apple framework APIs."
    },
    "django": {
        "why": "Batteries-included Python framework providing built-in ORM, admin dashboard, and robust web security.",
        "how": "Build a web application using Django models, views, templates, forms, and authentication."
    },
    "fastapi": {
        "why": "Modern, high-performance asynchronous Python framework with automatic interactive OpenAPI documentation.",
        "how": "Build high-throughput RESTful microservices with Pydantic validation and async route handlers."
    },
    "spring boot": {
        "why": "The leading enterprise Java framework for building production-grade microservices and APIs.",
        "how": "Build microservices in Spring Boot with Spring Data JPA, dependency injection, and security."
    },
    "excel": {
        "why": "The baseline business tool for structured tabular calculations, quick modeling, and executive reports.",
        "how": "Master VLOOKUP/XLOOKUP, Pivot Tables, advanced formulas, and interactive chart creation."
    },
    "pandas": {
        "why": "The premier Python library for tabular data manipulation, cleaning, aggregation, and filtering.",
        "how": "Practice DataFrame indexing, grouping, merging, pivoting, and handling missing data with Pandas."
    },
    "numpy": {
        "why": "Provides high-performance multi-dimensional array operations and scientific computing routines.",
        "how": "Practice vectorized mathematical operations, matrix manipulations, and slicing with NumPy."
    },
    "data cleaning": {
        "why": "Crucial first step in data analytics to eliminate null values, duplicates, and outliers.",
        "how": "Build data cleaning scripts that normalize dates, impute missing values, and handle dirty records."
    },
    "eda": {
        "why": "Uncovers distributions, correlations, patterns, and anomalies in raw datasets before modeling.",
        "how": "Generate correlation heatmaps, histograms, box plots, and summary statistics to understand data trends."
    },
    "statistics": {
        "why": "Provides the mathematical foundation for hypothesis testing, distributions, and inferential analytics.",
        "how": "Study probability distributions, confidence intervals, hypothesis testing (p-values, t-tests), and regression."
    },
    "data visualization": {
        "why": "Transforms complex numbers into clear, intuitive visual charts that business stakeholders understand.",
        "how": "Create informative charts using Matplotlib, Seaborn, or Plotly with polished color scales and labels."
    },
    "power bi": {
        "why": "Industry-standard business intelligence tool for interactive executive dashboards and DAX formulas.",
        "how": "Build multi-page Power BI reports connecting to SQL databases and publish interactive dashboards."
    },
    "tableau": {
        "why": "Powerful visual analytics platform for enterprise data exploration, dashboards, and storytelling.",
        "how": "Connect Tableau to data sources, create calculated fields, parameters, and interactive dashboards."
    },
    "data modeling": {
        "why": "Structures analytical data schemas for fast query performance and minimal reporting ambiguity.",
        "how": "Design star schemas, snowflake schemas, dimension tables, and fact tables using Kimball methodology."
    },
    "etl/elt": {
        "why": "Extracts data from transactional databases, transforms it, and loads it into analytical warehouses.",
        "how": "Build a Python/SQL ETL pipeline that extracts API records, transforms data, and loads it into PostgreSQL."
    },
    "apache spark": {
        "why": "Distributed data processing engine capable of computing massive datasets in parallel in memory.",
        "how": "Write PySpark scripts to perform distributed transformations, filtering, and joins at scale."
    },
    "airflow": {
        "why": "Industry standard for orchestrating, scheduling, and monitoring complex multi-stage DAG data pipelines.",
        "how": "Define an Apache Airflow Directed Acyclic Graph (DAG) with PythonOperators to schedule automated data jobs."
    },
    "kafka": {
        "why": "High-throughput distributed event streaming platform used for real-time streaming data architectures.",
        "how": "Set up a Kafka broker, write producer and consumer services in Python, and process streaming events."
    },
    "data warehouses": {
        "why": "Centralized repositories optimized for fast analytical SQL queries across petabytes of historical data.",
        "how": "Learn columnar storage principles and analytical SQL queries in Snowflake or Google BigQuery."
    },
    "data pipelines": {
        "why": "Automates the continuous flow of data from source systems to analytics and machine learning models.",
        "how": "Build resilient data pipelines with error handling, logging, schema validation, and retry logic."
    },
    "distributed systems": {
        "why": "Essential for understanding data consistency, partitioning, fault tolerance, and network latency at scale.",
        "how": "Study CAP theorem, consensus protocols (Raft), replication strategies, and horizontal partitioning."
    },
    "machine learning": {
        "why": "Enables software to automatically learn predictive patterns from historical data without explicit rules.",
        "how": "Train classification and regression models in Scikit-Learn practicing cross-validation and tuning."
    },
    "scikit-learn": {
        "why": "The standard Python machine learning library providing unified APIs for preprocessing and modeling.",
        "how": "Build end-to-end ML pipelines with ColumnTransformer, StandardScaler, estimators, and GridSearchCV."
    },
    "feature engineering": {
        "why": "Directly elevates machine learning accuracy by transforming raw data into high-signal predictors.",
        "how": "Practice one-hot encoding, target encoding, interaction features, handling skewness, and scaling."
    },
    "model evaluation": {
        "why": "Rigourously validates model generalization, preventing overfitting and measuring real-world accuracy.",
        "how": "Calculate confusion matrices, Precision, Recall, F1-score, ROC-AUC, and perform k-fold cross-validation."
    },
    "deep learning": {
        "why": "Powers state-of-the-art breakthroughs in computer vision, natural language processing, and generative AI.",
        "how": "Build neural networks in PyTorch or TensorFlow practicing forward pass, backpropagation, and loss functions."
    },
    "pytorch": {
        "why": "The leading deep learning framework in AI research and production computer vision and NLP systems.",
        "how": "Implement custom PyTorch nn.Modules, write training loops with autograd, and fine-tune pre-trained models."
    },
    "tensorflow": {
        "why": "Google-backed production deep learning platform for building and serving neural networks at scale.",
        "how": "Build neural network architectures using Keras APIs, callbacks, and export models for serving."
    },
    "nlp": {
        "why": "Enables applications to understand, analyze, and generate human language text.",
        "how": "Practice tokenization, TF-IDF, word embeddings, sentiment analysis, and transformer models in HuggingFace."
    },
    "computer vision": {
        "why": "Enables applications to extract meaningful information from digital images and video feeds.",
        "how": "Build image classification and object detection pipelines using OpenCV and convolutional networks (CNNs)."
    },
    "mlops basics": {
        "why": "Automates the deployment, monitoring, and versioning of machine learning models in production.",
        "how": "Package a trained model inside a Dockerized FastAPI service and log inference metrics."
    },
    "figma": {
        "why": "The industry-standard collaborative vector design and UI/UX prototyping platform.",
        "how": "Design interactive UI wireframes, high-fidelity prototypes, and maintain reusable component libraries in Figma."
    },
    "ui design": {
        "why": "Crafts aesthetic appeal, visual hierarchy, consistent typography, and polished user interface screens.",
        "how": "Study visual hierarchy, grid layouts, white space, typography scales, and accessible color palettes."
    },
    "ux design": {
        "why": "Focuses on user journey flows, task ease, and reducing friction across digital product experiences.",
        "how": "Map customer user journeys, identify usability pain points, and design friction-free navigation flows."
    },
    "user research": {
        "why": "Uncovers genuine user needs, motivations, and pain points through qualitative and quantitative studies.",
        "how": "Conduct user interviews, synthesize empathy maps, create personas, and extract user requirements."
    },
    "wireframing": {
        "why": "Creates the structural blueprint and content hierarchy of screens before investing in visual styling.",
        "how": "Sketch low-fidelity wireframes focusing on layout, content structure, and primary calls to action."
    },
    "prototyping": {
        "why": "Demonstrates interactive transitions and screen flows before development begins.",
        "how": "Link frames in Figma to create clickable interactive prototypes with realistic transitions and states."
    },
    "visual design": {
        "why": "Crafts aesthetic appeal, brand identity, visual hierarchy, and polished presentation.",
        "how": "Study grid layouts, white space, balance, contrast, and visual rhythm across digital interfaces."
    },
    "information architecture": {
        "why": "Organizes and labels content logically so users can effortlessly find what they need.",
        "how": "Conduct card sorting exercises, build sitemaps, and structure intuitive application navigation trees."
    },
    "usability testing": {
        "why": "Validates design usability with real users to identify friction points and task blockers early.",
        "how": "Write usability test scripts, observe user sessions, record completion rates, and iterate designs."
    },
    "design systems": {
        "why": "Provides reusable UI component libraries, tokens, and standards ensuring brand consistency at scale.",
        "how": "Build a design system in Figma specifying colors, typography, buttons, inputs, and component variants."
    },
    "agile/scrum": {
        "why": "Standard methodology for collaborative, iterative software delivery in modern engineering teams.",
        "how": "Participate in sprint planning, daily standups, sprint reviews, and backlog refinement using Jira."
    },
    "sdlc": {
        "why": "Encompasses the complete lifecycle of software: planning, designing, building, testing, and deploying.",
        "how": "Study SDLC phases, code review processes, versioning, release management, and post-deployment monitoring."
    },
    "problem solving": {
        "why": "Core foundational attribute for decomposing complex technical requirements into modular solutions.",
        "how": "Break down real-world engineering problems systematically through pseudocode and edge case analysis."
    },
    "team collaboration": {
        "why": "Essential for effectively building large-scale software products across cross-functional teams.",
        "how": "Practice proactive code reviews, constructive feedback, technical documentation, and pair programming."
    },
    "communication": {
        "why": "Ensures technical ideas, tradeoffs, and project timelines are communicated clearly to teammates and stakeholders.",
        "how": "Practice writing clean pull request descriptions, documentation, and presenting technical demos."
    },
}


# The 12 Comprehensive Role Matrices with Prioritized Tiers
ROLE_MATRICES: Dict[str, Dict[str, Any]] = {
    # 1. Full Stack Developer
    "full_stack_developer": {
        "canonical_title": "Full Stack Developer",
        "category": "Full Stack Development",
        "icon": "🎯",
        "dataset_titles": ["Full Stack Developer", "Software Engineer"],
        "min_experience_years": 2,
        "salary_range": "₹3.5 - 5.5 LPA",
        "education_requirement": "Bachelor's in Computer Science|Diploma in IT",
        "core": [
            "html", "css", "javascript", "typescript", "react", "node.js",
            "rest apis", "sql", "database design", "git", "authentication", "authorization"
        ],
        "important": [
            "mongodb", "docker", "testing", "web security", "api integration",
            "responsive design", "debugging", "linux"
        ],
        "recommended": [
            "graphql", "redis", "aws", "ci/cd", "system design",
            "performance optimization", "accessibility"
        ],
        "optional": [
            "playwright", "jest", "next.js", "microservices", "ai-assisted development"
        ],
        "professional": [
            "agile/scrum", "sdlc", "problem solving", "team collaboration", "communication"
        ]
    },

    # 2. Frontend Developer
    "frontend_developer": {
        "canonical_title": "Frontend Developer",
        "category": "Frontend Development",
        "icon": "🎨",
        "dataset_titles": ["Frontend Developer", "Web Designer", "UI Designer"],
        "min_experience_years": 1,
        "salary_range": "₹3.2 - 5.0 LPA",
        "education_requirement": "Bachelor's in Computer Science|Diploma in IT",
        "core": [
            "html", "css", "javascript", "typescript", "react", "responsive design",
            "rest apis", "git"
        ],
        "important": [
            "vue.js", "angular", "accessibility", "browser devtools", "ui development",
            "testing", "api integration"
        ],
        "recommended": [
            "next.js", "performance optimization", "figma", "npm"
        ],
        "optional": [
            "playwright", "jest", "cypress"
        ],
        "professional": [
            "agile/scrum", "problem solving", "team collaboration"
        ]
    },

    # 3. Backend Developer
    "backend_developer": {
        "canonical_title": "Backend Developer",
        "category": "Backend Development",
        "icon": "⚙️",
        "dataset_titles": ["Backend Developer", "Java Backend Developer", "PHP Developer"],
        "min_experience_years": 2,
        "salary_range": "₹3.5 - 5.2 LPA",
        "education_requirement": "Bachelor's in Computer Science",
        "core": [
            "python", "node.js", "java", "rest apis", "sql", "database design",
            "git", "authentication", "authorization"
        ],
        "important": [
            "postgresql", "mysql", "mongodb", "docker", "linux", "api integration",
            "testing", "orm", "web security", "debugging"
        ],
        "recommended": [
            "fastapi", "django", "express.js", "spring boot", "redis", "graphql",
            "cloud basics", "system design", "ci/cd"
        ],
        "optional": [
            "kubernetes", "microservices", "kafka"
        ],
        "professional": [
            "agile/scrum", "sdlc", "code review", "problem solving"
        ]
    },

    # 4. Web Developer
    "web_developer": {
        "canonical_title": "Web Developer",
        "category": "Web Development",
        "icon": "🌐",
        "dataset_titles": ["Web Designer", "Website Administrator", "Frontend Developer"],
        "min_experience_years": 1,
        "salary_range": "₹2.8 - 4.5 LPA",
        "education_requirement": "Bachelor's in Computer Science|Diploma in IT",
        "core": [
            "html", "css", "javascript", "responsive design", "git"
        ],
        "important": [
            "react", "vue.js", "rest apis", "sql", "browser devtools",
            "accessibility", "web security"
        ],
        "recommended": [
            "node.js", "database design", "deployment", "performance optimization"
        ],
        "optional": [
            "typescript", "next.js"
        ],
        "professional": [
            "problem solving", "agile/scrum", "time management"
        ]
    },

    # 5. Software Developer
    "software_developer": {
        "canonical_title": "Software Developer",
        "category": "Software Engineering",
        "icon": "💻",
        "dataset_titles": ["Software Engineer", "Software Architect", "Software Test Engineer"],
        "min_experience_years": 2,
        "salary_range": "₹3.5 - 5.5 LPA",
        "education_requirement": "Bachelor's in Computer Science|Bachelor's in Engineering",
        "core": [
            "python", "java", "c++", "oop", "dsa", "git", "sql", "problem solving"
        ],
        "important": [
            "software design", "database design", "rest apis", "testing",
            "debugging", "linux"
        ],
        "recommended": [
            "system design", "ci/cd", "sdlc"
        ],
        "optional": [
            "cloud basics", "docker", "microservices"
        ],
        "professional": [
            "agile/scrum", "code review", "team collaboration", "communication"
        ]
    },

    # 6. App / Mobile Developer
    "mobile_developer": {
        "canonical_title": "App / Mobile Developer",
        "category": "Mobile App Development",
        "icon": "📱",
        "dataset_titles": ["Mobile Developer Android", "Mobile Developer iOS"],
        "min_experience_years": 2,
        "salary_range": "₹3.2 - 5.0 LPA",
        "education_requirement": "Bachelor's in Computer Science",
        "core": [
            "kotlin", "swift", "flutter", "react native", "rest apis", "git"
        ],
        "important": [
            "android sdk", "ios sdk", "responsive design", "debugging", "testing"
        ],
        "recommended": [
            "deployment", "performance optimization", "ui development"
        ],
        "optional": [
            "offline sync", "cloud basics"
        ],
        "professional": [
            "agile/scrum", "problem solving", "team collaboration"
        ]
    },

    # 7. UI/UX Designer
    "ui_ux_designer": {
        "canonical_title": "UI/UX Designer",
        "category": "Design & User Experience",
        "icon": "✨",
        "dataset_titles": ["UX Designer", "UI Designer", "Web Designer", "Graphic Designer"],
        "min_experience_years": 1,
        "salary_range": "₹3.0 - 4.8 LPA",
        "education_requirement": "Bachelor's in Design|Bachelor's in Computer Science",
        "core": [
            "figma", "ui design", "ux design", "user research",
            "wireframing", "prototyping", "visual design"
        ],
        "important": [
            "information architecture", "usability testing", "responsive design",
            "accessibility", "design systems", "typography", "color theory"
        ],
        "recommended": [
            "user flows", "interaction design", "ux documentation"
        ],
        "optional": [
            "html", "css", "javascript"
        ],
        "professional": [
            "presentation skills", "communication", "team collaboration"
        ]
    },

    # 8. Data Analyst
    "data_analyst": {
        "canonical_title": "Data Analyst",
        "category": "Data & Analytics",
        "icon": "📈",
        "dataset_titles": ["Data Analyst", "BI Analyst", "BI Developer"],
        "min_experience_years": 1,
        "salary_range": "₹3.0 - 4.8 LPA",
        "education_requirement": "Bachelor's in Mathematics|Bachelor's in Statistics|Bachelor's in Computer Science",
        "core": [
            "sql", "excel", "data cleaning", "data analysis", "statistics", "data visualization"
        ],
        "important": [
            "power bi", "tableau", "python", "pandas", "numpy", "eda", "reporting"
        ],
        "recommended": [
            "data modeling", "etl/elt", "business intelligence", "data interpretation"
        ],
        "optional": [
            "machine learning", "data warehouses"
        ],
        "professional": [
            "communication", "critical thinking", "team collaboration"
        ]
    },

    # 9. Data Engineer
    "data_engineer": {
        "canonical_title": "Data Engineer",
        "category": "Data Engineering",
        "icon": "🗄️",
        "dataset_titles": ["Data Engineer", "ETL Developer", "Analytics Engineer"],
        "min_experience_years": 2,
        "salary_range": "₹3.8 - 5.8 LPA",
        "education_requirement": "Bachelor's in Computer Science",
        "core": [
            "python", "sql", "etl/elt", "data modeling", "data pipelines", "apache spark"
        ],
        "important": [
            "airflow", "kafka", "data warehouses", "docker", "database design", "linux"
        ],
        "recommended": [
            "distributed systems", "scala", "java", "cloud platforms", "ci/cd"
        ],
        "optional": [
            "kubernetes", "hadoop basics"
        ],
        "professional": [
            "agile/scrum", "problem solving", "team collaboration"
        ]
    },

    # 10. Data Scientist
    "data_scientist": {
        "canonical_title": "Data Scientist",
        "category": "Data Science",
        "icon": "🔬",
        "dataset_titles": ["Data Scientist", "Data Analyst"],
        "min_experience_years": 2,
        "salary_range": "₹4.2 - 6.5 LPA",
        "education_requirement": "Master's in Data Science|Bachelor's in Mathematics|Bachelor's in Statistics",
        "core": [
            "python", "sql", "pandas", "numpy", "statistics", "probability",
            "machine learning", "scikit-learn"
        ],
        "important": [
            "eda", "data visualization", "feature engineering", "model evaluation", "jupyter"
        ],
        "recommended": [
            "deep learning", "nlp", "experimentation"
        ],
        "optional": [
            "mlops basics", "generative ai", "apache spark"
        ],
        "professional": [
            "communication", "critical thinking", "problem solving"
        ]
    },

    # 11. AI/ML Engineer
    "ai_ml_engineer": {
        "canonical_title": "AI/ML Engineer",
        "category": "Artificial Intelligence",
        "icon": "🤖",
        "dataset_titles": ["Machine Learning Engineer", "AI/ML Specialist", "Data Scientist"],
        "min_experience_years": 3,
        "salary_range": "₹4.5 - 7.0 LPA",
        "education_requirement": "Master's in Computer Science|Master's in AI",
        "core": [
            "python", "machine learning", "deep learning", "pytorch", "tensorflow",
            "scikit-learn"
        ],
        "important": [
            "model evaluation", "feature engineering", "nlp", "computer vision",
            "docker", "rest apis", "git"
        ],
        "recommended": [
            "mlops basics", "cloud platforms", "performance optimization"
        ],
        "optional": [
            "distributed systems", "kubernetes", "generative ai"
        ],
        "professional": [
            "problem solving", "agile/scrum", "team collaboration"
        ]
    },

    # 12. Automation Engineer
    "automation_engineer": {
        "canonical_title": "Automation Engineer",
        "category": "Quality Assurance & Automation",
        "icon": "⚡",
        "dataset_titles": ["QA Engineer", "Software Test Engineer"],
        "min_experience_years": 2,
        "salary_range": "₹3.0 - 4.8 LPA",
        "education_requirement": "Bachelor's in IT|QA Certification",
        "core": [
            "python", "java", "test automation", "selenium", "playwright",
            "rest apis", "git"
        ],
        "important": [
            "ci/cd", "testing", "debugging", "sql", "linux"
        ],
        "recommended": [
            "docker", "performance optimization", "api integration"
        ],
        "optional": [
            "cloud basics", "security"
        ],
        "professional": [
            "agile/scrum", "problem solving", "attention to detail", "communication"
        ]
    },
}


class RoleKnowledgeBase:
    """Manages the 12 role matrices enriched dynamically from job_roles.csv."""

    def __init__(self, dataset_path: Optional[str] = None):
        self.dataset_path = dataset_path or JOB_ROLES_CSV
        self.roles = ROLE_MATRICES
        self._dataset_df: Optional[pd.DataFrame] = None
        self._load_dataset_enrichment()

    def _load_dataset_enrichment(self):
        """Read job_roles.csv to dynamically enrich experience/salary/education without modifying the file."""
        if not os.path.exists(self.dataset_path):
            return
        try:
            self._dataset_df = pd.read_csv(self.dataset_path)
            for role_key, role_data in self.roles.items():
                dataset_titles = role_data.get("dataset_titles", [])
                for d_title in dataset_titles:
                    row_matches = self._dataset_df[self._dataset_df["Job Title"].str.lower() == d_title.lower()]
                    if not row_matches.empty:
                        matched_row = row_matches.iloc[0]
                        if "Experience Years" in matched_row and pd.notna(matched_row["Experience Years"]):
                            role_data["min_experience_years"] = int(matched_row["Experience Years"])
                        if "Education Requirement" in matched_row and pd.notna(matched_row["Education Requirement"]):
                            role_data["education_requirement"] = str(matched_row["Education Requirement"])
                        break
        except Exception:
            pass

    def get_all_roles(self) -> Dict[str, Dict[str, Any]]:
        """Return all 12 canonical roles with prioritized skill tiers."""
        return self.roles

    def get_role(self, role_key: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific role by key."""
        return self.roles.get(role_key)

    @staticmethod
    def get_salary_range(role_key: str, experience_years: float = 1.0) -> str:
        """Get grounded, real-world bare minimum market salary in LPA."""
        return get_realistic_salary_range(role_key, experience_years)

    @staticmethod
    def get_skill_guide(skill_key: str) -> Dict[str, str]:
        """Get concise 1-sentence why and how for a skill."""
        norm = normalize_skill_name(skill_key)
        guide = SKILL_EXPLANATIONS.get(norm)
        if guide:
            return guide
        clean_name = skill_key.replace('_', ' ').title()
        return {
            "why": f"Required for technical execution and industry standards in {clean_name}.",
            "how": f"Build practical hands-on projects and study documentation for {clean_name}."
        }


# Backward compatibility
ROLE_TAXONOMY = ROLE_MATRICES
SKILL_GUIDES = SKILL_EXPLANATIONS


def get_realistic_salary_range(role_key: str, experience_years: float = 1.0) -> str:
    """
    Calculate grounded, real-world bare minimum market salary (in LPA)
    based on the role and candidate's experience level.
    Avoids artificial/inflated numbers (e.g. 70-130K).
    """
    try:
        exp = max(0.0, float(experience_years if experience_years is not None else 1.0))
    except (ValueError, TypeError):
        exp = 1.0

    # Realistic Indian IT market salary tiers (in LPA):
    # (<= 1.0 yr entry/fresher, <= 2.0 yrs junior, <= 4.0 yrs mid, 5+ yrs senior)
    SALARY_TIERS: Dict[str, List[tuple]] = {
        "web_developer": [(1.0, "₹2.8 - 4.2 LPA"), (2.0, "₹3.2 - 4.8 LPA"), (4.0, "₹4.5 - 7.0 LPA"), (99.0, "₹7.5 - 12.0 LPA")],
        "frontend_developer": [(1.0, "₹3.0 - 4.5 LPA"), (2.0, "₹3.5 - 5.2 LPA"), (4.0, "₹5.0 - 8.0 LPA"), (99.0, "₹8.5 - 14.0 LPA")],
        "backend_developer": [(1.0, "₹3.2 - 4.8 LPA"), (2.0, "₹3.8 - 5.8 LPA"), (4.0, "₹5.5 - 9.0 LPA"), (99.0, "₹9.5 - 16.0 LPA")],
        "full_stack_developer": [(1.0, "₹3.5 - 5.0 LPA"), (2.0, "₹4.0 - 6.2 LPA"), (4.0, "₹6.0 - 10.0 LPA"), (99.0, "₹10.5 - 18.0 LPA")],
        "software_developer": [(1.0, "₹3.5 - 5.0 LPA"), (2.0, "₹3.8 - 5.8 LPA"), (4.0, "₹5.5 - 9.0 LPA"), (99.0, "₹9.5 - 16.0 LPA")],
        "mobile_developer": [(1.0, "₹3.2 - 4.8 LPA"), (2.0, "₹3.6 - 5.6 LPA"), (4.0, "₹5.2 - 8.5 LPA"), (99.0, "₹9.0 - 15.0 LPA")],
        "ui_ux_designer": [(1.0, "₹2.8 - 4.2 LPA"), (2.0, "₹3.2 - 5.0 LPA"), (4.0, "₹4.8 - 7.5 LPA"), (99.0, "₹8.0 - 13.5 LPA")],
        "data_analyst": [(1.0, "₹3.0 - 4.5 LPA"), (2.0, "₹3.2 - 5.0 LPA"), (4.0, "₹4.8 - 7.5 LPA"), (99.0, "₹8.0 - 13.5 LPA")],
        "data_engineer": [(1.0, "₹3.6 - 5.2 LPA"), (2.0, "₹4.2 - 6.5 LPA"), (4.0, "₹6.0 - 10.0 LPA"), (99.0, "₹10.5 - 18.0 LPA")],
        "data_scientist": [(1.0, "₹3.8 - 5.8 LPA"), (2.0, "₹4.5 - 7.0 LPA"), (4.0, "₹6.5 - 11.0 LPA"), (99.0, "₹11.5 - 20.0 LPA")],
        "ai_ml_engineer": [(1.0, "₹4.0 - 6.2 LPA"), (2.0, "₹4.8 - 7.5 LPA"), (4.0, "₹7.0 - 12.0 LPA"), (99.0, "₹12.0 - 22.0 LPA")],
        "automation_engineer": [(1.0, "₹3.0 - 4.5 LPA"), (2.0, "₹3.2 - 5.0 LPA"), (4.0, "₹4.8 - 7.5 LPA"), (99.0, "₹8.0 - 13.5 LPA")],
    }

    tiers = SALARY_TIERS.get(role_key, [
        (1.0, "₹3.0 - 4.5 LPA"), (2.0, "₹3.5 - 5.2 LPA"), (4.0, "₹5.0 - 8.0 LPA"), (99.0, "₹8.5 - 14.0 LPA")
    ])
    for max_yr, sal_str in tiers:
        if exp <= max_yr:
            return sal_str
    return tiers[-1][1]
