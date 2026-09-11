"""Skill Taxonomy, Canonical Entities, Aliases, and Relationship Graph."""
import os
import json
from typing import Dict, List, Any, Optional, Tuple


CANONICAL_SKILLS: List[Dict[str, Any]] = [
    # Programming Languages
    {"skill_id": "SK-PY", "skill_name": "Python", "canonical_name": "Python", "category": "Programming Languages", "subcategory": "General Purpose / Backend", "description": "High-level interpreted language for backend, automation, and AI.", "technology_status": "widely_used", "aliases": ["Python", "Python3", "py"]},
    {"skill_id": "SK-JAV", "skill_name": "Java", "canonical_name": "Java", "category": "Programming Languages", "subcategory": "Enterprise / Object-Oriented", "description": "Enterprise-grade object-oriented programming language.", "technology_status": "established", "aliases": ["Java", "Java 8", "Java 11", "Java 17", "Java 21", "Core Java"]},
    {"skill_id": "SK-JS", "skill_name": "JavaScript", "canonical_name": "JavaScript", "category": "Programming Languages", "subcategory": "Client & Server Web", "description": "Fundamental scripting language for web interactivity.", "technology_status": "widely_used", "aliases": ["JavaScript", "JS", "ES6", "ES6+", "ECMAScript"]},
    {"skill_id": "SK-TS", "skill_name": "TypeScript", "canonical_name": "TypeScript", "category": "Programming Languages", "subcategory": "Typed Client & Server", "description": "Typed superset of JavaScript providing static types.", "technology_status": "widely_used", "aliases": ["TypeScript", "TS"]},
    {"skill_id": "SK-CPP", "skill_name": "C++", "canonical_name": "C++", "category": "Programming Languages", "subcategory": "Systems & High Performance", "description": "High-performance language for systems and algorithmic applications.", "technology_status": "established", "aliases": ["C++", "CPP", "C / C++"]},
    {"skill_id": "SK-CSH", "skill_name": "C#", "canonical_name": "C#", "category": "Programming Languages", "subcategory": "Enterprise / .NET", "description": "Modern object-oriented language for enterprise and games.", "technology_status": "established", "aliases": ["C#", "CSharp", ".NET C#"]},
    {"skill_id": "SK-GO", "skill_name": "Go", "canonical_name": "Go", "category": "Programming Languages", "subcategory": "Cloud & Concurrency", "description": "High-concurrency compiled language for cloud infrastructure.", "technology_status": "growing", "aliases": ["Go", "Golang"]},
    {"skill_id": "SK-SQL", "skill_name": "SQL", "canonical_name": "SQL", "category": "Databases & Querying", "subcategory": "Relational Querying", "description": "Standard language for querying and managing relational databases.", "technology_status": "established", "aliases": ["SQL", "Structured Query Language", "T-SQL", "PL/SQL"]},

    # Frontend Frameworks & Libraries
    {"skill_id": "SK-HTML", "skill_name": "HTML5", "canonical_name": "HTML5", "category": "Frontend Development", "subcategory": "Markup & Structure", "description": "Semantic markup language for web applications.", "technology_status": "established", "aliases": ["HTML5", "HTML", "HTML 5"]},
    {"skill_id": "SK-CSS", "skill_name": "CSS3", "canonical_name": "CSS3", "category": "Frontend Development", "subcategory": "Styling & Layout", "description": "Styling, layouts, Flexbox, and CSS Grid for web interfaces.", "technology_status": "established", "aliases": ["CSS3", "CSS", "CSS 3", "Cascading Style Sheets"]},
    {"skill_id": "SK-RCT", "skill_name": "React", "canonical_name": "React", "category": "Frontend Frameworks", "subcategory": "Component UI", "description": "Component-based library for single-page applications.", "technology_status": "widely_used", "aliases": ["React", "React.js", "ReactJS"]},
    {"skill_id": "SK-ANG", "skill_name": "Angular", "canonical_name": "Angular", "category": "Frontend Frameworks", "subcategory": "Enterprise Frontend", "description": "Full-featured TypeScript frontend framework.", "technology_status": "established", "aliases": ["Angular", "AngularJS", "Angular 2+"]},
    {"skill_id": "SK-VUE", "skill_name": "Vue.js", "canonical_name": "Vue.js", "category": "Frontend Frameworks", "subcategory": "Reactive UI", "description": "Progressive reactive framework for web UIs.", "technology_status": "established", "aliases": ["Vue.js", "Vue", "VueJS"]},
    {"skill_id": "SK-NXT", "skill_name": "Next.js", "canonical_name": "Next.js", "category": "Frontend Frameworks", "subcategory": "Full-Stack React", "description": "React framework for server-side rendering and static sites.", "technology_status": "growing", "aliases": ["Next.js", "NextJS", "Next"]},
    {"skill_id": "SK-TLW", "skill_name": "Tailwind CSS", "canonical_name": "Tailwind CSS", "category": "Frontend Development", "subcategory": "Utility CSS", "description": "Utility-first CSS framework for rapid UI styling.", "technology_status": "growing", "aliases": ["Tailwind CSS", "Tailwind"]},
    {"skill_id": "SK-BST", "skill_name": "Bootstrap", "canonical_name": "Bootstrap", "category": "Frontend Development", "subcategory": "CSS Framework", "description": "Responsive grid and component CSS framework.", "technology_status": "established", "aliases": ["Bootstrap", "Bootstrap 5", "Bootstrap 4"]},

    # Backend Frameworks
    {"skill_id": "SK-FAP", "skill_name": "FastAPI", "canonical_name": "FastAPI", "category": "Backend Frameworks", "subcategory": "Python Asynchronous REST", "description": "High-performance Python asynchronous API framework.", "technology_status": "growing", "aliases": ["FastAPI", "Fast API"]},
    {"skill_id": "SK-DJG", "skill_name": "Django", "canonical_name": "Django", "category": "Backend Frameworks", "subcategory": "Full-Featured Python", "description": "High-level Python web framework with built-in ORM.", "technology_status": "established", "aliases": ["Django", "Django REST Framework", "DRF"]},
    {"skill_id": "SK-FLK", "skill_name": "Flask", "canonical_name": "Flask", "category": "Backend Frameworks", "subcategory": "Python Microframework", "description": "Lightweight Python microframework for APIs.", "technology_status": "established", "aliases": ["Flask"]},
    {"skill_id": "SK-SPB", "skill_name": "Spring Boot", "canonical_name": "Spring Boot", "category": "Backend Frameworks", "subcategory": "Enterprise Java", "description": "Leading Java microservices framework.", "technology_status": "widely_used", "aliases": ["Spring Boot", "Spring", "Spring Framework", "SpringBoot"]},
    {"skill_id": "SK-NOD", "skill_name": "Node.js", "canonical_name": "Node.js", "category": "Backend Frameworks", "subcategory": "JavaScript Server", "description": "Server-side JavaScript runtime for asynchronous services.", "technology_status": "widely_used", "aliases": ["Node.js", "Node", "NodeJS"]},
    {"skill_id": "SK-EXP", "skill_name": "Express.js", "canonical_name": "Express.js", "category": "Backend Frameworks", "subcategory": "Node API", "description": "Fast minimalist web framework for Node.js.", "technology_status": "established", "aliases": ["Express.js", "Express", "ExpressJS"]},

    # Databases
    {"skill_id": "SK-PG", "skill_name": "PostgreSQL", "canonical_name": "PostgreSQL", "category": "Databases & Querying", "subcategory": "Relational RDBMS", "description": "Powerful open-source object-relational database.", "technology_status": "widely_used", "aliases": ["PostgreSQL", "Postgres", "Postgres DB"]},
    {"skill_id": "SK-MYS", "skill_name": "MySQL", "canonical_name": "MySQL", "category": "Databases & Querying", "subcategory": "Relational RDBMS", "description": "Widely used open-source relational database.", "technology_status": "established", "aliases": ["MySQL", "My SQL"]},
    {"skill_id": "SK-MDB", "skill_name": "MongoDB", "canonical_name": "MongoDB", "category": "Databases & Querying", "subcategory": "Document NoSQL", "description": "Document-oriented NoSQL database.", "technology_status": "established", "aliases": ["MongoDB", "Mongo"]},
    {"skill_id": "SK-RDS", "skill_name": "Redis", "canonical_name": "Redis", "category": "Databases & Querying", "subcategory": "In-Memory Caching", "description": "In-memory key-value data structure store and cache.", "technology_status": "widely_used", "aliases": ["Redis"]},
    {"skill_id": "SK-SQLT", "skill_name": "SQLite", "canonical_name": "SQLite", "category": "Databases & Querying", "subcategory": "Embedded Relational", "description": "Lightweight disk-based embedded SQL database.", "technology_status": "established", "aliases": ["SQLite", "SQLite3"]},

    # Cloud & DevOps
    {"skill_id": "SK-GIT", "skill_name": "Git", "canonical_name": "Git", "category": "DevOps & Tools", "subcategory": "Version Control", "description": "Distributed version control system for source code.", "technology_status": "widely_used", "aliases": ["Git", "Version Control"]},
    {"skill_id": "SK-GH", "skill_name": "GitHub", "canonical_name": "GitHub", "category": "DevOps & Tools", "subcategory": "Code Hosting & Collaboration", "description": "Platform for hosting code repositories and PR reviews.", "technology_status": "widely_used", "aliases": ["GitHub", "Git Hub"]},
    {"skill_id": "SK-DCK", "skill_name": "Docker", "canonical_name": "Docker", "category": "DevOps & Tools", "subcategory": "Containerization", "description": "Platform for packaging applications into containers.", "technology_status": "widely_used", "aliases": ["Docker", "Containerization", "Docker Compose"]},
    {"skill_id": "SK-K8S", "skill_name": "Kubernetes", "canonical_name": "Kubernetes", "category": "DevOps & Tools", "subcategory": "Container Orchestration", "description": "Orchestration system for container deployment and scaling.", "technology_status": "widely_used", "aliases": ["Kubernetes", "K8s"]},
    {"skill_id": "SK-AWS", "skill_name": "AWS", "canonical_name": "AWS", "category": "Cloud Platforms", "subcategory": "Public Cloud", "description": "Amazon Web Services cloud computing platform.", "technology_status": "widely_used", "aliases": ["AWS", "Amazon Web Services", "EC2", "S3", "AWS Cloud"]},
    {"skill_id": "SK-AZR", "skill_name": "Azure", "canonical_name": "Azure", "category": "Cloud Platforms", "subcategory": "Public Cloud", "description": "Microsoft Azure cloud computing platform.", "technology_status": "widely_used", "aliases": ["Azure", "Microsoft Azure"]},
    {"skill_id": "SK-GCP", "skill_name": "GCP", "canonical_name": "GCP", "category": "Cloud Platforms", "subcategory": "Public Cloud", "description": "Google Cloud Platform infrastructure and services.", "technology_status": "established", "aliases": ["GCP", "Google Cloud Platform", "Google Cloud"]},
    {"skill_id": "SK-LNX", "skill_name": "Linux", "canonical_name": "Linux", "category": "DevOps & Tools", "subcategory": "Operating System", "description": "Open-source Unix-like operating system kernel.", "technology_status": "established", "aliases": ["Linux", "Ubuntu", "CentOS", "Debian", "RedHat"]},
    {"skill_id": "SK-CICD", "skill_name": "CI/CD", "canonical_name": "CI/CD", "category": "DevOps & Tools", "subcategory": "Continuous Delivery", "description": "Continuous integration and deployment automation.", "technology_status": "widely_used", "aliases": ["CI/CD", "CI / CD", "Continuous Integration", "Continuous Deployment", "GitHub Actions", "Jenkins"]},

    # Data Science & Machine Learning
    {"skill_id": "SK-PND", "skill_name": "Pandas", "canonical_name": "Pandas", "category": "Data Science & ML", "subcategory": "Data Manipulation", "description": "Python library for structured tabular data manipulation.", "technology_status": "widely_used", "aliases": ["Pandas", "pd"]},
    {"skill_id": "SK-NUM", "skill_name": "NumPy", "canonical_name": "NumPy", "category": "Data Science & ML", "subcategory": "Array Computing", "description": "Multi-dimensional array computing library for Python.", "technology_status": "widely_used", "aliases": ["NumPy", "Numpy", "np"]},
    {"skill_id": "SK-SKL", "skill_name": "Scikit-Learn", "canonical_name": "Scikit-Learn", "category": "Data Science & ML", "subcategory": "Machine Learning", "description": "Machine learning algorithms and predictive modeling in Python.", "technology_status": "widely_used", "aliases": ["Scikit-Learn", "scikit-learn", "sklearn", "Scikit Learn"]},
    {"skill_id": "SK-TF", "skill_name": "TensorFlow", "canonical_name": "TensorFlow", "category": "Data Science & ML", "subcategory": "Deep Learning", "description": "End-to-end open-source machine learning framework.", "technology_status": "established", "aliases": ["TensorFlow", "Tensorflow", "TF", "Keras"]},
    {"skill_id": "SK-TOR", "skill_name": "PyTorch", "canonical_name": "PyTorch", "category": "Data Science & ML", "subcategory": "Deep Learning", "description": "Flexible deep learning framework for research and vision/NLP.", "technology_status": "widely_used", "aliases": ["PyTorch", "Pytorch", "Torch"]},
    {"skill_id": "SK-EXL", "skill_name": "Microsoft Excel", "canonical_name": "Microsoft Excel", "category": "Data Analytics", "subcategory": "Spreadsheets & Reporting", "description": "Spreadsheet software for financial/data calculations.", "technology_status": "established", "aliases": ["Microsoft Excel", "Excel", "MS Excel", "Spreadsheets"]},
    {"skill_id": "SK-PBI", "skill_name": "Power BI", "canonical_name": "Power BI", "category": "Data Analytics", "subcategory": "Business Intelligence", "description": "Interactive data visualization and business analytics tool.", "technology_status": "widely_used", "aliases": ["Power BI", "PowerBI", "DAX"]},
    {"skill_id": "SK-TBL", "skill_name": "Tableau", "canonical_name": "Tableau", "category": "Data Analytics", "subcategory": "Business Intelligence", "description": "Visual analytics software for corporate BI reporting.", "technology_status": "established", "aliases": ["Tableau", "Tableau Desktop"]},

    # UI/UX & Product Design
    {"skill_id": "SK-FIG", "skill_name": "Figma", "canonical_name": "Figma", "category": "UI/UX Design", "subcategory": "Vector Design & Prototyping", "description": "Industry-standard collaborative vector design and UI/UX prototyping platform.", "technology_status": "widely_used", "aliases": ["Figma", "FigJam"]},
    {"skill_id": "SK-AXD", "skill_name": "Adobe XD", "canonical_name": "Adobe XD", "category": "UI/UX Design", "subcategory": "Vector Design & Prototyping", "description": "Wireframing, prototyping, and UI interaction design software.", "technology_status": "established", "aliases": ["Adobe XD", "XD"]},
    {"skill_id": "SK-SKT", "skill_name": "Sketch", "canonical_name": "Sketch", "category": "UI/UX Design", "subcategory": "Vector Design", "description": "Dedicated UI vector design tool for interface and icon design.", "technology_status": "established", "aliases": ["Sketch", "Sketch App"]},
    {"skill_id": "SK-UR", "skill_name": "User Research", "canonical_name": "User Research", "category": "UI/UX Design", "subcategory": "UX Research", "description": "User research and interviews to uncover behaviors and product requirements.", "technology_status": "established", "aliases": ["User Research", "User Interviews", "Persona Creation", "User Personas"]},
    {"skill_id": "SK-WF", "skill_name": "Wireframing", "canonical_name": "Wireframing", "category": "UI/UX Design", "subcategory": "UX Architecture", "description": "Low-fidelity structural blueprints for application screens and flows.", "technology_status": "established", "aliases": ["Wireframing", "Wireframes", "Low-Fidelity Mockups"]},
    {"skill_id": "SK-PRT", "skill_name": "Prototyping", "canonical_name": "Prototyping", "category": "UI/UX Design", "subcategory": "Interactive Prototyping", "description": "Interactive prototypes demonstrating user interactions and product flow.", "technology_status": "established", "aliases": ["Prototyping", "Interactive Prototypes", "Clickable Prototypes"]},
    {"skill_id": "SK-UT", "skill_name": "Usability Testing", "canonical_name": "Usability Testing", "category": "UI/UX Design", "subcategory": "UX Evaluation", "description": "Evaluating design interfaces with users to identify navigation blockers.", "technology_status": "established", "aliases": ["Usability Testing", "User Testing", "Usability Studies"]},
    {"skill_id": "SK-DS", "skill_name": "Design Systems", "canonical_name": "Design Systems", "category": "UI/UX Design", "subcategory": "Design Systems", "description": "Reusable component libraries, design tokens, typography, and color consistency.", "technology_status": "widely_used", "aliases": ["Design Systems", "Component Libraries", "Design Tokens"]},
    {"skill_id": "SK-IA", "skill_name": "Information Architecture", "canonical_name": "Information Architecture", "category": "UI/UX Design", "subcategory": "UX Architecture", "description": "Organizing content hierarchies, site navigation, and user flows logically.", "technology_status": "established", "aliases": ["Information Architecture", "IA", "Site Mapping"]},

    # Big Data & Data Engineering
    {"skill_id": "SK-SPK", "skill_name": "Apache Spark", "canonical_name": "Apache Spark", "category": "Data Engineering", "subcategory": "Distributed Processing", "description": "High-performance distributed computing for big data pipelines and ETL.", "technology_status": "widely_used", "aliases": ["Apache Spark", "Spark", "PySpark"]},
    {"skill_id": "SK-AFL", "skill_name": "Airflow", "canonical_name": "Airflow", "category": "Data Engineering", "subcategory": "Workflow Orchestration", "description": "Orchestrating, scheduling, and monitoring complex multi-stage DAG data pipelines.", "technology_status": "widely_used", "aliases": ["Airflow", "Apache Airflow", "DAGs"]},
    {"skill_id": "SK-KFK", "skill_name": "Kafka", "canonical_name": "Kafka", "category": "Data Engineering", "subcategory": "Event Streaming", "description": "High-throughput event streaming and distributed message queuing.", "technology_status": "widely_used", "aliases": ["Kafka", "Apache Kafka", "Event Streaming"]},
    {"skill_id": "SK-SNW", "skill_name": "Snowflake", "canonical_name": "Snowflake", "category": "Data Engineering", "subcategory": "Cloud Data Warehouse", "description": "Enterprise cloud data warehouse designed for high-concurrency SQL analytics.", "technology_status": "widely_used", "aliases": ["Snowflake", "Snowflake DB"]},
    {"skill_id": "SK-ETL", "skill_name": "ETL Pipelines", "canonical_name": "ETL Pipelines", "category": "Data Engineering", "subcategory": "Data Pipelines", "description": "Extract, transform, and load data reliably across corporate databases and warehouses.", "technology_status": "established", "aliases": ["ETL Pipelines", "ETL", "ELT", "Data Pipelines"]},

    # Engineering Concepts & Architecture
    {"skill_id": "SK-DSA", "skill_name": "Data Structures & Algorithms", "canonical_name": "Data Structures & Algorithms", "category": "Computer Science Concepts", "subcategory": "Core CS", "description": "Efficient data organization, searching, and sorting.", "technology_status": "established", "aliases": ["Data Structures & Algorithms", "DSA", "Data Structures", "Algorithms"]},
    {"skill_id": "SK-OOP", "skill_name": "Object-Oriented Programming", "canonical_name": "Object-Oriented Programming", "category": "Computer Science Concepts", "subcategory": "Design Paradigm", "description": "Design based on objects, inheritance, polymorphism, and encapsulation.", "technology_status": "established", "aliases": ["Object-Oriented Programming", "OOP", "Object Oriented Programming"]},
    {"skill_id": "SK-RST", "skill_name": "REST API", "canonical_name": "REST API", "category": "API & Networking", "subcategory": "Web Services", "description": "Representational state transfer HTTP API endpoints.", "technology_status": "widely_used", "aliases": ["REST API", "RESTful API", "REST APIs", "REST", "Web APIs"]},
    {"skill_id": "SK-TST", "skill_name": "Software Testing", "canonical_name": "Software Testing", "category": "Quality Assurance & Testing", "subcategory": "Test Engineering", "description": "Automated unit, integration, and regression testing.", "technology_status": "established", "aliases": ["Software Testing", "Unit Testing", "Testing", "pytest", "JUnit", "Selenium"]},
    {"skill_id": "SK-AUTH", "skill_name": "Authentication", "canonical_name": "Authentication", "category": "Security & Systems", "subcategory": "Access Control", "description": "User identity verification via JWT, OAuth2, and sessions.", "technology_status": "established", "aliases": ["Authentication", "Auth", "JWT", "OAuth", "OAuth2"]},
    {"skill_id": "SK-RESP", "skill_name": "Responsive Design", "canonical_name": "Responsive Design", "category": "Frontend Development", "subcategory": "Cross-Device Layout", "description": "Cross-device responsive design and fluid viewport layouts.", "technology_status": "established", "aliases": ["Responsive Design", "Mobile-Friendly", "Responsive Layouts"]},
]


SKILL_RELATIONSHIPS: List[Dict[str, Any]] = [
    # (source, target, type, weight)
    {"source_skill_id": "SK-RCT", "target_skill_id": "SK-JS", "relationship_type": "requires", "weight": 1.0, "confidence": 0.99},
    {"source_skill_id": "SK-ANG", "target_skill_id": "SK-TS", "relationship_type": "requires", "weight": 1.0, "confidence": 0.99},
    {"source_skill_id": "SK-VUE", "target_skill_id": "SK-JS", "relationship_type": "requires", "weight": 1.0, "confidence": 0.99},
    {"source_skill_id": "SK-NXT", "target_skill_id": "SK-RCT", "relationship_type": "extension_of", "weight": 0.90, "confidence": 0.95},
    {"source_skill_id": "SK-RCT", "target_skill_id": "SK-VUE", "relationship_type": "alternative_to", "weight": 0.70, "confidence": 0.90},
    {"source_skill_id": "SK-RCT", "target_skill_id": "SK-ANG", "relationship_type": "alternative_to", "weight": 0.65, "confidence": 0.90},
    {"source_skill_id": "SK-DJG", "target_skill_id": "SK-PY", "relationship_type": "requires", "weight": 1.0, "confidence": 0.99},
    {"source_skill_id": "SK-FAP", "target_skill_id": "SK-PY", "relationship_type": "requires", "weight": 1.0, "confidence": 0.99},
    {"source_skill_id": "SK-FLK", "target_skill_id": "SK-PY", "relationship_type": "requires", "weight": 1.0, "confidence": 0.99},
    {"source_skill_id": "SK-SPB", "target_skill_id": "SK-JAV", "relationship_type": "requires", "weight": 1.0, "confidence": 0.99},
    {"source_skill_id": "SK-EXP", "target_skill_id": "SK-NOD", "relationship_type": "requires", "weight": 1.0, "confidence": 0.99},
    {"source_skill_id": "SK-NOD", "target_skill_id": "SK-JS", "relationship_type": "ecosystem_of", "weight": 0.95, "confidence": 0.99},
    {"source_skill_id": "SK-PG", "target_skill_id": "SK-SQL", "relationship_type": "commonly_used_with", "weight": 0.95, "confidence": 0.99},
    {"source_skill_id": "SK-MYS", "target_skill_id": "SK-SQL", "relationship_type": "commonly_used_with", "weight": 0.95, "confidence": 0.99},
    {"source_skill_id": "SK-AWS", "target_skill_id": "SK-AZR", "relationship_type": "alternative_to", "weight": 0.75, "confidence": 0.90},
    {"source_skill_id": "SK-AWS", "target_skill_id": "SK-GCP", "relationship_type": "alternative_to", "weight": 0.75, "confidence": 0.90},
    {"source_skill_id": "SK-K8S", "target_skill_id": "SK-DCK", "relationship_type": "commonly_used_with", "weight": 0.90, "confidence": 0.95},
    {"source_skill_id": "SK-SKL", "target_skill_id": "SK-PY", "relationship_type": "requires", "weight": 1.0, "confidence": 0.99},
    {"source_skill_id": "SK-PND", "target_skill_id": "SK-PY", "relationship_type": "requires", "weight": 1.0, "confidence": 0.99},
    {"source_skill_id": "SK-NUM", "target_skill_id": "SK-PY", "relationship_type": "requires", "weight": 1.0, "confidence": 0.99},
    {"source_skill_id": "SK-TOR", "target_skill_id": "SK-PY", "relationship_type": "requires", "weight": 1.0, "confidence": 0.99},
    {"source_skill_id": "SK-PBI", "target_skill_id": "SK-TBL", "relationship_type": "alternative_to", "weight": 0.80, "confidence": 0.92},
]


def export_skill_taxonomy_files(output_dir: str):
    """Export skills.csv, skill_aliases.csv, skill_relationships.csv, taxonomy.json."""
    os.makedirs(output_dir, exist_ok=True)
    import pandas as pd
    
    # 1. skills.csv
    skills_rows = []
    alias_rows = []
    for s in CANONICAL_SKILLS:
        skills_rows.append({
            "skill_id": s["skill_id"],
            "skill_name": s["skill_name"],
            "canonical_name": s["canonical_name"],
            "category": s["category"],
            "subcategory": s["subcategory"],
            "description": s["description"],
            "technology_status": s["technology_status"],
            "aliases": ";".join(s["aliases"]),
            "source_count": 1500,
            "confidence": 0.95,
        })
        for al in s["aliases"]:
            alias_rows.append({
                "skill_id": s["skill_id"],
                "alias": al,
                "alias_type": "exact_match" if al == s["canonical_name"] else "abbreviation_or_synonym",
                "confidence": 0.95,
            })
            
    df_skills = pd.DataFrame(skills_rows)
    df_skills.to_csv(os.path.join(output_dir, "skills.csv"), index=False)
    
    df_aliases = pd.DataFrame(alias_rows)
    df_aliases.to_csv(os.path.join(output_dir, "skill_aliases.csv"), index=False)
    
    df_rel = pd.DataFrame(SKILL_RELATIONSHIPS)
    df_rel.to_csv(os.path.join(output_dir, "skill_relationships.csv"), index=False)

    print(f"Exported skills.csv ({len(df_skills)}), skill_aliases.csv ({len(df_aliases)}), skill_relationships.csv ({len(df_rel)}) to {output_dir}")
