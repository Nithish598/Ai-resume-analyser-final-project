"""Enterprise Skill Normalization, Disambiguation, and Exact Matching Engine."""
import re
from typing import List, Dict, Set, Tuple, Optional, Any


# Canonical Aliases Dictionary
CANONICAL_SKILL_ALIASES: Dict[str, str] = {
    # Python & Frameworks
    "python": "Python",
    "python 3": "Python",
    "python3": "Python",
    "python programming": "Python",
    "py": "Python",
    "django": "Django",
    "flask": "Flask",
    "fastapi": "FastAPI",
    "fast api": "FastAPI",
    "django rest framework": "Django REST Framework",
    "drf": "Django REST Framework",
    
    # APIs & Web Services
    "rest api": "REST APIs",
    "rest apis": "REST APIs",
    "rest ap is": "REST APIs",
    "restful api": "REST APIs",
    "restful apis": "REST APIs",
    "restapi": "REST APIs",
    "restapis": "REST APIs",
    "restapi's": "REST APIs",
    "rest api's": "REST APIs",
    "rest-api": "REST APIs",
    "rest-apis": "REST APIs",
    "rest_api": "REST APIs",
    "rest_apis": "REST APIs",
    "web api": "REST APIs",
    "web apis": "REST APIs",
    "web api's": "REST APIs",
    "rest": "REST APIs",
    "api": "REST APIs",
    "apis": "REST APIs",
    "api's": "REST APIs",
    "api development": "REST APIs",
    "api integration": "REST APIs",
    "graphql": "GraphQL",
    "soap": "SOAP",
    
    # JavaScript / TypeScript / Web
    "javascript": "JavaScript",
    "js": "JavaScript",
    "typescript": "TypeScript",
    "ts": "TypeScript",
    "html": "HTML5",
    "html5": "HTML5",
    "css": "CSS3",
    "css3": "CSS3",
    "react": "React",
    "react.js": "React",
    "reactjs": "React",
    "react js": "React",
    "redux": "Redux",
    "node": "Node.js",
    "nodejs": "Node.js",
    "node.js": "Node.js",
    "express": "Express.js",
    "express.js": "Express.js",
    "vue": "Vue.js",
    "vue.js": "Vue.js",
    "vuejs": "Vue.js",
    "angular": "Angular",
    "tailwind": "Tailwind CSS",
    "tailwind css": "Tailwind CSS",
    "bootstrap": "Bootstrap",
    "responsive design": "Responsive Design",
    "responsive web design": "Responsive Design",
    "dom": "DOM Concepts",
    "dom manipulation": "DOM Concepts",
    "browser/dom concepts": "DOM Concepts",
    "accessibility": "Accessibility",

    # Java & C-Family (Strict Disambiguation)
    "java": "Java",
    "core java": "Java",
    "advanced java": "Java",
    "spring": "Spring Boot",
    "spring boot": "Spring Boot",
    "springboot": "Spring Boot",
    "jdbc": "JDBC",
    "hibernate": "Hibernate",
    "c": "C",
    "c programming": "C",
    "c++": "C++",
    "cpp": "C++",
    "c plus plus": "C++",
    "c#": "C#",
    "c sharp": "C#",
    "csharp": "C#",
    "dotnet": ".NET",
    ".net": ".NET",

    # Databases
    "sql": "SQL",
    "mysql": "MySQL",
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "psql": "PostgreSQL",
    "sqlite": "SQLite",
    "sqlite3": "SQLite",
    "mongodb": "MongoDB",
    "mongo": "MongoDB",
    "redis": "Redis",
    "oracle": "Oracle DB",
    "oracle db": "Oracle DB",
    "database management": "Database Management",
    "dbms": "Database Management",
    "rdbms": "Database Management",
    "database fundamentals": "Database Management",

    # Data Science & Machine Learning
    "pandas": "Pandas",
    "numpy": "NumPy",
    "scikit-learn": "Scikit-Learn",
    "scikit learn": "Scikit-Learn",
    "sklearn": "Scikit-Learn",
    "machine learning": "Machine Learning",
    "ml": "Machine Learning",
    "deep learning": "Deep Learning",
    "dl": "Deep Learning",
    "tensorflow": "TensorFlow",
    "tf": "TensorFlow",
    "pytorch": "PyTorch",
    "torch": "PyTorch",
    "nlp": "Natural Language Processing",
    "natural language processing": "Natural Language Processing",
    "computer vision": "Computer Vision",
    "cv": "Computer Vision",
    "data visualization": "Data Visualization",
    "matplotlib": "Data Visualization",
    "seaborn": "Data Visualization",
    "statistics": "Statistics",
    "statistical analysis": "Statistics",
    "data analysis": "Data Analysis",
    "data preprocessing": "Data Preprocessing",
    "model evaluation": "Model Evaluation",
    "mlops": "MLOps",

    # Business Intelligence & Office
    "microsoft excel": "Microsoft Excel",
    "ms excel": "Microsoft Excel",
    "excel": "Microsoft Excel",
    "microsoft word": "Microsoft Word",
    "ms word": "Microsoft Word",
    "word": "Microsoft Word",
    "microsoft office": "Microsoft Office",
    "ms office": "Microsoft Office",
    "power bi": "Power BI",
    "powerbi": "Power BI",
    "tableau": "Tableau",

    # DevOps, Cloud & Version Control (Git != GitHub)
    "git": "Git",
    "github": "GitHub",
    "gitlab": "GitLab",
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "k8s": "Kubernetes",
    "aws": "AWS",
    "amazon web services": "AWS",
    "gcp": "GCP",
    "google cloud": "GCP",
    "azure": "Azure",
    "microsoft azure": "Azure",
    "cloud": "Cloud",
    "linux": "Linux",
    "unix": "Linux",
    "ci/cd": "CI/CD",
    "cicd": "CI/CD",
    "authentication": "Authentication",

    # Web & 3D Interactive UI
    "react three fiber": "React Three Fiber",
    "three.js": "Three.js",
    "threejs": "Three.js",
    "framer motion": "Framer Motion",
    "vite": "Vite",
    "ui animation": "UI Animation",
    "3d web development": "3D Web Development",
    "interactive ui": "Interactive UI",
    "visual effects": "Visual Effects",
    "full stack development": "Full Stack Development",
    "frontend development": "Frontend Development",
    "backend development": "Backend Development",
    "my sql": "MySQL",
    "rest ap is": "REST APIs",
    "simple jwt": "JWT Authentication",
    "jwt authentication (simple jwt)": "JWT Authentication",
    "jwt": "JWT Authentication",
    "jwt authentication": "JWT Authentication",
    "next.js": "Next.js",
    "nextjs": "Next.js",
    "next js": "Next.js",
    "vercel": "Vercel",
    "render": "Render",
    "netlify": "Netlify",
    "github pages": "GitHub Pages",
    "heroku": "Heroku",
    "digitalocean": "DigitalOcean",
    "sass": "Sass / SCSS",
    "scss": "Sass / SCSS",
    "storybook": "Storybook",
    "figma": "Figma",
    "adobe xd": "Adobe XD",
    "canva": "Canva",
    "jest": "Jest",
    "playwright": "Playwright",
    "cypress": "Cypress",
    "selenium": "Selenium",
    "pytest": "PyTest",
    "postman": "Postman",
    "swagger": "Swagger",
    "npm": "npm",
    "yarn": "Yarn",
    "webpack": "Webpack",
    "vscode": "VS Code",
    "vs code": "VS Code",
    "intellij": "IntelliJ IDEA",
    "intellij idea": "IntelliJ IDEA",
    "visual studio": "Visual Studio",
    "chrome devtools": "Chrome DevTools",
    "browser devtools": "Browser DevTools",
    "browser apis": "Browser APIs",
    "figjam": "FigJam",
    "design systems": "Design Systems",
    "wireframing": "Wireframing",
    "prototyping": "Prototyping",
    "user research": "User Research",
    "ux research": "User Research",
    "user flows": "User Flows",
    "interaction design": "Interaction Design",
    "user-centered design": "User-Centered Design",
    "usability testing": "Usability Testing",
    "information architecture": "Information Architecture",
    "visual design": "Visual Design",
    "component design": "Component Design",
    "typography": "Typography",
    "color systems": "Color Systems",
    "wcag": "WCAG",
    "keyboard accessibility": "Keyboard Accessibility",
    "screen reader compatibility": "Screen Reader Compatibility",
    "semantic html": "Semantic HTML",
    "css modules": "CSS Modules",
    "react router": "React Router",
    "zustand": "Zustand",
    "react testing library": "React Testing Library",
    "rtl": "React Testing Library",
    "web performance": "Web Performance",
    "performance optimization": "Performance Optimization",
    "component architecture": "Component Architecture",
    "swiftui": "SwiftUI",
    "android sdk": "Android SDK",
    "android studio": "Android Studio",
    "xcode": "Xcode",
    "flutter": "Flutter",
    "react native": "React Native",
    "mobile ui": "Mobile UI",
    "state management": "State Management",
    "navigation": "Navigation",
    "push notifications": "Push Notifications",
    "local storage": "Local Storage",
    "mobile testing": "Mobile Testing",
    "app deployment": "App Deployment",
    "authorization": "Authorization",
    "oauth": "OAuth",
    "oauth2": "OAuth",
    "api design": "API Design",
    "microservices": "Microservices",
    "junit": "JUnit",
    "cloud deployment": "Cloud Deployment",
    "frontend architecture": "Frontend Architecture",
    "backend architecture": "Backend Architecture",
    "api integration": "API Integration",
    "database design": "Database Design",
    "design patterns": "Design Patterns",
    "software architecture": "Software Architecture",
    "unit testing": "Unit Testing",
    "integration testing": "Integration Testing",
    "automated testing": "Automated Testing",
    "code review": "Code Review",
    "documentation": "Documentation",
    "version control": "Version Control",
    "cloud platforms": "Cloud Platforms",
    "data cleaning": "Data Cleaning",
    "exploratory data analysis": "Exploratory Data Analysis",
    "eda": "Exploratory Data Analysis",
    "reporting": "Reporting",
    "business intelligence": "Business Intelligence",
    "r": "R",
    "matplotlib": "Matplotlib",
    "seaborn": "Seaborn",
    "pivot tables": "Pivot Tables",
    "vlookup": "VLOOKUP/XLOOKUP",
    "xlookup": "VLOOKUP/XLOOKUP",
    "vlookup/xlookup": "VLOOKUP/XLOOKUP",
    "power query": "Power Query",
    "looker": "Looker",
    "sql server": "SQL Server",
    "jupyter notebook": "Jupyter Notebook",
    "jupyter": "Jupyter Notebook",
    "jupyterlab": "JupyterLab",
    "kpi analysis": "KPI Analysis",
    "dashboard development": "Dashboard Development",
    "business reporting": "Business Reporting",
    "data storytelling": "Data Storytelling",
    "xgboost": "XGBoost",
    "lightgbm": "LightGBM",
    "probability": "Probability",
    "feature engineering": "Feature Engineering",
    "time series": "Time Series",
    "model deployment": "Model Deployment",
    "mlflow": "MLflow",
    "scala": "Scala",
    "apache spark": "Apache Spark",
    "spark": "Apache Spark",
    "pyspark": "PySpark",
    "apache airflow": "Apache Airflow",
    "airflow": "Apache Airflow",
    "kafka": "Kafka",
    "apache kafka": "Kafka",
    "dbt": "dbt",
    "etl": "ETL Pipelines",
    "elt": "ELT Pipelines",
    "etl pipelines": "ETL Pipelines",
    "elt pipelines": "ELT Pipelines",
    "snowflake": "Snowflake",
    "bigquery": "BigQuery",
    "google bigquery": "BigQuery",
    "amazon redshift": "Amazon Redshift",
    "redshift": "Amazon Redshift",
    "hadoop": "Hadoop",
    "s3": "AWS S3",
    "aws s3": "AWS S3",
    "glue": "AWS Glue",
    "aws glue": "AWS Glue",
    "data factory": "Azure Data Factory",
    "azure data factory": "Azure Data Factory",
    "synapse analytics": "Azure Synapse Analytics",
    "azure synapse": "Azure Synapse Analytics",
    "dataflow": "Google Cloud Dataflow",
    "data modeling": "Data Modeling",
    "data warehousing": "Data Warehousing",
    "batch processing": "Batch Processing",
    "stream processing": "Stream Processing",
    "distributed systems": "Distributed Systems",
    "data quality": "Data Quality",
    "data governance": "Data Governance",
    "problem solving": "Problem Solving",
    "team collaboration": "Team Collaboration",
    "agile": "Agile/Scrum",
    "scrum": "Agile/Scrum",
    "agile/scrum": "Agile/Scrum",
    "communication": "Communication",
    "time management": "Time Management",
    "leadership": "Leadership",

    # Core Computer Science & Engineering
    "data structures": "Data Structures",
    "algorithms": "Algorithms",
    "data structures and algorithms": "Data Structures & Algorithms",
    "data structures & algorithms": "Data Structures & Algorithms",
    "dsa": "Data Structures & Algorithms",
    "oop": "Object-Oriented Programming",
    "object oriented programming": "Object-Oriented Programming",
    "object-oriented programming": "Object-Oriented Programming",
    "debugging": "Debugging",
    "software testing": "Software Testing",
    "testing": "Software Testing",
    "system design": "System Design",
}



# Canonical Taxonomy Mapping for Categorized Skills Matrix
SKILL_TAXONOMY_CATEGORIES: Dict[str, str] = {
    # 1. Programming Languages
    "python": "Programming Languages",
    "javascript": "Programming Languages",
    "typescript": "Programming Languages",
    "java": "Programming Languages",
    "c": "Programming Languages",
    "c++": "Programming Languages",
    "c#": "Programming Languages",
    "sql": "Programming Languages",
    "go": "Programming Languages",
    "rust": "Programming Languages",
    "ruby": "Programming Languages",
    "php": "Programming Languages",
    "swift": "Programming Languages",
    "kotlin": "Programming Languages",
    "r": "Programming Languages",
    "scala": "Programming Languages",
    "dart": "Programming Languages",
    "bash": "Programming Languages",
    "shell": "Programming Languages",

    # 2. Frontend Technologies & Frameworks
    "html5": "Frontend Technologies",
    "html": "Frontend Technologies",
    "css3": "Frontend Technologies",
    "css": "Frontend Technologies",
    "react": "Frontend Technologies",
    "next.js": "Frontend Technologies",
    "vue.js": "Frontend Technologies",
    "angular": "Frontend Technologies",
    "svelte": "Frontend Technologies",
    "tailwind css": "Frontend Technologies",
    "bootstrap": "Frontend Technologies",
    "framer motion": "Frontend Technologies",
    "three.js": "Frontend Technologies",
    "react three fiber": "Frontend Technologies",
    "redux": "Frontend Technologies",
    "sass / scss": "Frontend Technologies",
    "dom concepts": "Frontend Technologies",
    "responsive design": "Frontend Technologies",
    "vite": "Frontend Technologies",
    "jquery": "Frontend Technologies",
    "ui animation": "Frontend Technologies",
    "3d web development": "Frontend Technologies",
    "interactive ui": "Frontend Technologies",
    "visual effects": "Frontend Technologies",
    "full stack development": "Frontend Technologies",
    "frontend development": "Frontend Technologies",

    # 3. Backend Technologies & Frameworks
    "node.js": "Backend Technologies",
    "express.js": "Backend Technologies",
    "django": "Backend Technologies",
    "django rest framework": "Backend Technologies",
    "fastapi": "Backend Technologies",
    "flask": "Backend Technologies",
    "spring boot": "Backend Technologies",
    "spring": "Backend Technologies",
    ".net": "Backend Technologies",
    "asp.net": "Backend Technologies",
    "ruby on rails": "Backend Technologies",
    "laravel": "Backend Technologies",
    "nestjs": "Backend Technologies",
    "jdbc": "Backend Technologies",
    "hibernate": "Backend Technologies",
    "backend development": "Backend Technologies",

    # 4. APIs & Web Services
    "rest api": "APIs & Web Services",
    "rest apis": "APIs & Web Services",
    "graphql": "APIs & Web Services",
    "soap": "APIs & Web Services",
    "websockets": "APIs & Web Services",
    "grpc": "APIs & Web Services",
    "api integration": "APIs & Web Services",

    # 5. Authentication & Security
    "jwt authentication": "Authentication & Security",
    "authentication": "Authentication & Security",
    "authorization": "Authentication & Security",
    "oauth": "Authentication & Security",
    "web security": "Authentication & Security",
    "cryptography": "Authentication & Security",

    # 6. Databases & Storage
    "postgresql": "Databases & Storage",
    "mysql": "Databases & Storage",
    "mongodb": "Databases & Storage",
    "redis": "Databases & Storage",
    "sqlite": "Databases & Storage",
    "oracle db": "Databases & Storage",
    "database management": "Databases & Storage",
    "dynamodb": "Databases & Storage",
    "cassandra": "Databases & Storage",
    "sql server": "Databases & Storage",
    "firebase": "Databases & Storage",
    "elasticsearch": "Databases & Storage",

    # 7. Cloud, Hosting & Deployment
    "aws": "Cloud & Hosting",
    "gcp": "Cloud & Hosting",
    "azure": "Cloud & Hosting",
    "vercel": "Cloud & Hosting",
    "render": "Cloud & Hosting",
    "netlify": "Cloud & Hosting",
    "github pages": "Cloud & Hosting",
    "heroku": "Cloud & Hosting",
    "digitalocean": "Cloud & Hosting",
    "cloud": "Cloud & Hosting",

    # 8. DevOps, CI/CD & Infrastructure
    "docker": "DevOps & Infrastructure",
    "kubernetes": "DevOps & Infrastructure",
    "ci/cd": "DevOps & Infrastructure",
    "github actions": "DevOps & Infrastructure",
    "jenkins": "DevOps & Infrastructure",
    "terraform": "DevOps & Infrastructure",
    "ansible": "DevOps & Infrastructure",
    "linux": "DevOps & Infrastructure",
    "nginx": "DevOps & Infrastructure",
    "apache": "DevOps & Infrastructure",

    # 9. Development Tools & Platforms
    "git": "Development Tools",
    "github": "Development Tools",
    "gitlab": "Development Tools",
    "bitbucket": "Development Tools",
    "postman": "Development Tools",
    "swagger": "Development Tools",
    "vscode": "Development Tools",
    "vs code": "Development Tools",
    "jira": "Development Tools",
    "npm": "Development Tools",
    "yarn": "Development Tools",
    "webpack": "Development Tools",

    # 10. UI / UX & Design
    "figma": "UI / UX Design",
    "adobe xd": "UI / UX Design",
    "canva": "UI / UX Design",
    "design systems": "UI / UX Design",
    "accessibility": "UI / UX Design",
    "wireframing": "UI / UX Design",
    "prototyping": "UI / UX Design",
    "user research": "UI / UX Design",

    # 11. Data Science & Machine Learning
    "pandas": "Data Science & AI",
    "numpy": "Data Science & AI",
    "scikit-learn": "Data Science & AI",
    "tensorflow": "Data Science & AI",
    "pytorch": "Data Science & AI",
    "machine learning": "Data Science & AI",
    "deep learning": "Data Science & AI",
    "natural language processing": "Data Science & AI",
    "computer vision": "Data Science & AI",
    "data visualization": "Data Science & AI",
    "matplotlib": "Data Science & AI",
    "seaborn": "Data Science & AI",
    "statistics": "Data Science & AI",
    "data analysis": "Data Science & AI",
    "feature engineering": "Data Science & AI",
    "model evaluation": "Data Science & AI",
    "mlops": "Data Science & AI",

    # 12. Business Intelligence & Analytics
    "power bi": "Business Intelligence",
    "tableau": "Business Intelligence",
    "microsoft excel": "Business Intelligence",
    "excel": "Business Intelligence",
    "looker": "Business Intelligence",
    "etl pipelines": "Business Intelligence",

    # 13. Software Testing & Quality Assurance
    "software testing": "Testing & QA",
    "testing": "Testing & QA",
    "jest": "Testing & QA",
    "playwright": "Testing & QA",
    "cypress": "Testing & QA",
    "selenium": "Testing & QA",
    "pytest": "Testing & QA",
    "unit testing": "Testing & QA",

    # 14. Core Computer Science
    "data structures & algorithms": "Core Computer Science",
    "data structures": "Core Computer Science",
    "algorithms": "Core Computer Science",
    "object-oriented programming": "Core Computer Science",
    "system design": "Core Computer Science",
    "debugging": "Core Computer Science",

    # 15. Office & Productivity
    "microsoft office": "Office Productivity",
    "microsoft word": "Office Productivity",
    "microsoft powerpoint": "Office Productivity",
    "google workspace": "Office Productivity",

    # 16. Soft Skills
    "problem solving": "Soft Skills & Attributes",
    "team collaboration": "Soft Skills & Attributes",
    "communication": "Soft Skills & Attributes",
    "agile/scrum": "Soft Skills & Attributes",
    "leadership": "Soft Skills & Attributes",
    "time management": "Soft Skills & Attributes",
    "adaptability": "Soft Skills & Attributes",
}


# Precise Archetype Mapping for Real-World Industry Categorization
# Archetypes: 'language' | 'tool' | 'framework' | 'library' | 'platform' | 'database' | 'concept'
SKILL_ARCHETYPES: Dict[str, str] = {
    # Languages
    "python": "language",
    "javascript": "language",
    "typescript": "language",
    "java": "language",
    "c": "language",
    "c++": "language",
    "c#": "language",
    "go": "language",
    "rust": "language",
    "ruby": "language",
    "php": "language",
    "swift": "language",
    "kotlin": "language",
    "dart": "language",
    "r": "language",
    "scala": "language",
    "sql": "language",
    "bash": "language",
    "shell": "language",
    "html5": "language",
    "html": "language",
    "css3": "language",
    "css": "language",

    # Tools
    "vscode": "tool",
    "vs code": "tool",
    "visual studio": "tool",
    "intellij": "tool",
    "intellij idea": "tool",
    "chrome devtools": "tool",
    "browser devtools": "tool",
    "postman": "tool",
    "swagger": "tool",
    "npm": "tool",
    "yarn": "tool",
    "webpack": "tool",
    "vite": "tool",
    "git": "tool",
    "github": "tool",
    "gitlab": "tool",
    "bitbucket": "tool",
    "docker": "tool",
    "kubernetes": "tool",
    "jenkins": "tool",
    "terraform": "tool",
    "ansible": "tool",
    "jira": "tool",
    "android studio": "tool",
    "xcode": "tool",
    "figma": "tool",
    "figjam": "tool",
    "adobe xd": "tool",
    "canva": "tool",
    "jupyter notebook": "tool",
    "jupyter": "tool",
    "jupyterlab": "tool",
    "microsoft excel": "tool",
    "excel": "tool",
    "power bi": "tool",
    "tableau": "tool",
    "looker": "tool",
    "mlflow": "tool",
    "apache airflow": "tool",
    "airflow": "tool",
    "dbt": "tool",
    "storybook": "tool",

    # Frameworks
    "react": "framework",
    "next.js": "framework",
    "vue.js": "framework",
    "angular": "framework",
    "svelte": "framework",
    "tailwind css": "framework",
    "bootstrap": "framework",
    "django": "framework",
    "django rest framework": "framework",
    "fastapi": "framework",
    "flask": "framework",
    "node.js": "framework",
    "express.js": "framework",
    "spring boot": "framework",
    ".net": "framework",
    "asp.net": "framework",
    "ruby on rails": "framework",
    "laravel": "framework",
    "nestjs": "framework",
    "android sdk": "framework",
    "flutter": "framework",
    "react native": "framework",
    "swiftui": "framework",
    "uikit": "framework",
    "hadoop": "framework",
    "apache spark": "framework",

    # Libraries
    "redux": "library",
    "zustand": "library",
    "react router": "library",
    "framer motion": "library",
    "three.js": "library",
    "react three fiber": "library",
    "pandas": "library",
    "numpy": "library",
    "matplotlib": "library",
    "seaborn": "library",
    "scikit-learn": "library",
    "xgboost": "library",
    "lightgbm": "library",
    "tensorflow": "library",
    "pytorch": "library",
    "pyspark": "library",
    "jest": "library",
    "playwright": "library",
    "cypress": "library",
    "selenium": "library",
    "pytest": "library",
    "junit": "library",
    "react testing library": "library",
    "sass / scss": "library",
    "css modules": "library",
    "jquery": "library",
    "hibernate": "library",
    "jdbc": "library",

    # Platforms & Cloud
    "aws": "platform",
    "gcp": "platform",
    "azure": "platform",
    "vercel": "platform",
    "netlify": "platform",
    "render": "platform",
    "github pages": "platform",
    "firebase": "platform",
    "linux": "platform",
    "heroku": "platform",
    "digitalocean": "platform",
    "snowflake": "platform",
    "bigquery": "platform",
    "amazon redshift": "platform",
    "aws s3": "platform",
    "aws glue": "platform",
    "azure data factory": "platform",
    "azure synapse analytics": "platform",
    "google cloud dataflow": "platform",
    "cloud platforms": "platform",
    "cloud": "platform",

    # Databases
    "postgresql": "database",
    "mysql": "database",
    "mongodb": "database",
    "redis": "database",
    "sqlite": "database",
    "sql server": "database",
    "oracle db": "database",
    "dynamodb": "database",
    "cassandra": "database",
    "database management": "database",
    "elasticsearch": "database",

    # Concepts, Methodologies & Workflows
    "responsive design": "concept",
    "dom concepts": "concept",
    "browser apis": "concept",
    "rest api": "concept",
    "rest apis": "concept",
    "graphql": "concept",
    "soap": "concept",
    "accessibility": "concept",
    "wcag": "concept",
    "keyboard accessibility": "concept",
    "screen reader compatibility": "concept",
    "semantic html": "concept",
    "web performance": "concept",
    "performance optimization": "concept",
    "component architecture": "concept",
    "mobile ui": "concept",
    "state management": "concept",
    "navigation": "concept",
    "push notifications": "concept",
    "local storage": "concept",
    "mobile testing": "concept",
    "app deployment": "concept",
    "user research": "concept",
    "user flows": "concept",
    "wireframing": "concept",
    "prototyping": "concept",
    "usability testing": "concept",
    "information architecture": "concept",
    "interaction design": "concept",
    "user-centered design": "concept",
    "visual design": "concept",
    "design systems": "concept",
    "component design": "concept",
    "typography": "concept",
    "color systems": "concept",
    "ui animation": "concept",
    "authentication": "concept",
    "authorization": "concept",
    "jwt authentication": "concept",
    "oauth": "concept",
    "api design": "concept",
    "microservices": "concept",
    "ci/cd": "concept",
    "cloud deployment": "concept",
    "frontend architecture": "concept",
    "backend architecture": "concept",
    "api integration": "concept",
    "database design": "concept",
    "data structures": "concept",
    "algorithms": "concept",
    "data structures & algorithms": "concept",
    "object-oriented programming": "concept",
    "design patterns": "concept",
    "software architecture": "concept",
    "debugging": "concept",
    "software testing": "concept",
    "unit testing": "concept",
    "integration testing": "concept",
    "automated testing": "concept",
    "problem solving": "concept",
    "code review": "concept",
    "version control": "concept",
    "documentation": "concept",
    "agile/scrum": "concept",
    "data cleaning": "concept",
    "data analysis": "concept",
    "statistics": "concept",
    "probability": "concept",
    "exploratory data analysis": "concept",
    "data visualization": "concept",
    "reporting": "concept",
    "business intelligence": "concept",
    "kpi analysis": "concept",
    "dashboard development": "concept",
    "business reporting": "concept",
    "data storytelling": "concept",
    "feature engineering": "concept",
    "model evaluation": "concept",
    "natural language processing": "concept",
    "computer vision": "concept",
    "time series": "concept",
    "model deployment": "concept",
    "mlops": "concept",
    "etl pipelines": "concept",
    "elt pipelines": "concept",
    "data modeling": "concept",
    "data warehousing": "concept",
    "batch processing": "concept",
    "stream processing": "concept",
    "distributed systems": "concept",
    "data quality": "concept",
    "data governance": "concept",
}


class SkillNormalizer:
    """Provides canonical resolution and exact set-theoretic matching for skills."""

    @classmethod
    def get_skill_archetype(cls, skill_name: str) -> str:
        """
        Classify any skill into its technical archetype:
        'language' | 'tool' | 'framework' | 'library' | 'platform' | 'database' | 'concept'
        """
        if not skill_name:
            return "concept"
        norm = cls.normalize_skill(skill_name)
        k = norm.lower()
        if k in SKILL_ARCHETYPES:
            return SKILL_ARCHETYPES[k]
        
        # Heuristic archetype rules
        if any(w in k for w in ["database", "sql", "mongo", "postgres", "redis", "storage"]):
            return "database"
        elif any(w in k for w in ["tool", "studio", "git", "postman", "figma", "excel", "jupyter", "airflow", "dbt", "docker", "vscode", "devtool"]):
            return "tool"
        elif any(w in k for w in ["framework", "react", "vue", "angular", "django", "flask", "spring", "express", "flutter", "spark"]):
            return "framework"
        elif any(w in k for w in ["library", "redux", "pandas", "numpy", "torch", "tensor", "scikit", "jest", "cypress", "motion", "router"]):
            return "library"
        elif any(w in k for w in ["cloud", "aws", "azure", "gcp", "vercel", "netlify", "render", "hosting", "platform"]):
            return "platform"
        elif any(w in k for w in ["language", "script", "python", "java", "c++", "c#", "golang", "ruby", "rust", "scala", "kotlin", "swift"]):
            return "language"
        
        return "concept"

    @classmethod
    def normalize_skill(cls, raw_skill: Any) -> str:

        """Normalize a skill string or dictionary to its canonical title."""
        if not raw_skill:
            return ""
        if isinstance(raw_skill, dict):
            raw_skill = raw_skill.get("name") or raw_skill.get("skill") or raw_skill.get("title") or ""
        
        s_str = str(raw_skill).strip()
        if not s_str:
            return ""

        s = s_str.lower()
        s = s.replace("’", "'").replace("‘", "'")
        s = re.sub(r"^[\s*•\-\–\—\+\d\.\)]+", "", s).strip()
        s = re.sub(r"[\(\)\[\]]", "", s)
        s = re.sub(r"\s+", " ", s).strip()
        
        # Exact alias lookup
        if s in CANONICAL_SKILL_ALIASES:
            return CANONICAL_SKILL_ALIASES[s]

        # Strip 's or apostrophes (e.g. "restapi's" -> "restapi", "rest api's" -> "rest api")
        s_no_apos = re.sub(r"['’]s$", "", s).strip()
        if s_no_apos in CANONICAL_SKILL_ALIASES:
            return CANONICAL_SKILL_ALIASES[s_no_apos]

        s_no_quote = s.replace("'", "").strip()
        if s_no_quote in CANONICAL_SKILL_ALIASES:
            return CANONICAL_SKILL_ALIASES[s_no_quote]
            
        # Strip common trailing noise e.g. "python language" -> "python"
        s_clean = re.sub(r"\s+(?:language|programming|framework|basics|fundamentals)$", "", s).strip()
        if s_clean in CANONICAL_SKILL_ALIASES:
            return CANONICAL_SKILL_ALIASES[s_clean]

        return s_str.title()

    normalize_skill_name = normalize_skill

    @classmethod
    def normalize_skills_list(cls, skills: Any) -> List[str]:
        """Normalize a list of skills, returning unique canonical names."""
        if not skills:
            return []
        if isinstance(skills, str):
            skills = [s.strip() for s in skills.split(",") if s.strip()]
        elif isinstance(skills, dict):
            flat = []
            for v in skills.values():
                if isinstance(v, list):
                    flat.extend(v)
                elif isinstance(v, (str, dict)):
                    flat.append(v)
            skills = flat

        seen = set()
        result = []
        for sk in (skills or []):
            norm = cls.normalize_skill(sk)
            if norm and norm.lower() not in seen:
                seen.add(norm.lower())
                result.append(norm)
        return result

    @classmethod
    def match_skills(
        cls,
        candidate_skills: Any,
        target_skills: Any,
    ) -> Tuple[List[str], List[str]]:
        """
        Compare candidate skills against target skills.
        Strictly prevents substring false positives (e.g. Java != JavaScript).
        Returns: (demonstrated_in_resume, not_demonstrated_in_resume)
        """
        cand_list = cls.normalize_skills_list(candidate_skills)
        norm_cand = {s.lower(): s for s in cand_list if s}
        
        # Also support GitHub presence helping satisfy Git if present
        if "github" in norm_cand and "git" not in norm_cand:
            # Note: GitHub is present, but Git itself is not explicitly listed
            pass

        matched = []
        missing = []

        target_list = cls.normalize_skills_list(target_skills)
        for target_norm in target_list:
            target_key = target_norm.lower()
            
            # Direct match
            if target_key in norm_cand:
                matched.append(target_norm)
            elif target_key in ["rest api", "rest apis", "restapis", "restapi", "restapi's", "rest api's"] and any(
                k in norm_cand for k in ["rest apis", "rest api", "restapis", "restapi", "restapi's", "rest api's"]
            ):
                matched.append(target_norm)
            elif target_key in ["jwt", "jwt authentication", "simple jwt"] and ("jwt authentication" in norm_cand or "jwt" in norm_cand):
                matched.append(target_norm)
            elif target_key == "data structures & algorithms" and ("data structures" in norm_cand or "algorithms" in norm_cand):
                matched.append(target_norm)
            elif target_key in ["html", "html5"] and ("html5" in norm_cand or "html" in norm_cand):
                matched.append(target_norm)
            elif target_key in ["css", "css3"] and ("css3" in norm_cand or "css" in norm_cand):
                matched.append(target_norm)
            elif target_key in ["microsoft excel", "excel"] and ("microsoft excel" in norm_cand or "excel" in norm_cand):
                matched.append(target_norm)
            else:
                missing.append(target_norm)

        return sorted(list(dict.fromkeys(matched))), sorted(list(dict.fromkeys(missing)))

    @classmethod
    def get_skill_category(cls, skill_name: str) -> str:
        """Assign true canonical category for a skill based on its intrinsic nature."""
        if not skill_name:
            return "Other Technical Skills"
        norm = cls.normalize_skill(skill_name)
        k = norm.lower()
        if k in SKILL_TAXONOMY_CATEGORIES:
            return SKILL_TAXONOMY_CATEGORIES[k]
        
        # Heuristic taxonomy rules
        if any(w in k for w in ["language", "script", "c++", "java", "python", "ruby", "golang", "rust", "kotlin", "swift", "dart"]):
            return "Programming Languages"
        elif any(w in k for w in ["css", "html", "react", "vue", "angular", "frontend", "ui", "web", "tailwind", "bootstrap", "framer", "three"]):
            return "Frontend Technologies"
        elif any(w in k for w in ["backend", "django", "flask", "fastapi", "spring", "express", "node", "server", "rails", "laravel"]):
            return "Backend Technologies"
        elif any(w in k for w in ["sql", "mongo", "database", "postgres", "redis", "db", "storage", "dynamo", "cassandra"]):
            return "Databases & Storage"
        elif any(w in k for w in ["api", "graphql", "rest", "soap", "endpoint", "grpc"]):
            return "APIs & Web Services"
        elif any(w in k for w in ["aws", "azure", "gcp", "cloud", "vercel", "render", "netlify", "heroku", "digitalocean"]):
            return "Cloud & Hosting"
        elif any(w in k for w in ["docker", "kubernetes", "ci/cd", "devops", "jenkins", "linux", "container", "ansible", "terraform"]):
            return "DevOps & Infrastructure"
        elif any(w in k for w in ["auth", "security", "jwt", "oauth", "crypto"]):
            return "Authentication & Security"
        elif any(w in k for w in ["figma", "design", "ux", "wireframe", "prototype", "adobe", "canva"]):
            return "UI / UX Design"
        elif any(w in k for w in ["test", "jest", "playwright", "selenium", "cypress", "qa", "pytest"]):
            return "Testing & QA"
        elif any(w in k for w in ["learning", "nlp", "vision", "ai", "pandas", "numpy", "data science", "torch", "tensor"]):
            return "Data Science & AI"
        elif any(w in k for w in ["excel", "power bi", "tableau", "bi", "analytics", "looker"]):
            return "Business Intelligence"
        elif any(w in k for w in ["git", "github", "gitlab", "bitbucket", "jira", "tool", "postman", "swagger", "vscode", "npm", "yarn"]):
            return "Development Tools"
        elif any(w in k for w in ["algorithm", "structure", "system design", "oop", "architecture", "debugging"]):
            return "Core Computer Science"
        elif any(w in k for w in ["communication", "problem solving", "collaboration", "leadership", "teamwork", "agile", "scrum", "time management"]):
            return "Soft Skills & Attributes"
        elif any(w in k for w in ["office", "word", "powerpoint", "workspace"]):
            return "Office Productivity"
        
        return "Other Technical Skills"

    @classmethod
    def build_master_skill_set(cls, candidate: Any) -> Dict[str, Dict[str, Any]]:
        """
        Construct a comprehensive, non-lossy Master Skill Set from ALL Module 1 sources:
        1. skills.* (all 19 categories + skill_evidence)
        2. professional_summary / summary
        3. experience[].responsibilities, experience[].technologies, experience[].details, experience[].source_text
        4. projects[].description, projects[].technologies, projects[].details, projects[].source_text
        5. certifications
        6. raw_text / resume_text / full_text
        """
        if hasattr(candidate, "to_dict"):
            data = candidate.to_dict()
        elif isinstance(candidate, dict):
            data = candidate
        else:
            data = {}

        master_map: Dict[str, Dict[str, Any]] = {}

        # ------------------------------------------------------------------
        # SECTION LABEL PATTERNS — strip e.g. "Languages:", "Frontend:", etc.
        # ------------------------------------------------------------------
        _SECTION_LABEL_RE = re.compile(
            r"^(?:languages?|programming\s+languages?|frontend|backend|databases?|cloud|tools?|"
            r"platforms?|frameworks?|libraries|apis?|web\s+technologies?|skills?|technologies?|"
            r"tools\s+&?\s*platforms?|cloud\s*/?\s*deployment|devops|testing|ui\s*/?\s*ux|"
            r"soft\s+skills?|certifications?|other|additional|misc(?:ellaneous)?)\s*:?\s*",
            re.IGNORECASE,
        )

        # Long separator between section names in combined strings like
        # "Languages: Python ... Frontend: HTML ..."
        _SECTION_SPLIT_RE = re.compile(
            r"(?:languages?|programming\s+languages?|frontend|backend|databases?|cloud|tools?|"
            r"platforms?|frameworks?|libraries|apis?|web\s+technologies?|skills?|technologies?|"
            r"tools\s+&?\s*platforms?|cloud\s*/?\s*deployment|devops|testing|ui\s*/?\s*ux|"
            r"soft\s+skills?|certifications?|other|additional|misc(?:ellaneous)?)\s*:",
            re.IGNORECASE,
        )

        def _is_atomic_skill(s: str) -> bool:
            """
            Return True only when s looks like a single skill name, not a sentence,
            paragraph, combined list, or section label.
            Rules:
            - Length ≤ 60 characters (e.g. "Django REST Framework" = 21, "Machine Learning" = 16)
            - Does NOT contain a colon that looks like "Label: ..."
            - Does NOT contain 3+ comma-separated tokens (that's a list, not a skill)
            - Does NOT start with a section label like "Languages:", "Frontend:", etc.
            - Does NOT look like a sentence (contains verb-like patterns or > 8 words)
            """
            if not s or len(s) > 80:
                return False
            # Reject if it looks like a sentence (has >7 space-separated tokens)
            words = s.split()
            if len(words) > 7:
                return False
            # Reject if it contains a colon surrounded by words (section label pattern)
            if re.search(r'\w+\s*:\s*\w', s):
                return False
            # Reject if it has 3+ comma-separated parts
            if s.count(',') >= 2:
                return False
            # Reject if it starts with a known section label
            if _SECTION_LABEL_RE.match(s):
                remainder = _SECTION_LABEL_RE.sub('', s).strip()
                if not remainder or ',' in remainder:
                    return False
            # Reject very common non-skill patterns
            if re.search(r'\b(developed|built|implemented|worked|created|designed|managed|led|used|using|with|and)\b', s, re.IGNORECASE):
                return False
            return True

        def _atomize(raw: str) -> list:
            """
            Split a potentially multi-skill or section-prefixed string into individual
            atomic skill tokens. Returns an empty list if the string is clearly a
            sentence or non-skill text.
            """
            if not raw or not isinstance(raw, str):
                return []
            s = raw.strip()
            if not s:
                return []

            # First: if the string contains section labels, split on them
            if _SECTION_SPLIT_RE.search(s):
                # Split on section boundaries, then recurse on each part
                parts = _SECTION_SPLIT_RE.split(s)
                tokens = []
                for part in parts:
                    tokens.extend(_atomize(part))
                return tokens

            # Strip leading section label (e.g. "Languages: Python" → "Python")
            s = _SECTION_LABEL_RE.sub('', s).strip()
            if not s:
                return []

            # Split on commas → individual candidates
            if ',' in s:
                candidates = [t.strip() for t in s.split(',') if t.strip()]
                # Also handle " / " separators within tokens like "Three.js / React Three Fiber"
                results = []
                for c in candidates:
                    # Keep "X / Y" if both X and Y are known skills (e.g. "Three.js / React Three Fiber")
                    slash_parts = [p.strip() for p in c.split('/') if p.strip()]
                    if len(slash_parts) > 1:
                        for sp in slash_parts:
                            if _is_atomic_skill(sp):
                                results.append(sp)
                    else:
                        if _is_atomic_skill(c):
                            results.append(c)
                return results

            # Handle " / " within a single token
            slash_parts = [p.strip() for p in s.split('/') if p.strip()]
            if len(slash_parts) > 1:
                results = []
                for sp in slash_parts:
                    if _is_atomic_skill(sp):
                        results.append(sp)
                return results

            # Single token — validate as atomic skill
            if _is_atomic_skill(s):
                return [s]
            return []

        def _record(raw_name: str, source_type: str, evidence: str, confidence: str = "high"):
            """
            Record a skill into master_map after atomization, normalization, and validation.
            Raw multi-skill strings and sentences are silently split or discarded.
            """
            for token in _atomize(raw_name):
                if not token or not isinstance(token, str):
                    continue
                cleaned = token.strip()
                if not cleaned:
                    continue
                norm = cls.normalize_skill(cleaned)
                if not norm:
                    continue
                norm_k = norm.lower()
                cat = cls.get_skill_category(norm)

                if norm_k not in master_map:
                    master_map[norm_k] = {
                        "skill": cleaned,
                        "normalized_skill": norm,
                        "category": cat,
                        "evidence": evidence,
                        "evidence_source": source_type,
                        "confidence": confidence,
                    }
                else:
                    prio = {
                        "EXPLICIT_SKILL": 7,
                        "PROJECT_TECHNOLOGY": 6,
                        "EXPERIENCE_TECHNOLOGY": 5,
                        "CERTIFICATION_EVIDENCE": 4,
                        "RAW_TEXT_EVIDENCE": 4,
                        "PROJECT_EVIDENCE": 3,
                        "EXPERIENCE_EVIDENCE": 2,
                        "SUMMARY_EVIDENCE": 1,
                    }
                    curr_prio = prio.get(master_map[norm_k]["evidence_source"], 0)
                    new_prio = prio.get(source_type, 0)
                    if new_prio > curr_prio:
                        master_map[norm_k]["evidence_source"] = source_type
                        master_map[norm_k]["evidence"] = evidence
                        master_map[norm_k]["confidence"] = confidence

        # 1. Inspect structured skills (all 19 categories)
        s_obj = data.get("skills", {})
        if isinstance(s_obj, list):
            for sk in s_obj:
                _record(str(sk), "EXPLICIT_SKILL", f"Explicitly listed under skills: {sk}", "high")
        elif isinstance(s_obj, dict):
            for cat_k, cat_v in s_obj.items():
                if cat_k == "skill_evidence" and isinstance(cat_v, list):
                    for ev in cat_v:
                        if isinstance(ev, dict):
                            s_name = ev.get("canonical_name") or ev.get("skill") or ""
                            s_src = ev.get("source", "skills section")
                            s_conf = ev.get("confidence", "high")
                            _record(s_name, "EXPLICIT_SKILL", f"Evidence from {s_src}: {s_name}", s_conf)
                elif isinstance(cat_v, list):
                    for sk in cat_v:
                        # Each list item may itself be a comma-delimited string — _record handles splitting
                        _record(str(sk), "EXPLICIT_SKILL", f"Listed under skills.{cat_k}: {sk}", "high")
                elif isinstance(cat_v, str):
                    # String value of a skill category — atomize before recording
                    _record(cat_v, "EXPLICIT_SKILL", f"Listed under skills.{cat_k}", "high")
                # dict values are skipped (not meaningful as individual skills)

        # Flat fallback
        for fsk in data.get("skills_flat", []) or []:
            _record(str(fsk), "EXPLICIT_SKILL", f"Listed in skills profile: {fsk}", "high")

        # 2. Inspect projects
        for p in data.get("projects", []) or []:
            if isinstance(p, dict):
                p_name = p.get("name") or p.get("title") or "Project"
                for t in p.get("technologies", []) or []:
                    _record(str(t), "PROJECT_TECHNOLOGY", f"Used in project '{p_name}': {t}", "high")
                p_text = " ".join([
                    str(p.get("description") or ""),
                    str(p.get("details") or ""),
                    str(p.get("source_text") or "")
                ])
                for alias, canonical in CANONICAL_SKILL_ALIASES.items():
                    if len(alias) >= 2 and re.search(r'\b' + re.escape(alias) + r'\b', p_text, re.IGNORECASE):
                        _record(canonical, "PROJECT_EVIDENCE", f"Demonstrated in project '{p_name}': {p_text[:120]}...", "medium")

        # 3. Inspect experience
        exp = data.get("experience") or {}
        exp_list = []
        if isinstance(exp, list):
            exp_list = exp
        elif isinstance(exp, dict):
            exp_list = exp.get("full_time", []) + exp.get("internships", []) + exp.get("details", []) + exp.get("previous_roles", [])

        for e in exp_list:
            if isinstance(e, dict):
                comp = e.get("company") or e.get("organization") or "Experience"
                role_t = e.get("role") or e.get("title") or "Role"
                for t in e.get("technologies", []) or []:
                    _record(str(t), "EXPERIENCE_TECHNOLOGY", f"Used at {comp} as {role_t}: {t}", "high")
                resp_text = " ".join([
                    str(e.get("responsibilities") or ""),
                    str(e.get("description") or ""),
                    str(e.get("details") or ""),
                    str(e.get("source_text") or ""),
                    str(e.get("summary") or "")
                ])
                for alias, canonical in CANONICAL_SKILL_ALIASES.items():
                    if len(alias) >= 2 and re.search(r'\b' + re.escape(alias) + r'\b', resp_text, re.IGNORECASE):
                        _record(canonical, "EXPERIENCE_EVIDENCE", f"Demonstrated at {comp}: {resp_text[:120]}...", "medium")

        # 4. Inspect professional summary
        summ_text = str(data.get("professional_summary") or data.get("summary") or "")
        if summ_text:
            for alias, canonical in CANONICAL_SKILL_ALIASES.items():
                if len(alias) >= 2 and re.search(r'\b' + re.escape(alias) + r'\b', summ_text, re.IGNORECASE):
                    _record(canonical, "SUMMARY_EVIDENCE", f"Mentioned in summary: {summ_text[:120]}...", "medium")

        # 5. Inspect certifications
        for c in data.get("certifications", []) or []:
            c_name = c.get("name") if isinstance(c, dict) else str(c)
            for alias, canonical in CANONICAL_SKILL_ALIASES.items():
                if len(alias) >= 2 and re.search(r'\b' + re.escape(alias) + r'\b', c_name, re.IGNORECASE):
                    _record(canonical, "CERTIFICATION_EVIDENCE", f"Certified in: {c_name}", "high")

        # 6. RAW RESUME VALIDATION: scan raw_text / resume_text / full_text
        raw_t = str(data.get("raw_text") or data.get("resume_text") or data.get("full_text") or "")
        if raw_t:
            for alias, canonical in CANONICAL_SKILL_ALIASES.items():
                if len(alias) >= 2 and re.search(r'\b' + re.escape(alias) + r'\b', raw_t, re.IGNORECASE):
                    _record(canonical, "RAW_TEXT_EVIDENCE", f"Explicitly found in raw resume text: {alias}", "high")

        return master_map

    @classmethod
    def build_categorized_skills_matrix(cls, candidate: Any) -> Dict[str, List[str]]:
        """
        Build the complete, deduplicated Categorized Skills Matrix sorted by standard category order.
        Guarantees NO skill loss and zero arbitrary capping.
        """
        master_skills = cls.build_master_skill_set(candidate)
        matrix: Dict[str, List[str]] = {}

        for item in master_skills.values():
            cat = item["category"]
            skill_name = item["normalized_skill"]
            if cat not in matrix:
                matrix[cat] = []
            if skill_name not in matrix[cat]:
                matrix[cat].append(skill_name)

        # Standard display order of categories
        ordered_cats = [
            "Programming Languages",
            "Frontend Technologies",
            "Backend Technologies",
            "APIs & Web Services",
            "Authentication & Security",
            "Databases & Storage",
            "Cloud & Hosting",
            "DevOps & Infrastructure",
            "Development Tools",
            "UI / UX Design",
            "Data Science & AI",
            "Business Intelligence",
            "Testing & QA",
            "Core Computer Science",
            "Office Productivity",
            "Soft Skills & Attributes",
            "Other Technical Skills",
        ]

        ordered_matrix: Dict[str, List[str]] = {}
        for cat in ordered_cats:
            if cat in matrix and matrix[cat]:
                ordered_matrix[cat] = sorted(matrix[cat])

        # Any extra custom categories
        for cat, skills in matrix.items():
            if cat not in ordered_matrix and skills:
                ordered_matrix[cat] = sorted(skills)

        return ordered_matrix
