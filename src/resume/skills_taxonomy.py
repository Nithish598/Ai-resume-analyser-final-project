"""Comprehensive Domain-Specific Skills Taxonomy and Evidence Classifier for AI Recruitment Platform.

This module provides:
1. Controlled Canonical Taxonomy:
   - programming_languages (Python, Java, C, C++, C#, JavaScript, TypeScript, Go, Rust, Ruby, PHP, SQL, etc.)
   - databases (MySQL, PostgreSQL, Oracle DB, MongoDB, SQLite, Redis, MariaDB, etc.)
   - frameworks (React, Angular, Vue.js, Django, Flask, Spring Boot, etc.)
   - libraries (NumPy, Pandas, Matplotlib, Scikit-learn, TensorFlow, PyTorch, etc.)
   - ui_ux_tools (Figma, Adobe XD, Sketch, Photoshop, Illustrator, Canva, etc.)
   - office_productivity (Microsoft Excel, Microsoft Word, Microsoft PowerPoint, etc.)
   - tools (Git, GitHub, Docker, Postman, VS Code, Tally, SPSS, etc.)
   - cloud (AWS, Azure, GCP, etc.)
   - platforms (Android, iOS, Windows, Linux, Salesforce, WordPress, Shopify, etc.)
   - web_technologies (HTML5, CSS3, REST APIs, GraphQL, etc.)
   - technical_disciplines (DSA, OOP, System Design, Marketing Analytics, etc.)
   - soft_skills (Communication, Leadership, Teamwork, etc.)

2. Evidence Classifier:
   - Identifies whether a technology mention represents a confirmed skill vs. a career aspiration or negated mention.
   - MENTIONED TECHNOLOGY != CONFIRMED SKILL.
"""
import re
from typing import Dict, List, Set, Tuple, Optional, Any

# Mapping of normalized search pattern -> (Canonical Name, Category)
SKILLS_TAXONOMY: Dict[str, Tuple[str, str]] = {
    # ==================== PROGRAMMING LANGUAGES ====================
    "python": ("Python", "programming_languages"),
    "python3": ("Python", "programming_languages"),
    "python 3": ("Python", "programming_languages"),
    "java": ("Java", "programming_languages"),
    "javascript": ("JavaScript", "programming_languages"),
    "js": ("JavaScript", "programming_languages"),
    "typescript": ("TypeScript", "programming_languages"),
    "ts": ("TypeScript", "programming_languages"),
    "c": ("C", "programming_languages"),
    "c++": ("C++", "programming_languages"),
    "cpp": ("C++", "programming_languages"),
    "c plus plus": ("C++", "programming_languages"),
    "c#": ("C#", "programming_languages"),
    "csharp": ("C#", "programming_languages"),
    "c sharp": ("C#", "programming_languages"),
    "golang": ("Go", "programming_languages"),
    "go": ("Go", "programming_languages"),
    "rust": ("Rust", "programming_languages"),
    "ruby": ("Ruby", "programming_languages"),
    "php": ("PHP", "programming_languages"),
    "swift": ("Swift", "programming_languages"),
    "kotlin": ("Kotlin", "programming_languages"),
    "scala": ("Scala", "programming_languages"),
    "r": ("R", "programming_languages"),
    "dart": ("Dart", "programming_languages"),
    "sql": ("SQL", "programming_languages"),
    "pl/sql": ("PL/SQL", "programming_languages"),
    "plsql": ("PL/SQL", "programming_languages"),
    "t-sql": ("T-SQL", "programming_languages"),
    "tsql": ("T-SQL", "programming_languages"),
    "bash": ("Bash", "programming_languages"),
    "shell": ("Shell Scripting", "programming_languages"),
    "shell scripting": ("Shell Scripting", "programming_languages"),
    "powershell": ("PowerShell", "programming_languages"),
    "perl": ("Perl", "programming_languages"),
    "matlab": ("MATLAB", "programming_languages"),
    "julia": ("Julia", "programming_languages"),
    "assembly": ("Assembly", "programming_languages"),
    "objective-c": ("Objective-C", "programming_languages"),
    "visual basic": ("Visual Basic", "programming_languages"),
    "vb.net": ("Visual Basic", "programming_languages"),
    "haskell": ("Haskell", "programming_languages"),
    "elixir": ("Elixir", "programming_languages"),
    "clojure": ("Clojure", "programming_languages"),
    "lua": ("Lua", "programming_languages"),
    "solidity": ("Solidity", "programming_languages"),

    # ==================== DATABASES ====================
    "mysql": ("MySQL", "databases"),
    "my sql": ("MySQL", "databases"),
    "postgresql": ("PostgreSQL", "databases"),
    "postgres": ("PostgreSQL", "databases"),
    "oracle database": ("Oracle Database", "databases"),
    "oracle db": ("Oracle Database", "databases"),
    "oracle": ("Oracle Database", "databases"),
    "microsoft sql server": ("Microsoft SQL Server", "databases"),
    "ms sql server": ("Microsoft SQL Server", "databases"),
    "sql server": ("Microsoft SQL Server", "databases"),
    "mongodb": ("MongoDB", "databases"),
    "mongo": ("MongoDB", "databases"),
    "sqlite": ("SQLite", "databases"),
    "sqlite3": ("SQLite", "databases"),
    "redis": ("Redis", "databases"),
    "mariadb": ("MariaDB", "databases"),
    "cassandra": ("Cassandra", "databases"),
    "dynamodb": ("DynamoDB", "databases"),
    "firebase firestore": ("Firebase Firestore", "databases"),
    "firestore": ("Firebase Firestore", "databases"),
    "firebase": ("Firebase", "databases"),
    "neo4j": ("Neo4j", "databases"),
    "couchdb": ("CouchDB", "databases"),
    "elasticsearch": ("Elasticsearch", "databases"),
    "snowflake": ("Snowflake", "databases"),
    "bigquery": ("BigQuery", "databases"),
    "redshift": ("Amazon Redshift", "databases"),
    "amazon redshift": ("Amazon Redshift", "databases"),
    "supabase": ("Supabase", "databases"),
    "dbms": ("DBMS", "databases"),
    "rdbms": ("RDBMS", "databases"),

    # ==================== FRAMEWORKS ====================
    "react": ("React", "frameworks"),
    "react.js": ("React", "frameworks"),
    "reactjs": ("React", "frameworks"),
    "angular": ("Angular", "frameworks"),
    "angularjs": ("AngularJS", "frameworks"),
    "vue": ("Vue.js", "frameworks"),
    "vue.js": ("Vue.js", "frameworks"),
    "vuejs": ("Vue.js", "frameworks"),
    "next.js": ("Next.js", "frameworks"),
    "nextjs": ("Next.js", "frameworks"),
    "nuxt.js": ("Nuxt.js", "frameworks"),
    "nuxtjs": ("Nuxt.js", "frameworks"),
    "svelte": ("Svelte", "frameworks"),
    "django": ("Django", "frameworks"),
    "flask": ("Flask", "frameworks"),
    "fastapi": ("FastAPI", "frameworks"),
    "spring": ("Spring", "frameworks"),
    "spring boot": ("Spring Boot", "frameworks"),
    "springboot": ("Spring Boot", "frameworks"),
    "express": ("Express.js", "frameworks"),
    "express.js": ("Express.js", "frameworks"),
    "expressjs": ("Express.js", "frameworks"),
    "nest.js": ("NestJS", "frameworks"),
    "nestjs": ("NestJS", "frameworks"),
    ".net": (".NET", "frameworks"),
    "dotnet": (".NET", "frameworks"),
    ".net core": (".NET Core", "frameworks"),
    "asp.net": ("ASP.NET", "frameworks"),
    "laravel": ("Laravel", "frameworks"),
    "symfony": ("Symfony", "frameworks"),
    "codeigniter": ("CodeIgniter", "frameworks"),
    "ruby on rails": ("Ruby on Rails", "frameworks"),
    "rails": ("Ruby on Rails", "frameworks"),
    "flutter": ("Flutter", "frameworks"),
    "react native": ("React Native", "frameworks"),
    "tailwind": ("Tailwind CSS", "frameworks"),
    "tailwindcss": ("Tailwind CSS", "frameworks"),
    "tailwind css": ("Tailwind CSS", "frameworks"),
    "bootstrap": ("Bootstrap", "frameworks"),
    "django rest framework": ("Django REST Framework (DRF)", "frameworks"),
    "drf": ("Django REST Framework (DRF)", "frameworks"),

    # ==================== LIBRARIES ====================
    "numpy": ("NumPy", "libraries"),
    "pandas": ("Pandas", "libraries"),
    "matplotlib": ("Matplotlib", "libraries"),
    "seaborn": ("Seaborn", "libraries"),
    "plotly": ("Plotly", "libraries"),
    "scikit-learn": ("Scikit-learn", "libraries"),
    "sklearn": ("Scikit-learn", "libraries"),
    "tensorflow": ("TensorFlow", "libraries"),
    "pytorch": ("PyTorch", "libraries"),
    "keras": ("Keras", "libraries"),
    "opencv": ("OpenCV", "libraries"),
    "cv2": ("OpenCV", "libraries"),
    "jquery": ("jQuery", "libraries"),
    "requests": ("Requests", "libraries"),
    "scipy": ("SciPy", "libraries"),
    "hugging face": ("Hugging Face", "libraries"),
    "transformers": ("Transformers", "libraries"),
    "spacy": ("spaCy", "libraries"),
    "nltk": ("NLTK", "libraries"),
    "gensim": ("Gensim", "libraries"),
    "redux": ("Redux", "libraries"),
    "rxjs": ("RxJS", "libraries"),
    "beautifulsoup": ("BeautifulSoup", "libraries"),
    "bs4": ("BeautifulSoup", "libraries"),
    "scrapy": ("Scrapy", "libraries"),
    "selenium": ("Selenium", "libraries"),
    "playwright": ("Playwright", "libraries"),
    "langchain": ("LangChain", "libraries"),
    "llama-index": ("LlamaIndex", "libraries"),
    "llamaindex": ("LlamaIndex", "libraries"),
    "three.js": ("Three.js", "libraries"),
    "threejs": ("Three.js", "libraries"),
    "react three fiber": ("React Three Fiber", "libraries"),
    "framer motion": ("Framer Motion", "libraries"),
    "prisma": ("Prisma ORM", "libraries"),
    "sqlalchemy": ("SQLAlchemy", "libraries"),

    # ==================== UI / UX DESIGN TOOLS ====================
    "figma": ("Figma", "ui_ux_tools"),
    "adobe xd": ("Adobe XD", "ui_ux_tools"),
    "xd": ("Adobe XD", "ui_ux_tools"),
    "sketch": ("Sketch", "ui_ux_tools"),
    "adobe photoshop": ("Adobe Photoshop", "ui_ux_tools"),
    "photoshop": ("Adobe Photoshop", "ui_ux_tools"),
    "adobe illustrator": ("Adobe Illustrator", "ui_ux_tools"),
    "illustrator": ("Adobe Illustrator", "ui_ux_tools"),
    "canva": ("Canva", "ui_ux_tools"),
    "framer": ("Framer", "ui_ux_tools"),
    "invision": ("InVision", "ui_ux_tools"),
    "balsamiq": ("Balsamiq", "ui_ux_tools"),
    "axure": ("Axure", "ui_ux_tools"),
    "coreldraw": ("CorelDRAW", "ui_ux_tools"),

    # ==================== OFFICE PRODUCTIVITY ====================
    "microsoft excel": ("Microsoft Excel", "office_productivity"),
    "ms excel": ("Microsoft Excel", "office_productivity"),
    "excel": ("Microsoft Excel", "office_productivity"),
    "microsoft word": ("Microsoft Word", "office_productivity"),
    "ms word": ("Microsoft Word", "office_productivity"),
    "word": ("Microsoft Word", "office_productivity"),
    "microsoft powerpoint": ("Microsoft PowerPoint", "office_productivity"),
    "microsoft power point": ("Microsoft PowerPoint", "office_productivity"),
    "ms powerpoint": ("Microsoft PowerPoint", "office_productivity"),
    "ms power point": ("Microsoft PowerPoint", "office_productivity"),
    "powerpoint": ("Microsoft PowerPoint", "office_productivity"),
    "power point": ("Microsoft PowerPoint", "office_productivity"),
    "microsoft office": ("Microsoft Office", "office_productivity"),
    "ms office": ("Microsoft Office", "office_productivity"),
    "google docs": ("Google Docs", "office_productivity"),
    "google sheets": ("Google Sheets", "office_productivity"),
    "google slides": ("Google Slides", "office_productivity"),
    "microsoft outlook": ("Microsoft Outlook", "office_productivity"),
    "outlook": ("Microsoft Outlook", "office_productivity"),

    # ==================== TOOLS & PLATFORMS ====================
    "git": ("Git", "tools"),
    "github": ("GitHub", "tools"),
    "git & github": ("Git & GitHub", "tools"),
    "git and github": ("Git & GitHub", "tools"),
    "gitlab": ("GitLab", "tools"),
    "bitbucket": ("Bitbucket", "tools"),
    "docker": ("Docker", "tools"),
    "kubernetes": ("Kubernetes", "tools"),
    "k8s": ("Kubernetes", "tools"),
    "jenkins": ("Jenkins", "tools"),
    "terraform": ("Terraform", "tools"),
    "ansible": ("Ansible", "tools"),
    "jira": ("Jira", "tools"),
    "confluence": ("Confluence", "tools"),
    "postman": ("Postman", "tools"),
    "swagger": ("Swagger / OpenAPI", "tools"),
    "visual studio code": ("VS Code", "tools"),
    "vs code": ("VS Code", "tools"),
    "vscode": ("VS Code", "tools"),
    "intellij": ("IntelliJ IDEA", "tools"),
    "intellij idea": ("IntelliJ IDEA", "tools"),
    "eclipse": ("Eclipse", "tools"),
    "android studio": ("Android Studio", "tools"),
    "webpack": ("Webpack", "tools"),
    "vite": ("Vite", "tools"),
    "kafka": ("Apache Kafka", "tools"),
    "rabbitmq": ("RabbitMQ", "tools"),
    "celery": ("Celery", "tools"),
    "airflow": ("Apache Airflow", "tools"),
    "spark": ("Apache Spark", "tools"),
    "hadoop": ("Hadoop", "tools"),
    "ci/cd": ("CI/CD", "tools"),
    "github actions": ("GitHub Actions", "tools"),
    "circleci": ("CircleCI", "tools"),
    "grafana": ("Grafana", "tools"),
    "prometheus": ("Prometheus", "tools"),
    "splunk": ("Splunk", "tools"),
    "datadog": ("DataDog", "tools"),
    "nginx": ("Nginx", "tools"),
    "apache": ("Apache HTTP Server", "tools"),
    "arduino": ("Arduino", "tools"),
    "arduino uno": ("Arduino UNO", "tools"),
    "raspberry pi": ("Raspberry Pi", "tools"),
    "power bi": ("Power BI", "tools"),
    "powerbi": ("Power BI", "tools"),
    "tableau": ("Tableau", "tools"),
    "basic computer knowledge": ("Basic Computer Knowledge", "tools"),
    "basic computer skills": ("Basic Computer Knowledge", "tools"),
    "computer knowledge": ("Basic Computer Knowledge", "tools"),
    "tally": ("Tally", "tools"),
    "tally erp": ("Tally", "tools"),
    "tally prime": ("Tally", "tools"),
    "spss": ("SPSS", "tools"),
    "spss(statistical package for the social sciences)": ("SPSS", "tools"),
    "statistical package for the social sciences": ("SPSS", "tools"),
    "jwt": ("JWT Authentication", "tools"),

    # ==================== CLOUD TECHNOLOGIES ====================
    "aws": ("AWS", "cloud"),
    "amazon web services": ("AWS", "cloud"),
    "ec2": ("AWS EC2", "cloud"),
    "s3": ("AWS S3", "cloud"),
    "lambda": ("AWS Lambda", "cloud"),
    "azure": ("Microsoft Azure", "cloud"),
    "microsoft azure": ("Microsoft Azure", "cloud"),
    "gcp": ("Google Cloud", "cloud"),
    "google cloud": ("Google Cloud", "cloud"),
    "google cloud platform": ("Google Cloud", "cloud"),
    "oracle cloud": ("Oracle Cloud", "cloud"),
    "ibm cloud": ("IBM Cloud", "cloud"),
    "digitalocean": ("DigitalOcean", "cloud"),
    "heroku": ("Heroku", "cloud"),
    "cloudflare": ("Cloudflare", "cloud"),
    "openstack": ("OpenStack", "cloud"),
    "vercel": ("Vercel", "cloud"),
    "netlify": ("Netlify", "cloud"),
    "serverless": ("Serverless Architecture", "cloud"),
    "render": ("Render", "cloud"),

    # ==================== PLATFORMS ====================
    "android": ("Android", "platforms"),
    "ios": ("iOS", "platforms"),
    "windows": ("Windows", "platforms"),
    "linux": ("Linux", "platforms"),
    "unix": ("Unix", "platforms"),
    "macos": ("macOS", "platforms"),
    "salesforce": ("Salesforce", "platforms"),
    "wordpress": ("WordPress", "platforms"),
    "shopify": ("Shopify", "platforms"),

    # ==================== WEB TECHNOLOGIES ====================
    "html": ("HTML", "web_technologies"),
    "html5": ("HTML5", "web_technologies"),
    "css": ("CSS", "web_technologies"),
    "css3": ("CSS3", "web_technologies"),
    "sass": ("SASS", "web_technologies"),
    "scss": ("SCSS", "web_technologies"),
    "rest api": ("RESTful APIs", "web_technologies"),
    "restful api": ("RESTful APIs", "web_technologies"),
    "rest apis": ("RESTful APIs", "web_technologies"),
    "restapi": ("RESTful APIs", "web_technologies"),
    "restapis": ("RESTful APIs", "web_technologies"),
    "restapi's": ("RESTful APIs", "web_technologies"),
    "rest api's": ("RESTful APIs", "web_technologies"),
    "rest-api": ("RESTful APIs", "web_technologies"),
    "rest-apis": ("RESTful APIs", "web_technologies"),
    "rest": ("REST APIs", "web_technologies"),
    "graphql": ("GraphQL", "web_technologies"),
    "websocket": ("WebSockets", "web_technologies"),
    "websockets": ("WebSockets", "web_technologies"),
    "json": ("JSON", "web_technologies"),
    "xml": ("XML", "web_technologies"),
    "responsive design": ("Responsive Web Design", "web_technologies"),
    "responsive web design": ("Responsive Web Design", "web_technologies"),

    # ==================== TECHNICAL DISCIPLINES ====================
    "machine learning": ("Machine Learning", "technical_disciplines"),
    "deep learning": ("Deep Learning", "technical_disciplines"),
    "data science": ("Data Science", "technical_disciplines"),
    "nlp": ("Natural Language Processing (NLP)", "technical_disciplines"),
    "natural language processing": ("Natural Language Processing (NLP)", "technical_disciplines"),
    "computer vision": ("Computer Vision", "technical_disciplines"),
    "data analysis": ("Data Analysis", "technical_disciplines"),
    "data visualization": ("Data Visualization", "technical_disciplines"),
    "data engineering": ("Data Engineering", "technical_disciplines"),
    "business analysis": ("Business Analysis", "technical_disciplines"),
    "marketing analytics": ("Marketing Analytics", "technical_disciplines"),
    "competitor analysis": ("Competitor Analysis", "technical_disciplines"),
    "competitive analysis": ("Competitive Analysis", "technical_disciplines"),
    "business process improvement": ("Business Process Improvement", "technical_disciplines"),
    "microservices": ("Microservices", "technical_disciplines"),
    "distributed systems": ("Distributed Systems", "technical_disciplines"),
    "agile": ("Agile Methodology", "technical_disciplines"),
    "scrum": ("Scrum", "technical_disciplines"),
    "devops": ("DevOps", "technical_disciplines"),
    "object oriented programming": ("Object-Oriented Programming (OOP)", "technical_disciplines"),
    "oop": ("Object-Oriented Programming (OOP)", "technical_disciplines"),
    "oops": ("Object-Oriented Programming (OOP)", "technical_disciplines"),
    "data structures": ("Data Structures & Algorithms", "technical_disciplines"),
    "data structures and algorithms": ("Data Structures & Algorithms", "technical_disciplines"),
    "algorithms": ("Data Structures & Algorithms", "technical_disciplines"),
    "dsa": ("Data Structures & Algorithms", "technical_disciplines"),
    "system design": ("System Design", "technical_disciplines"),
    "cybersecurity": ("Cybersecurity", "technical_disciplines"),
    "blockchain": ("Blockchain", "technical_disciplines"),
    "test driven development": ("Test Driven Development (TDD)", "technical_disciplines"),
    "tdd": ("Test Driven Development (TDD)", "technical_disciplines"),
    "full stack development": ("Full Stack Development", "technical_disciplines"),
    "software development": ("Software Development", "technical_disciplines"),
    "web development": ("Web Development", "technical_disciplines"),
    "backend development": ("Backend Development", "technical_disciplines"),
    "frontend development": ("Frontend Development", "technical_disciplines"),
    "game development": ("Game Development", "technical_disciplines"),
    "accounting": ("Accounting", "technical_disciplines"),
    "finance": ("Finance", "technical_disciplines"),
    "business management": ("Business Management", "technical_disciplines"),
    "financial management": ("Financial Management", "technical_disciplines"),

    # ==================== SOFT SKILLS ====================
    "communication": ("Communication", "soft_skills"),
    "communication skills": ("Communication", "soft_skills"),
    "leadership": ("Leadership", "soft_skills"),
    "problem solving": ("Problem Solving", "soft_skills"),
    "team collaboration": ("Team Collaboration", "soft_skills"),
    "teamwork": ("Teamwork", "soft_skills"),
    "time management": ("Time Management", "soft_skills"),
    "critical thinking": ("Critical Thinking", "soft_skills"),
    "adaptability": ("Adaptability", "soft_skills"),
    "quick learner": ("Quick Learner", "soft_skills"),
    "fast learner": ("Quick Learner", "soft_skills"),
    "mentoring": ("Mentoring", "soft_skills"),
    "negotiation": ("Negotiation", "soft_skills"),
    "conflict resolution": ("Conflict Resolution", "soft_skills"),
    "creativity": ("Creativity", "soft_skills"),
    "analytical thinking": ("Analytical Thinking", "soft_skills"),
    "project management": ("Project Management", "soft_skills"),
}

# Regex patterns identifying career aspirations, target goals, or future desires
ASPIRATION_PATTERNS = [
    re.compile(r"\b(?:want|aspire|wish|hope|aim|plan|seeking|looking|interested|eager|intent|strive)\s+(?:to\s+become|to\s+learn|to\s+work|for\s+opportunities|to\s+gain|for\s+a\s+role|for\s+a\s+position|to\s+pursue)\b", re.IGNORECASE),
    re.compile(r"\b(?:looking\s+for|seeking)\s+(?:a|an|the|entry\s+level|junior|intern|developer|engineer|opportunities\s+in|role\s+in|position\s+in)\b", re.IGNORECASE),
    re.compile(r"\b(?:career\s+goal|career\s+objective|objective|goal\s+is\s+to|aspiring|future|target\s+role|desired\s+role|desired\s+position)\b", re.IGNORECASE),
    re.compile(r"\b(?:looking\s+forward\s+to\s+learning|want\s+to\s+learn|currently\s+planning\s+to\s+learn|interested\s+in\s+learning)\b", re.IGNORECASE),
]

# Regex patterns identifying explicit negative/non-usage mentions
NEGATED_PATTERNS = [
    re.compile(r"\b(?:did\s+not\s+work\s+with|never\s+used|not\s+worked\s+on|no\s+experience\s+with|without\s+using|migrated\s+away\s+from|instead\s+of|neither|not\s+proficient\s+in)\b", re.IGNORECASE),
    re.compile(r"\b(?:do\s+not\s+know|have\s+not\s+used|haven't\s+used|didn't\s+use)\b", re.IGNORECASE),
]

# Regex patterns identifying in-progress learning (should not be marked confirmed professional proficiency)
LEARNING_PATTERNS = [
    re.compile(r"\b(?:currently\s+learning|in\s+the\s+process\s+of\s+learning|learning\s+basics\s+of|beginner\s+in|studying)\b", re.IGNORECASE),
]

# High-confidence explicit skill section names
HIGH_CONFIDENCE_SKILL_SECTIONS = {
    "skills", "technical skills", "technical expertise", "core skills", "key skills",
    "programming skills", "software skills", "it skills", "tools & technologies",
    "tools and technologies", "technologies", "programming languages", "databases",
    "frameworks", "libraries", "tools", "ui/ux", "office productivity", "developer skills",
    "strengths", "technical competencies",
}


def normalize_skill_name(raw_name: str) -> str:
    """Normalize a raw skill string to its canonical taxonomy name if matched."""
    if not raw_name:
        return ""
    clean = re.sub(r"\s+", " ", raw_name).strip()
    clean_lower = clean.lower()
    
    if clean_lower in SKILLS_TAXONOMY:
        return SKILLS_TAXONOMY[clean_lower][0]
    
    # Strip trailing punctuation or annotations like "(Basic)"
    base = re.sub(r"\s*\([^)]*\)", "", clean).strip()
    if base.lower() in SKILLS_TAXONOMY:
        return SKILLS_TAXONOMY[base.lower()][0]
        
    return clean


def get_canonical_category(skill_name: str) -> Optional[str]:
    """Retrieve canonical category from taxonomy for a given skill name."""
    if not skill_name:
        return None
    clean_lower = skill_name.strip().lower()
    if clean_lower in SKILLS_TAXONOMY:
        return SKILLS_TAXONOMY[clean_lower][1]
    
    base = re.sub(r"\s*\([^)]*\)", "", skill_name).strip().lower()
    if base in SKILLS_TAXONOMY:
        return SKILLS_TAXONOMY[base][1]
    return None


def is_aspiration_sentence(sentence: str) -> bool:
    """Determine if a sentence describes career goals / aspirations rather than current capability."""
    if not sentence:
        return False
    return any(p.search(sentence) for p in ASPIRATION_PATTERNS)


def is_negated_sentence(sentence: str, tech_name: Optional[str] = None) -> bool:
    """Determine if a sentence explicitly negates experience with a technology."""
    if not sentence:
        return False
    if any(p.search(sentence) for p in NEGATED_PATTERNS):
        if tech_name:
            escaped = re.escape(tech_name)
            pattern = rf"(?<![a-zA-Z0-9_]){escaped}(?![a-zA-Z0-9_])"
            return bool(re.search(pattern, sentence, re.IGNORECASE))
        return True
    return False


def is_learning_sentence(sentence: str, tech_name: Optional[str] = None) -> bool:
    """Determine if a sentence indicates in-progress learning."""
    if not sentence:
        return False
    if any(p.search(sentence) for p in LEARNING_PATTERNS):
        if tech_name:
            escaped = re.escape(tech_name)
            pattern = rf"(?<![a-zA-Z0-9_]){escaped}(?![a-zA-Z0-9_])"
            return bool(re.search(pattern, sentence, re.IGNORECASE))
        return True
    return False


def classify_skill_evidence(
    skill_name: str,
    context_sentence: str,
    section_name: Optional[str] = None,
) -> Tuple[str, bool]:
    """
    Evaluate candidate skill evidence.
    
    Returns:
        (evidence_type, is_confirmed)
        evidence_type in [
            'EXPLICIT_SKILL', 'EXPERIENCE_USAGE', 'PROJECT_USAGE',
            'CERTIFICATION_USAGE', 'EDUCATION_USAGE', 'ASPIRATION',
            'NEGATED_MENTION', 'LEARNING', 'CONTEXTUAL_MENTION', 'UNKNOWN'
        ]
    """
    sec_lower = (section_name or "").strip().lower()
    ctx_clean = (context_sentence or "").strip()
    
    # 1. Check for explicit negative context
    if is_negated_sentence(ctx_clean, skill_name):
        return ("NEGATED_MENTION", False)
        
    # 2. Check for career aspiration context
    if is_aspiration_sentence(ctx_clean):
        # Even if mentioned in a career objective, if it's only an aspiration, it's not confirmed
        return ("ASPIRATION", False)

    # 3. Check for learning context
    if is_learning_sentence(ctx_clean, skill_name):
        return ("LEARNING", False)
        
    # 4. Check high-confidence skills section
    if sec_lower in HIGH_CONFIDENCE_SKILL_SECTIONS or "skill" in sec_lower:
        return ("EXPLICIT_SKILL", True)
        
    # 5. Check Experience section
    if "experience" in sec_lower or "internship" in sec_lower or "work" in sec_lower or "employment" in sec_lower:
        # Check active usage verbs
        if re.search(r"\b(?:using|used|developed|built|created|implemented|worked\s+with|programmed\s+in|configured|designed|leveraged|utilized)\b", ctx_clean, re.IGNORECASE):
            return ("EXPERIENCE_USAGE", True)
        return ("EXPERIENCE_USAGE", True)
        
    # 6. Check Project section
    if "project" in sec_lower:
        return ("PROJECT_USAGE", True)
        
    # 7. Check Certification section
    if "certif" in sec_lower or "course" in sec_lower or "license" in sec_lower:
        return ("CERTIFICATION_USAGE", True)
        
    # 8. Check Education / Coursework section
    if "education" in sec_lower or "academic" in sec_lower or "coursework" in sec_lower:
        return ("EDUCATION_USAGE", True)
        
    # Default fallback: if context proves usage
    if re.search(r"\b(?:developed|built|created|implemented|worked\s+with|proficient\s+in|experience\s+with|knowledge\s+of|skills?\s*:)\b", ctx_clean, re.IGNORECASE):
        return ("EXPERIENCE_USAGE", True)
        
    if len(ctx_clean) < 80 and not is_aspiration_sentence(ctx_clean):
        # Short bullet or list item
        return ("EXPLICIT_SKILL", True)
        
    return ("CONTEXTUAL_MENTION", False)


def get_all_skills() -> Dict[str, Tuple[str, str]]:
    """Return the entire skills dictionary."""
    return SKILLS_TAXONOMY


def get_skills_by_category() -> Dict[str, Set[str]]:
    """Return set of canonical skills grouped by category."""
    categories: Dict[str, Set[str]] = {
        "programming_languages": set(),
        "databases": set(),
        "frameworks": set(),
        "libraries": set(),
        "ui_ux_tools": set(),
        "office_productivity": set(),
        "tools": set(),
        "cloud": set(),
        "platforms": set(),
        "web_technologies": set(),
        "technical_disciplines": set(),
        "soft_skills": set(),
        "technical": set(),
        "other": set(),
    }
    for _, (canonical, cat) in SKILLS_TAXONOMY.items():
        if cat in categories:
            categories[cat].add(canonical)
    return categories
