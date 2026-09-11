"""Enterprise Job Role Knowledge Base for Module 2: AI Career Intelligence Engine.

Defines technical role requirements, categorized skill tiers (Essential, Common,
Recommended, Advanced), typical responsibilities, daily work activities, grouped
tech stacks, interview prep topics, project blueprints, and dependency-aware
learning roadmaps for 17 benchmark engineering and data roles:
1. Frontend Developer
2. Backend Developer
3. Full Stack Developer
4. Software Engineer
5. Web Developer
6. Python Developer
7. Java Developer
8. Data Analyst
9. Data Scientist
10. Machine Learning Engineer
11. DevOps Engineer
12. QA / Test Automation Engineer
13. Mobile Developer
14. Cloud Engineer
15. Cybersecurity Analyst
16. UI Developer
17. Database Developer
"""
from typing import Dict, List, Any, Optional


SKILL_IMPORTANCE_REASONS: Dict[str, str] = {
    "python": "Python is essential for backend services, automation scripts, data science pipelines, and REST API engineering.",
    "java": "Java is an enterprise-grade object-oriented language widely used for high-throughput, mission-critical backend systems.",
    "c": "C provides fundamental understanding of procedural programming, memory management, and systems architectures.",
    "c++": "C++ is widely used for high-performance computing, systems programming, game engines, and low-latency algorithmic systems.",
    "c#": "C# and .NET power enterprise backend services, desktop applications, and scalable cloud systems.",
    "html": "HTML provides the core structure and semantic markup for accessible, standards-compliant web applications.",
    "html5": "HTML5 provides modern semantic structure and accessible elements for responsive web development.",
    "css": "CSS is essential for styling, responsive grid/flexbox layouts, cross-device presentation, and visual hierarchy.",
    "css3": "CSS3 enables modern animations, transitions, responsive grid layouts, and multi-device visual formatting.",
    "javascript": "JavaScript is the fundamental language powering client-side web interactivity, DOM manipulation, and asynchronous network calls.",
    "typescript": "TypeScript adds static typing to JavaScript, improving code predictability, tooling support, and maintainability in large codebases.",
    "react": "React is the industry-standard component library for building fast, maintainable single-page applications (SPAs).",
    "angular": "Angular is a comprehensive enterprise frontend framework featuring built-in dependency injection and TypeScript integration.",
    "vue.js": "Vue.js is a progressive JavaScript framework known for approachable reactivity and component architecture.",
    "sql": "SQL is essential for database querying, CRUD transactions, table schema design, and transactional data persistence.",
    "git": "Git is the industry-standard version control system for tracking source code changes, branching, and team collaboration.",
    "github": "GitHub is the primary platform for hosting code repositories, version control collaboration, pull requests, and developer portfolios.",
    "rest api": "REST APIs enable frontend and backend systems to communicate and exchange structured JSON payloads reliably.",
    "fastapi": "FastAPI is a modern, high-performance Python framework for building asynchronous RESTful APIs with automatic OpenAPI documentation.",
    "django": "Django is a robust Python web framework providing built-in ORM, authentication, admin tooling, and enterprise backend architecture.",
    "flask": "Flask is a lightweight Python microframework suited for modular microservices, prototypes, and lightweight web services.",
    "spring boot": "Spring Boot is the leading enterprise Java framework for building robust, production-grade microservices and APIs.",
    "node.js": "Node.js allows running JavaScript on the server for asynchronous, event-driven, high-concurrency backend services.",
    "express.js": "Express.js is a minimal and flexible Node.js web application framework for building REST APIs.",
    "docker": "Docker containerizes applications to guarantee consistent execution across local development and production cloud environments.",
    "kubernetes": "Kubernetes automates container orchestration, auto-scaling, and cluster management for distributed microservices.",
    "pandas": "Pandas provides high-performance data structures and cleaning tools for structured and tabular datasets.",
    "numpy": "NumPy provides high-performance multi-dimensional array operations and fundamental scientific computing routines.",
    "scikit-learn": "Scikit-Learn provides core machine learning algorithms for predictive modeling, classification, regression, and clustering.",
    "tensorflow": "TensorFlow is an end-to-end framework for training, optimizing, and deploying deep learning and neural network models.",
    "pytorch": "PyTorch is a flexible deep learning library widely used in AI research and production computer vision and NLP systems.",
    "microsoft excel": "Excel is widely used for spreadsheet data analysis, pivot tables, VLOOKUP/XLOOKUP formulas, and executive business reporting.",
    "power bi": "Power BI enables building interactive business intelligence dashboards, DAX queries, and executive reports.",
    "tableau": "Tableau enables rich visual analytics, data storytelling, and interactive corporate reporting across disparate databases.",
    "data structures": "Solid DSA knowledge ensures efficient memory utilization and optimal data organization.",
    "algorithms": "Algorithm optimization ensures software applications run fast and scale well under heavy user and data loads.",
    "data structures & algorithms": "DSA knowledge is fundamental for writing efficient, optimized, and scalable algorithmic logic.",
    "object-oriented programming": "OOP principles (encapsulation, inheritance, polymorphism, abstraction) ensure modular, maintainable software design.",
    "database management": "Understanding relational and NoSQL database concepts is crucial for reliable data persistence and query indexing.",
    "responsive design": "Responsive design ensures web interfaces display smoothly across smartphones, tablets, laptops, and wide monitors.",
    "data analysis": "Data analysis techniques uncover actionable business patterns and statistical insights from raw datasets.",
    "statistics": "Statistical analysis provides the mathematical foundation for evaluating data distributions, hypothesis tests, and AI models.",
    "software testing": "Automated unit and integration testing ensure software reliability and prevent regressions in production deployments.",
    "debugging": "Systematic debugging skills help isolate root causes of runtime errors, inspect stack traces, and optimize execution flow.",
    "authentication": "Secure authentication (JWT, OAuth2, sessions) and authorization protocols protect user data and backend endpoints.",
    "dom concepts": "Understanding DOM manipulation, event bubbling, and browser rendering lifecycles enables smooth dynamic UI behaviors.",
    "linux": "Linux command-line proficiency is essential for server administration, container management, and CI/CD pipelines.",
    "ci/cd": "CI/CD automated pipelines test, build, and deploy code changes rapidly and reliably to production servers.",
    "aws": "Amazon Web Services provides cloud infrastructure for hosting scalable serverless and microservice architectures.",
    "cybersecurity": "Cybersecurity principles ensure network protection, vulnerability mitigation, and secure coding practices.",
    "figma": "Figma is the industry-standard collaborative vector design and UI/UX prototyping platform.",
    "sketch": "Sketch is a dedicated UI vector design tool for macOS interface and icon design.",
    "adobe xd": "Adobe XD provides wireframing, prototyping, and UI interaction design capabilities.",
    "user research": "User research and interviews uncover user behaviors, friction points, and product design requirements.",
    "wireframing": "Wireframing provides low-fidelity structural blueprints for application screens and user flows.",
    "prototyping": "Interactive prototyping demonstrates user interactions, animations, and product usability before development.",
    "usability testing": "Usability testing evaluates design interfaces with real users to identify navigation blockers.",
    "information architecture": "Information architecture organizes content hierarchies, site navigation, and user flows logically.",
    "interaction design": "Interaction design defines how users engage with interactive UI components and screen transitions.",
    "design systems": "Design systems provide reusable component libraries, design tokens, typography, and color consistency.",
    "product design": "Product design bridges user needs, visual aesthetics, and business objectives into cohesive digital products.",
    "wcag": "WCAG guidelines ensure digital interfaces are accessible to users with visual, auditory, or motor impairments.",
    "apache spark": "Apache Spark provides high-performance distributed computing for big data pipelines and ETL workflows.",
    "pyspark": "PySpark allows writing scalable distributed data processing jobs using Python syntax.",
    "airflow": "Apache Airflow orchestrates, schedules, and monitors complex multi-stage DAG data pipelines.",
    "kafka": "Apache Kafka enables high-throughput, low-latency event streaming and distributed message queuing.",
    "snowflake": "Snowflake is an enterprise cloud data warehouse designed for high-concurrency SQL analytics.",
    "bigquery": "Google BigQuery provides serverless, highly-scalable cloud data warehousing for analytics.",
    "redshift": "Amazon Redshift enables fast cloud data warehousing and SQL analytics across petabyte-scale datasets.",
    "etl pipelines": "ETL pipelines extract, transform, and load data reliably across corporate operational databases and warehouses.",
    "kotlin": "Kotlin is the modern, expressive programming language recommended for native Android application development.",
    "swift": "Swift is the fast, safe, and modern programming language for native iOS and Apple platform development.",
    "android sdk": "Android SDK provides the essential framework libraries and APIs for building native Android mobile apps.",
    "android studio": "Android Studio is the official integrated development environment (IDE) for Android application engineering.",
    "jetpack compose": "Jetpack Compose is Android's modern, declarative UI toolkit for crafting native user interfaces.",
    "swiftui": "SwiftUI is Apple's declarative UI framework for building user interfaces across iOS and macOS.",
    "uikit": "UIKit provides the core interface architecture and touch event handling for iOS applications.",
    "room": "Room persistence library provides an abstraction layer over SQLite for fluent database access on Android.",
    "core data": "Core Data is Apple's framework for managing object graphs and local data persistence in iOS apps.",
    "flutter": "Flutter enables building cross-platform natively compiled applications for mobile, web, and desktop from a single codebase.",
    "react native": "React Native allows writing cross-platform mobile apps using React and JavaScript/TypeScript.",
    "dbt": "dbt enables data analytics engineers to transform raw warehouse data using modular, testable SQL SELECT statements.",
    "xgboost": "XGBoost provides high-performance gradient boosting algorithms for tabular predictive modeling competitions and production AI.",
    "feature engineering": "Feature engineering transforms raw domain attributes into optimal mathematical features for machine learning models.",
    "model evaluation": "Model evaluation metrics (Accuracy, Precision, Recall, F1, ROC-AUC) rigorously validate machine learning performance.",
    "web security": "Learn XSS, CSRF, SQL injection, secure headers, secrets management and common web security practices.",
    "client-server architecture": "Client-server architecture separates user interface clients from server-side computational and data logic.",
    "mvc": "MVC design pattern separates application logic into Models, Views, and Controllers for maintainability.",
    "next.js": "Learn Next.js for full-stack React applications, routing, server-side rendering and modern web application architecture.",
    "graphql": "Understand GraphQL queries, mutations, schemas and API integration.",
    "postgresql": "Learn PostgreSQL database design, queries, indexing and production usage.",
    "mongodb": "Understand document databases and when MongoDB is appropriate for application development.",
    "redis": "Learn Redis for caching, sessions and high-performance data access.",
    "cloud computing": "Understand fundamental cloud concepts, deployment, networking and scalability.",
    "authorization": "Understand roles, permissions and access control.",
    "testing": "Learn unit, integration and end-to-end testing.",
    "jest": "Learn automated JavaScript/TypeScript unit testing.",
    "playwright": "Learn browser-based end-to-end testing.",
    "system design": "Learn how to design scalable, maintainable and reliable web applications.",
    "database design": "Learn relational modeling, normalization, indexing and query optimization.",
    "problem solving": "Improve structured technical problem solving.",
    "agile/scrum": "Understand sprint planning, standups, backlog management and iterative development.",
    "devtools": "Use browser developer tools for debugging, networking and performance analysis.",
    "browser devtools": "Use browser developer tools for debugging, networking and performance analysis.",
    "npm": "Understand JavaScript package management and dependency management.",
    "api integration": "Learn how frontend and backend systems communicate with external APIs.",
    "accessibility": "Learn accessible HTML, keyboard navigation, semantic markup and WCAG fundamentals.",
    "performance optimization": "Learn frontend/backend performance optimization, caching and efficient database/API usage.",
    "ai-assisted development": "Learn how to responsibly use AI coding assistants for development, debugging, testing and documentation.",
}


PREREQUISITES_GRAPH: Dict[str, List[str]] = {
    "react": ["javascript"],
    "next.js": ["react", "javascript"],
    "angular": ["typescript", "javascript"],
    "vue.js": ["javascript"],
    "svelte": ["javascript"],
    "fastapi": ["python"],
    "django": ["python"],
    "flask": ["python"],
    "spring boot": ["java"],
    "express.js": ["node.js", "javascript"],
    "pandas": ["python"],
    "numpy": ["python"],
    "scikit-learn": ["python", "numpy"],
    "xgboost": ["python", "scikit-learn"],
    "machine learning": ["statistics", "python"],
    "deep learning": ["machine learning", "python"],
    "pytorch": ["python"],
    "tensorflow": ["python"],
    "postgresql": ["sql"],
    "mysql": ["sql"],
    "sqlite": ["sql"],
    "docker": ["linux"],
    "kubernetes": ["docker"],
    "airflow": ["python"],
    "apache spark": ["python", "sql"],
    "pyspark": ["python", "apache spark"],
    "dbt": ["sql"],
    "jetpack compose": ["kotlin", "android sdk"],
    "room": ["kotlin", "sql"],
    "swiftui": ["swift"],
    "core data": ["swift"],
    "design systems": ["figma", "wireframing"],
    "usability testing": ["user research", "wireframing"],
    "power bi": ["data analysis"],
    "tableau": ["data analysis"],
}


JOB_ROLES_KNOWLEDGE_BASE: Dict[str, Dict[str, Any]] = {
    # =============================================================
    # 1. FRONTEND DEVELOPER
    # =============================================================
    "frontend_developer": {
        "role_id": "ROLE-FE-01",
        "role_name": "Frontend Developer",
        "category": "Web & Mobile Development",
        "icon": "🎨",
        "description": "Frontend Developers build the part of websites and applications that users interact with. They create responsive user interfaces, implement interactive behaviors, connect frontend applications with APIs, and ensure cross-browser compatibility.",
        "overview": (
            "Frontend Developers specialize in crafting the client-side user experience of web applications. "
            "They translate UI/UX design wireframes into clean, semantic, and responsive code. A modern Frontend Developer "
            "works with semantic HTML5, modern CSS3 (Flexbox, Grid), and JavaScript/TypeScript to build modular component-based "
            "applications. They connect client interfaces to backend REST/GraphQL APIs, manage application state, handle user input "
            "validation, and optimize rendering performance across desktop and mobile browsers."
        ),
        "work_activities": [
            "Reviewing UI/UX Figma wireframes and breaking designs into reusable modular components.",
            "Writing semantic HTML5 markup and responsive CSS3 styling using modern layout grids.",
            "Implementing client-side business logic and state management in JavaScript or React.",
            "Integrating backend REST APIs using asynchronous Fetch/Axios calls and handling loading/error states.",
            "Testing user interfaces across different web browsers, mobile viewports, and accessibility standards.",
            "Collaborating with backend engineers on API contracts and participating in Git pull request code reviews.",
        ],
        "responsibilities": [
            "Develop responsive, accessible, and high-performance web user interfaces.",
            "Build modular and reusable UI components using modern frontend libraries.",
            "Integrate RESTful API endpoints and manage asynchronous client-side data flows.",
            "Ensure cross-browser compatibility, responsive typography, and mobile-first layouts.",
            "Write client-side unit tests and debug rendering issues using browser DevTools.",
            "Participate in agile sprint ceremonies, daily standups, and Git version control workflows.",
        ],
        "tech_stack_groups": {
            "Core Languages": ["HTML5", "CSS3", "JavaScript"],
            "Frameworks & Libraries": ["React", "Vue.js", "Angular"],
            "Styling & UI": ["Tailwind CSS", "Bootstrap", "Sass / SCSS"],
            "Build & Package Tools": ["npm", "Vite", "Webpack"],
            "Version Control & APIs": ["Git", "GitHub", "REST API", "JSON"],
            "Testing & Quality": ["Jest", "Playwright", "Cypress", "Browser DevTools"],
        },
        "competency_matrix": [
            {
                "category": "Core Web Languages",
                "tier": "CORE",
                "skills": ["HTML5", "CSS3", "JavaScript"],
                "description": "Semantic HTML5 structure, modern CSS styling, and core JavaScript DOM manipulation."
            },
            {
                "category": "Frontend Frameworks",
                "tier": "REQUIRED",
                "is_alternative_group": True,
                "group_name": "Frontend Framework",
                "alternatives": ["React", "Angular", "Vue.js", "Next.js", "Svelte"],
                "description": "Component-based UI architecture in at least one modern frontend framework (React, Angular, Vue, or Svelte)."
            },
            {
                "category": "Responsive Design & Styling",
                "tier": "CORE",
                "skills": ["Responsive Design", "DOM Concepts"],
                "description": "Cross-device responsiveness, Flexbox/Grid layouts, and browser rendering lifecycle."
            },
            {
                "category": "APIs & Asynchronous Data",
                "tier": "REQUIRED",
                "skills": ["REST API", "JSON"],
                "description": "Consuming REST APIs asynchronously, handling HTTP payloads, loading states, and error responses."
            },
            {
                "category": "Version Control",
                "tier": "CORE",
                "skills": ["Git"],
                "description": "Git source control, commit hygiene, and repository management."
            },
            {
                "category": "Development Tools & DevTools",
                "tier": "REQUIRED",
                "skills": ["GitHub", "Browser DevTools", "VS Code", "npm"],
                "description": "Git branching, PR workflows, and inspecting runtime performance in browser DevTools."
            },
            {
                "category": "Testing & Build Tools",
                "tier": "PREFERRED",
                "skills": ["Software Testing", "TypeScript", "Tailwind CSS"],
                "description": "Client-side unit testing, typed JavaScript with TypeScript, and utility CSS frameworks."
            },
            {
                "category": "Advanced Frontend",
                "tier": "OPTIONAL",
                "skills": ["Design Systems", "Web Performance Optimization", "CI/CD"],
                "description": "Design token consistency, Core Web Vitals optimization, and automated CI/CD builds."
            }

        ],
        "alternative_skill_clusters": [
            {
                "cluster_name": "Frontend Framework",
                "options": ["React", "Angular", "Vue.js", "Next.js", "Svelte"],
                "importance": "Common",
                "description": "Component-based frontend framework (React, Angular, Vue, or Svelte)."
            }
        ],
        "skills_required": {
            "core": ["HTML5", "CSS3", "JavaScript", "DOM Concepts", "Responsive Design", "Git"],
            "required": ["REST API", "Browser DevTools", "JSON", "Frontend Framework"],
            "preferred": ["TypeScript", "Tailwind CSS", "Software Testing", "Redux", "Vite"],
            "optional": ["Design Systems", "Web Performance Optimization", "CI/CD", "Security Basics"],
            "essential": ["HTML5", "CSS3", "JavaScript", "DOM Concepts", "Responsive Design", "Git"],
            "common": ["REST API", "npm", "Browser DevTools", "JSON", "Accessibility"],
            "recommended": ["TypeScript", "Tailwind CSS", "Redux", "Software Testing", "Vite"],
            "advanced": ["Frontend Architecture", "Design Systems", "Web Performance Optimization", "CI/CD", "Security Basics"],
        },
        "backend_language_flexible": False,
        "education_relevance": "Degree in Computer Science, Information Technology, Software Engineering, or demonstrated frontend project portfolio.",
        "experience_expectations": {
            "fresher": "Strong command of HTML5/CSS3/JavaScript, DOM manipulation, responsive layouts, Git, and at least 2-3 interactive web projects.",
            "junior": "1-2 years experience with React or another component framework, API integrations, and collaborative Git branching.",
            "mid": "3-5 years experience including state management architectures, frontend performance tuning, and automated testing suites.",
            "senior": "5+ years experience designing enterprise design systems, frontend architecture, micro-frontends, and mentoring junior engineers.",
        },
        "competency_expectations": [
            "Translate UI mockups into pixel-perfect, responsive web pages without layout breaks.",
            "Manipulate the DOM dynamically using vanilla JavaScript and modern framework hooks.",
            "Fetch data from REST APIs, serialize JSON payloads, and handle edge-case error states.",
            "Manage code versions, create feature branches, and submit clean pull requests on GitHub.",
            "Debug client-side JavaScript execution, inspect network requests, and profile rendering in DevTools.",
        ],
        "interview_preparation": {
            "core_technical_areas": [
                "Semantic HTML5 tags and accessibility (ARIA roles).",
                "CSS box model, specificity, Flexbox, and CSS Grid layout algorithms.",
                "JavaScript closures, scope, prototypal inheritance, and event loop execution.",
                "Asynchronous programming: Promises, async/await, and Fetch API.",
                "React lifecycle, hooks (useState, useEffect, useMemo), and component re-rendering.",
            ],
            "coding_topics": [
                "Array transformations (map, filter, reduce), object destructuring, and string parsing.",
                "DOM manipulation tasks (dynamic list creation, modal dialog toggling, event delegation).",
                "Building an interactive search bar with client-side filtering and debouncing.",
            ],
            "practical_tasks": [
                "Build a responsive multi-card product grid from a mockup.",
                "Consume a public REST API (e.g. GitHub Users, Weather API) and display data with pagination.",
                "Implement form validation with error messaging on submission.",
            ],
        },
        "not_required_yet": [
            "Advanced Kubernetes cluster configuration.",
            "Complex microservices backend architectures.",
            "Distributed database sharding and low-level kernel tuning.",
            "Enterprise cloud infrastructure management (Terraform/AWS CloudFormation).",
        ],
        "career_progression": {
            "Junior Frontend Developer": "Builds UI components, fixes client-side bugs, and integrates REST APIs under senior guidance.",
            "Mid-Level Frontend Developer": "Designs component hierarchies, owns major feature modules, and implements state management.",
            "Senior Frontend Developer": "Architects frontend applications, establishes code standards, optimizes performance, and mentors team members.",
            "Frontend Lead / Principal": "Defines enterprise design system strategy, evaluates technical stacks, and drives multi-team frontend architecture.",
        },
        "learning_roadmap_phases": [
            {
                "phase": "Phase 1 — Core Web Foundation",
                "focus": "Semantic HTML5, modern CSS3 layouts (Flexbox, CSS Grid), responsive design principles, and Git version control basics.",
            },
            {
                "phase": "Phase 2 — JavaScript Fundamentals",
                "focus": "Data types, ES6+ features, functions, DOM manipulation, browser events, Promises, async/await, and Fetch API.",
            },
            {
                "phase": "Phase 3 — Component-Based UI Framework",
                "focus": "React core fundamentals: JSX, component architecture, props vs. state, hooks (useState, useEffect), and client routing.",
            },
            {
                "phase": "Phase 4 — Professional Engineering Practices",
                "focus": "REST API integration, form handling, error boundaries, browser DevTools debugging, and basic unit testing with Jest.",
            },
            {
                "phase": "Phase 5 — Portfolio & Deployment",
                "focus": "Build and deploy 2–3 complete interactive web applications on platforms like Vercel, Netlify, or GitHub Pages.",
            },
        ],
        "targeted_project_blueprints": [
            {
                "tier": "Beginner Project",
                "name": "Responsive Portfolio & Interactive Task Board",
                "skills": ["HTML5", "CSS3", "JavaScript", "DOM Concepts", "Git"],
                "description": "Build a responsive personal website with an interactive Kanban task board utilizing local storage persistence.",
            },
            {
                "tier": "Intermediate Project",
                "name": "Live API-Driven Analytics Dashboard",
                "skills": ["JavaScript", "REST API", "JSON", "Fetch API", "Responsive Design"],
                "description": "Create a dynamic dashboard that consumes public REST APIs, visualizes data cards, and supports live search filtering.",
            },
            {
                "tier": "Job-Ready Project",
                "name": "E-Commerce Web Application with Cart & Auth",
                "skills": ["React", "JavaScript", "REST API", "State Management", "Git"],
                "description": "Develop a component-driven React application with dynamic routing, product filtering, shopping cart state, and mock checkout.",
            },
        ],
        "project_relevance_keywords": ["frontend", "web", "html", "css", "javascript", "react", "ui", "interface", "portfolio", "spa"],
    },

    # =============================================================
    # 2. BACKEND DEVELOPER
    # =============================================================
    "backend_developer": {
        "role_id": "ROLE-BE-02",
        "role_name": "Backend Developer",
        "category": "Software Engineering & Backend",
        "icon": "💻",
        "description": "Backend Developers architect and build server-side logic, database interactions, authentication mechanisms, and API endpoints that power web and mobile applications.",
        "overview": (
            "Backend Developers engineer the server-side infrastructure that powers software applications. "
            "They write core business logic in backend languages like Python, Java, or Node.js, design and query relational "
            "databases using SQL, and build secure RESTful or GraphQL APIs. Backend engineers manage data serialization, "
            "user authentication (JWT, OAuth), session state, server-side caching (Redis), error handling, and cloud deployments."
        ),
        "work_activities": [
            "Designing RESTful API endpoints and defining JSON data contracts for client applications.",
            "Writing database schema migrations, optimizing SQL queries, and configuring table indexing.",
            "Implementing user authentication, role-based access control, and cryptographic password hashing.",
            "Writing unit and integration test suites to ensure robust server-side transaction handling.",
            "Configuring server logging, monitoring latency, and profiling slow database queries.",
            "Deploying services using containerization (Docker) and collaborating on backend architecture.",
        ],
        "responsibilities": [
            "Design and build scalable server-side REST APIs and microservice endpoints.",
            "Design relational database schemas, write SQL queries, and manage transactional integrity.",
            "Implement secure authentication, authorization, and data encryption protocols.",
            "Manage server-side error logging, input validation, and rate limiting.",
            "Write comprehensive automated unit and integration tests for backend services.",
            "Deploy containerized services to cloud environments and monitor health metrics.",
        ],
        "tech_stack_groups": {
            "Backend Languages": ["Python", "Java", "JavaScript", "C#", "Go"],
            "Frameworks": ["FastAPI", "Django", "Spring Boot", "Express.js", "Flask"],
            "Databases": ["PostgreSQL", "MySQL", "SQLite", "MongoDB", "Redis"],
            "APIs & Auth": ["REST API", "JSON", "JWT", "OAuth2", "GraphQL"],
            "DevOps & Tools": ["Git", "Docker", "Linux", "Postman"],
            "Testing": ["pytest", "JUnit", "Supertest"],
        },
        "competency_matrix": [
            {
                "category": "Backend Language & Ecosystem",
                "tier": "CORE",
                "is_alternative_group": True,
                "group_name": "Backend Language",
                "alternatives": ["Python", "Java", "Node.js", "C#", "Go", "PHP"],
                "description": "Proficiency in at least one modern server-side programming language (Python, Java, Node.js, C#, or Go)."
            },
            {
                "category": "Backend Frameworks",
                "tier": "REQUIRED",
                "is_alternative_group": True,
                "group_name": "Backend Framework",
                "alternatives": ["FastAPI", "Django", "Flask", "Spring Boot", "Express.js", "ASP.NET", "NestJS", "Laravel", "Gin"],
                "description": "Server-side web framework for routing, middleware, and request lifecycle handling."
            },
            {
                "category": "API Architecture & Security",
                "tier": "CORE",
                "skills": ["REST API", "Authentication", "JSON"],
                "description": "HTTP methods, status codes, payload serialization, JWT token generation, and secure password hashing."
            },
            {
                "category": "Relational Databases & SQL",
                "tier": "CORE",
                "skills": ["SQL", "Database Management"],
                "description": "Relational schema design, normalization, joins, aggregations, transactional ACID properties, and indexes."
            },
            {
                "category": "Testing & Debugging",
                "tier": "REQUIRED",
                "skills": ["Software Testing", "Debugging", "Postman"],
                "description": "Automated unit/integration testing, inspecting stack traces, and testing routes via Postman."
            },
            {
                "category": "DevOps & Containerization",
                "tier": "PREFERRED",
                "skills": ["Git", "Docker", "Linux"],
                "description": "Version control branching, Docker containerization, and basic Linux server administration."
            },
            {
                "category": "Advanced Systems & Cloud",
                "tier": "OPTIONAL",
                "skills": ["PostgreSQL", "Redis", "CI/CD", "AWS"],
                "description": "Enterprise database instances, in-memory caching layers (Redis), CI/CD pipelines, and cloud hosting."
            }
        ],
        "alternative_skill_clusters": [
            {
                "cluster_name": "Backend Framework",
                "options": ["FastAPI", "Django", "Flask", "Spring Boot", "Express.js", "ASP.NET", "NestJS", "Laravel", "Gin"],
                "importance": "Common",
                "description": "Server-side web framework (FastAPI, Django, Spring Boot, or Express.js)."
            }
        ],
        "skills_required": {
            "core": ["SQL", "REST API", "Database Management", "Authentication", "Git", "Software Testing"],
            "required": ["JSON", "Postman", "Debugging", "Backend Framework"],
            "preferred": ["Docker", "PostgreSQL", "Redis", "Linux", "Object-Oriented Programming"],
            "optional": ["Microservices Architecture", "System Design", "Message Queues (RabbitMQ/Kafka)", "CI/CD", "AWS"],
            "essential": ["SQL", "REST API", "Database Management", "Authentication", "Git", "Software Testing"],
            "common": ["JSON", "Postman", "Debugging"],
            "recommended": ["Docker", "PostgreSQL", "Redis", "Linux", "Object-Oriented Programming"],
            "advanced": ["Microservices Architecture", "System Design", "Message Queues (RabbitMQ/Kafka)", "CI/CD", "AWS"],
        },
        "backend_language_flexible": True,
        "education_relevance": "B.Sc / B.Tech / B.E / BCA in Computer Science, IT, or related technical discipline.",
        "experience_expectations": {
            "fresher": "Solid proficiency in at least one backend language (Python/Java), relational SQL queries, REST API construction, and Git.",
            "junior": "1-2 years experience building production APIs, database migrations, and implementing secure user authentication.",
            "mid": "3-5 years experience designing scalable database schemas, caching layers (Redis), and containerized microservices.",
            "senior": "5+ years experience in distributed systems, database sharding, asynchronous event queues, and architectural oversight.",
        },
        "competency_expectations": [
            "Build complete CRUD REST APIs handling HTTP status codes, headers, and JSON responses.",
            "Design normalized relational database schemas with primary/foreign keys and indexes.",
            "Implement secure user signup/login workflows using bcrypt hashing and JWT tokens.",
            "Write automated backend test suites to verify business logic and edge cases.",
            "Containerize backend applications using Dockerfiles and test API routes with Postman.",
        ],
        "interview_preparation": {
            "core_technical_areas": [
                "HTTP protocol fundamentals: methods (GET, POST, PUT, DELETE), status codes, headers.",
                "Relational SQL operations: INNER/LEFT JOINs, GROUP BY, aggregations, transactions (ACID).",
                "RESTful design principles and idempotent API operations.",
                "Authentication strategies: Session cookies vs. Stateless JWT token flows.",
                "Database indexing: B-trees, primary vs. secondary indexes, and query explain plans.",
            ],
            "coding_topics": [
                "Designing a database schema for an e-commerce or user management platform.",
                "Writing complex SQL queries with multiple table joins and conditional filtering.",
                "Implementing a rate limiter or token validation middleware function in code.",
            ],
            "practical_tasks": [
                "Build a complete CRUD API in Python/Java with SQLite/PostgreSQL persistence.",
                "Implement JWT authentication middleware protecting restricted endpoints.",
                "Write automated unit tests using pytest or JUnit verifying API responses.",
            ],
        },
        "not_required_yet": [
            "Distributed consensus protocols (Raft/Paxos).",
            "Multi-region cloud failover architecture.",
            "High-frequency algorithmic trading systems.",
            "Large-scale Kubernetes cluster auto-scaler tuning.",
        ],
        "career_progression": {
            "Junior Backend Developer": "Builds and tests API endpoints, writes database migrations, and assists with bug fixes.",
            "Mid-Level Backend Developer": "Designs database models, owns service microservices, implements caching, and optimizes queries.",
            "Senior Backend Developer": "Architects distributed services, defines security guidelines, handles scaling bottlenecks, and reviews team code.",
            "Backend Lead / Architect": "Establishes enterprise backend strategy, oversees database infrastructure, and guides technical roadmap.",
        },
        "learning_roadmap_phases": [
            {
                "phase": "Phase 1 — Programming & CS Foundations",
                "focus": "Master core backend language (Python or Java), OOP principles, data structures, and Git version control.",
            },
            {
                "phase": "Phase 2 — Relational Databases & SQL",
                "focus": "Schema design, table normalization, primary/foreign keys, CRUD operations, joins, and SQL query optimization.",
            },
            {
                "phase": "Phase 3 — Web API Frameworks",
                "focus": "Build RESTful APIs with FastAPI/Django/Spring Boot: request validation, JSON serialization, and routing.",
            },
            {
                "phase": "Phase 4 — Security & Production Engineering",
                "focus": "JWT authentication, password hashing, environment variables, automated unit testing with pytest/JUnit, and Docker containerization.",
            },
            {
                "phase": "Phase 5 — Deployment & Cloud",
                "focus": "Deploy services to cloud environments (e.g. Render, Railway, AWS EC2) and connect production PostgreSQL databases.",
            },
        ],
        "targeted_project_blueprints": [
            {
                "tier": "Beginner Project",
                "name": "CRUD REST API with SQLite Persistence",
                "skills": ["Python", "FastAPI", "SQL", "Git"],
                "description": "Create a structured backend API for student or inventory management with full CRUD operations and structured JSON responses.",
            },
            {
                "tier": "Intermediate Project",
                "name": "Secure Auth & User Management Service",
                "skills": ["Python / Java", "REST API", "Authentication", "SQL", "Software Testing"],
                "description": "Build an authentication service featuring user registration, bcrypt password hashing, JWT token validation, and protected routes.",
            },
            {
                "tier": "Job-Ready Project",
                "name": "Scalable E-Commerce Backend Service",
                "skills": ["FastAPI / Django", "PostgreSQL", "Docker", "REST API", "Software Testing"],
                "description": "Engineer a production-grade backend with PostgreSQL integration, product catalogs, order processing, and Docker containerization.",
            },
        ],
        "project_relevance_keywords": ["backend", "api", "database", "server", "crud", "django", "flask", "fastapi", "spring", "sql", "postgres"],
    },

    # =============================================================
    # 3. FULL STACK DEVELOPER
    # =============================================================
    "full_stack_developer": {
        "role_id": "ROLE-FS-03",
        "role_name": "Full Stack Developer",
        "category": "Full Stack Engineering",
        "icon": "🌐",
        "description": "Full Stack Developers work across both frontend and backend development. They build responsive client user interfaces, backend API services, manage database storage, and deploy complete end-to-end applications.",
        "overview": (
            "Full Stack Developers bridge client-side user interfaces with server-side infrastructure. "
            "They understand the complete lifecycle of a web request—from a button click in a React/HTML interface, through HTTP network "
            "layers and API gateways, to server business logic, relational SQL database transactions, and cloud deployments. "
            "A qualified Full Stack Developer writes semantic frontend markup, builds backend REST endpoints, and manages full application integration."
        ),
        "work_activities": [
            "Building responsive frontend components and connecting them to server-side API endpoints.",
            "Designing backend application logic, database schemas, and data access models.",
            "Managing user authentication, session security, and state synchronization across client and server.",
            "Testing end-to-end workflows from user input down to persistent database storage.",
            "Deploying full-stack web applications to cloud servers and managing environment variables.",
            "Collaborating across the entire technology stack to deliver complete product features.",
        ],
        "responsibilities": [
            "Develop end-to-end web features across client, server, and database layers.",
            "Build responsive frontend interfaces using modern HTML5, CSS3, and JavaScript.",
            "Create scalable backend RESTful APIs and handle server-side data processing.",
            "Design and query relational SQL databases for persistent data storage.",
            "Implement secure authentication, session management, and authorization flows.",
            "Deploy and maintain full-stack applications on cloud hosting platforms.",
        ],
        "tech_stack_groups": {
            "Frontend": ["HTML5", "CSS3", "JavaScript", "React"],
            "Backend": ["Python", "Node.js", "Java", "FastAPI", "Django", "Express.js"],
            "Databases": ["PostgreSQL", "MySQL", "SQLite", "MongoDB"],
            "APIs & Networking": ["REST API", "JSON", "HTTP", "JWT"],
            "DevOps & Tools": ["Git", "GitHub", "Docker", "npm"],
        },
        "competency_matrix": [
            {
                "category": "Frontend Fundamentals",
                "tier": "CORE",
                "skills": ["HTML5", "CSS3", "JavaScript", "Responsive Design"],
                "description": "Semantic markup, styling, layout responsive design, and core client-side scripting."
            },
            {
                "category": "Frontend Frameworks",
                "tier": "REQUIRED",
                "is_alternative_group": True,
                "group_name": "Frontend Framework",
                "alternatives": ["React", "Angular", "Vue.js", "Svelte", "Next.js"],
                "description": "Component-based UI architecture in at least one modern frontend framework (React, Angular, Vue, or Svelte)."
            },
            {
                "category": "Backend Languages & Ecosystems",
                "tier": "CORE",
                "is_alternative_group": True,
                "group_name": "Backend Language",
                "alternatives": ["Node.js", "Python", "Java", "C#", "Go", "PHP"],
                "description": "Server-side language execution and application lifecycle management."
            },
            {
                "category": "Backend Frameworks",
                "tier": "REQUIRED",
                "is_alternative_group": True,
                "group_name": "Backend Framework",
                "alternatives": ["Express.js", "FastAPI", "Django", "Spring Boot", "ASP.NET Core", "Flask", "NestJS", "Laravel", "Gin"],
                "description": "Server-side web framework for routing, middleware, and request handling."
            },
            {
                "category": "API Architecture & Authentication",
                "tier": "CORE",
                "skills": ["REST API", "Authentication", "JSON"],
                "description": "HTTP methods, status codes, JSON payloads, and token-based JWT/OAuth authentication."
            },
            {
                "category": "Databases & Storage",
                "tier": "CORE",
                "skills": ["SQL", "Database Management"],
                "description": "Relational schema design, normalization, indexes, and transactional queries."
            },
            {
                "category": "DevOps & Containerization",
                "tier": "PREFERRED",
                "skills": ["Git", "Docker", "CI/CD"],
                "description": "Version control, Docker containers, and CI/CD automated build pipelines."
            },
            {
                "category": "Cloud Platforms",
                "tier": "PREFERRED",
                "is_alternative_group": True,
                "group_name": "Cloud Platform",
                "alternatives": ["AWS", "Azure", "GCP"],
                "description": "Cloud hosting, compute, or managed cloud services."
            },
            {
                "category": "Security & Architecture",
                "tier": "REQUIRED",
                "skills": ["Web Security", "Client-Server Architecture"],
                "description": "Mitigating CORS, XSS, and SQL Injection; designing multi-tier client-server architectures."
            },
            {
                "category": "Testing & Engineering",
                "tier": "REQUIRED",
                "skills": ["Software Testing", "Debugging", "Data Structures & Algorithms"],
                "description": "Automated unit/integration testing, runtime debugging, and fundamental DSA."
            }
        ],
        "alternative_skill_clusters": [
            {
                "cluster_name": "Frontend Framework",
                "options": ["React", "Angular", "Vue.js", "Next.js", "Svelte"],
                "importance": "Essential",
                "description": "Modern frontend component library or framework (React, Angular, Vue, Next.js)."
            },
            {
                "cluster_name": "Backend Language & Ecosystem",
                "options": ["Node.js", "Express.js", "Python", "FastAPI", "Django", "Java", "Spring Boot", "C#", ".NET", "Go"],
                "importance": "Essential",
                "description": "Server-side language and framework (Node.js, Python, Java, C#, or Go)."
            },
            {
                "cluster_name": "Cloud Platform",
                "options": ["AWS", "Azure", "GCP"],
                "importance": "Recommended",
                "description": "Cloud infrastructure and hosting platform."
            }
        ],
        "skills_required": {
            "core": ["HTML5", "CSS3", "JavaScript", "SQL", "REST API", "Git", "Authentication"],
            "required": ["Frontend Framework", "Backend Framework", "Database Management", "Software Testing", "Debugging", "Web Security", "Client-Server Architecture", "Data Structures & Algorithms"],
            "preferred": ["TypeScript", "Docker", "CI/CD", "PostgreSQL", "Cloud Platform"],
            "optional": ["Microservices Architecture", "System Design", "Kubernetes", "Kafka"],
            "essential": ["HTML5", "CSS3", "JavaScript", "SQL", "REST API", "Git", "Authentication"],
            "common": ["Responsive Design", "Database Management"],
            "recommended": ["TypeScript", "Docker", "PostgreSQL", "Software Testing", "Tailwind CSS"],
            "advanced": ["Full-Stack Architecture", "CI/CD", "Cloud Infrastructure (AWS/GCP)", "System Design"],
        },
        "backend_language_flexible": True,
        "education_relevance": "Degree in Computer Science, Software Engineering, Information Technology, or verified full-stack project portfolio.",
        "experience_expectations": {
            "fresher": "Demonstrated full-stack project evidence connecting a responsive frontend (HTML/CSS/JS) to a backend API (Python/Java/Node) and database.",
            "junior": "1-2 years experience delivering integrated web features, managing database state, and handling user authentication.",
            "mid": "3-5 years experience optimizing full-stack application performance, managing API contracts, and automated testing.",
            "senior": "5+ years experience architecting multi-tier cloud applications, leading cross-functional delivery, and mentoring engineers.",
        },
        "competency_expectations": [
            "Build an end-to-end web application from database schema to interactive frontend UI.",
            "Establish seamless communication between client-side Fetch calls and backend API routes.",
            "Implement user login, token-based session persistence, and role-based UI rendering.",
            "Deploy both frontend client bundles and backend web services to cloud platforms.",
        ],
        "interview_preparation": {
            "core_technical_areas": [
                "End-to-end web architecture: Client $\\rightarrow$ HTTP Request $\\rightarrow$ API Controller $\\rightarrow$ Database $\\rightarrow$ Response.",
                "CORS (Cross-Origin Resource Sharing) mechanisms and header configuration.",
                "State management between client memory and server persistent database.",
                "Relational SQL schema design vs. document NoSQL trade-offs.",
                "JWT authentication: token generation, validation, and client-side storage.",
            ],
            "coding_topics": [
                "Building a full-stack CRUD application in a single pairing session.",
                "Connecting a frontend form submission to a database write and returning updated JSON.",
            ],
            "practical_tasks": [
                "Build a complete web application (e.g. Note-taking app, Job board, or Blog platform).",
                "Deploy the application with a hosted frontend and a connected cloud database.",
            ],
        },
        "not_required_yet": [
            "Multi-region distributed database replication clusters.",
            "Advanced service mesh configurations (Istio).",
            "Custom hardware driver development.",
        ],
        "career_progression": {
            "Junior Full Stack Developer": "Implements features across frontend and backend under technical supervision.",
            "Mid-Level Full Stack Developer": "Independently builds and deploys end-to-end features, manages database migrations, and designs APIs.",
            "Senior Full Stack Developer": "Architects full-stack solutions, establishes coding standards across the stack, and optimizes system bottlenecks.",
            "Principal / Tech Lead": "Guides high-level system architecture, evaluates new technologies, and aligns engineering with product vision.",
        },
        "learning_roadmap_phases": [
            {
                "phase": "Phase 1 — Frontend Foundations",
                "focus": "HTML5 semantic structure, modern responsive CSS3, and core JavaScript fundamentals (DOM, events, ES6+).",
            },
            {
                "phase": "Phase 2 — Backend & Database Foundations",
                "focus": "Backend programming (Python or Node.js), relational database design with SQL, and CRUD queries.",
            },
            {
                "phase": "Phase 3 — API Integration & Authentication",
                "focus": "Build RESTful APIs, handle JSON payloads, and implement JWT-based user authentication.",
            },
            {
                "phase": "Phase 4 — Frontend Framework Integration",
                "focus": "Connect a component-based frontend (React) to your backend API, managing asynchronous state.",
            },
            {
                "phase": "Phase 5 — Full Stack Deployment",
                "focus": "Deploy complete full-stack web applications with cloud database hosting and version control on GitHub.",
            },
        ],
        "targeted_project_blueprints": [
            {
                "tier": "Beginner Project",
                "name": "Personal Blog & Content Management Platform",
                "skills": ["HTML5", "CSS3", "JavaScript", "Python / FastAPI", "SQLite"],
                "description": "Build an integrated web app where users can create, edit, and delete articles with persistent database storage.",
            },
            {
                "tier": "Intermediate Project",
                "name": "User Auth & Project Collaboration Board",
                "skills": ["React", "FastAPI / Node.js", "SQL", "Authentication", "Git"],
                "description": "Develop a Kanban task management app with JWT login, personal user dashboards, and real-time task updates.",
            },
            {
                "tier": "Job-Ready Project",
                "name": "Full-Featured E-Commerce / Recruitment Platform",
                "skills": ["React", "Python / Node.js", "PostgreSQL", "Docker", "REST API", "Git"],
                "description": "Build a production-grade full-stack platform with user profiles, search filtering, database transactions, and cloud deployment.",
            },
        ],
        "project_relevance_keywords": ["fullstack", "full stack", "web application", "webapp", "portal", "e-commerce", "end-to-end"],
    },

    # =============================================================
    # 4. SOFTWARE ENGINEER
    # =============================================================
    "software_engineer": {
        "role_id": "ROLE-SE-04",
        "role_name": "Software Engineer",
        "category": "Software Engineering & Backend",
        "icon": "⚙️",
        "description": "Software Engineers design, develop, test, maintain, and improve software applications. They work with programming languages, algorithms, data structures, databases, APIs, and software development lifecycles (SDLC).",
        "overview": (
            "Software Engineers apply computer science principles, algorithmic problem-solving, and disciplined engineering practices "
            "to create reliable, high-performance software systems. They write modular code using Object-Oriented and functional paradigms, "
            "implement efficient data structures and algorithms, design database interactions with SQL, develop APIs, and write comprehensive "
            "automated test suites. Entry-level software engineers focus on algorithmic correctness, clean code structure, and Git collaboration."
        ),
        "work_activities": [
            "Analyzing functional requirements and designing clean, modular software components.",
            "Writing high-quality, testable code in a modern programming language (Python, Java, C++, or C#).",
            "Applying optimal data structures and algorithms to solve computational efficiency bottlenecks.",
            "Writing unit and integration tests to ensure software reliability and prevent regressions.",
            "Participating in peer code reviews, debugging stack traces, and maintaining documentation.",
            "Collaborating in agile software development lifecycles (SDLC) using Git version control.",
        ],
        "responsibilities": [
            "Design, implement, and maintain high-quality software features and modules.",
            "Apply data structures and algorithms to solve engineering problems efficiently.",
            "Write automated unit, integration, and regression test suites.",
            "Participate actively in code reviews, technical discussions, and sprint planning.",
            "Debug complex runtime issues, analyze performance, and refactor legacy code.",
            "Follow clean code principles, version control workflows, and documentation standards.",
        ],
        "tech_stack_groups": {
            "Programming Languages": ["Python", "Java", "C++", "C#", "C", "Go"],
            "Core CS Fundamentals": ["Data Structures & Algorithms", "Object-Oriented Programming", "Operating Systems", "Networking"],
            "Databases & APIs": ["SQL", "Database Management", "REST API", "JSON"],
            "Engineering & DevOps": ["Git", "GitHub", "Docker", "Linux", "CI/CD"],
            "Testing & Quality": ["Software Testing", "Unit Testing", "Debugging", "pytest", "JUnit"],
        },
        "competency_matrix": [
            {
                "category": "Core Programming Language",
                "tier": "CORE",
                "is_alternative_group": True,
                "group_name": "Programming Language",
                "alternatives": ["Python", "Java", "C++", "C#", "C", "Go"],
                "description": "At least one fundamental compiled or interpreted programming language."
            },
            {
                "category": "DSA & Computer Science Fundamentals",
                "tier": "CORE",
                "skills": ["Data Structures & Algorithms", "Object-Oriented Programming"],
                "description": "Fundamental data structures, search/sort algorithms, algorithmic complexity (Big-O), and SOLID OOP design."
            },
            {
                "category": "Version Control & Engineering Workflow",
                "tier": "CORE",
                "skills": ["Git", "Debugging"],
                "description": "Git version control, PR workflows, and systematic runtime debugging."
            },
            {
                "category": "Databases & APIs",
                "tier": "REQUIRED",
                "skills": ["SQL", "REST API", "Database Management"],
                "description": "Relational querying, CRUD operations, database schema design, and consuming/building REST APIs."
            },
            {
                "category": "Testing & Software Quality",
                "tier": "CORE",
                "skills": ["Software Testing"],
                "description": "Automated unit testing, test-driven logic, integration test suites, and regression prevention."
            },
            {
                "category": "DevOps, Containers & Linux",
                "tier": "PREFERRED",
                "skills": ["Linux", "Docker", "CI/CD"],
                "description": "Linux shell administration, container packaging with Docker, and CI/CD automation."
            },
            {
                "category": "System Design & Architecture",
                "tier": "OPTIONAL",
                "skills": ["Microservices Architecture", "Cloud Infrastructure (AWS/GCP)"],
                "description": "Scalable system design, modular architectures, microservices, and cloud hosting."
            }
        ],
        "alternative_skill_clusters": [
            {
                "cluster_name": "Primary Programming Language",
                "options": ["Python", "Java", "C++", "C#", "C", "Go"],
                "importance": "Essential",
                "description": "At least one core general-purpose programming language (Python, Java, C++, C#, or Go)."
            }
        ],
        "skills_required": {
            "core": ["Object-Oriented Programming", "Data Structures & Algorithms", "Git", "Debugging", "Software Testing", "Primary Programming Language"],
            "required": ["SQL", "REST API", "Database Management"],
            "preferred": ["Linux", "Docker", "CI/CD", "Design Patterns"],
            "optional": ["Microservices Architecture", "System Design", "Cloud Infrastructure (AWS/GCP)", "Distributed Systems"],
            "essential": ["Object-Oriented Programming", "Data Structures & Algorithms", "Git", "Debugging", "Software Testing", "SQL", "REST API"],
            "common": ["Database Management", "Linux", "JSON", "Unit Testing", "Clean Code"],
            "recommended": ["Docker", "CI/CD", "Design Patterns", "System Design", "Agile / Scrum"],
            "advanced": ["Distributed Systems", "Concurrency & Multithreading", "Scalability", "Cloud Architecture (AWS)"],
        },
        "backend_language_flexible": True,
        "education_relevance": "B.Sc / B.Tech / B.E / MCA in Computer Science, Software Engineering, or related technical field.",
        "experience_expectations": {
            "fresher": "Strong command of core programming (Python/Java/C++), OOP, fundamental data structures (arrays, lists, trees, hash tables), basic SQL, and Git.",
            "junior": "1-2 years experience contributing to professional codebases, automated test suites, and collaborative sprint cycles.",
            "mid": "3-5 years experience leading feature design, refactoring architectures, optimizing performance, and mentoring junior engineers.",
            "senior": "5+ years experience driving system architecture, technical roadmaps, cross-team engineering standards, and high-scale reliability.",
        },
        "competency_expectations": [
            "Write clean, modular, and maintainable code adhering to SOLID object-oriented design principles.",
            "Select and implement optimal data structures (hash maps, trees, queues) based on algorithmic time/space complexity.",
            "Write comprehensive automated unit tests covering edge cases and error handling paths.",
            "Use Git for branching, rebasing, resolving merge conflicts, and conducting code reviews.",
        ],
        "interview_preparation": {
            "core_technical_areas": [
                "Time and space complexity analysis (Big-O notation).",
                "Object-Oriented Programming: Inheritance, Polymorphism, Encapsulation, Abstraction.",
                "Data structures: Arrays, Linked Lists, Stacks, Queues, Hash Tables, Binary Trees, Graphs.",
                "Core algorithms: Binary Search, Sorting (Merge/Quick Sort), Recursion, BFS/DFS tree traversal.",
                "Database fundamentals: SQL queries, indexing, and ACID transaction properties.",
            ],
            "coding_topics": [
                "Algorithmic problem solving: Two-pointer technique, sliding window, and hash map lookups.",
                "String manipulation, array reversals, and frequency counters.",
                "Tree traversal algorithms (inorder, preorder, postorder, level-order).",
            ],
            "practical_tasks": [
                "Implement a custom data structure (e.g. LRU Cache, Custom Queue, or Binary Search Tree).",
                "Write a complete modular class library with comprehensive unit tests in Python or Java.",
            ],
        },
        "not_required_yet": [
            "High-scale distributed consensus algorithms (Paxos/Raft).",
            "Multi-datacenter global database failover architecture.",
            "Enterprise executive management and budgeting.",
        ],
        "career_progression": {
            "Associate / Junior Software Engineer": "Writes tested modular code, fixes bugs, and delivers assigned feature tickets under senior review.",
            "Software Engineer (Mid-Level)": "Designs and implements complex features independently, participates in architectural design, and mentors juniors.",
            "Senior Software Engineer": "Owns major subsystems, leads architectural decisions, ensures code quality across teams, and drives technical excellence.",
            "Staff / Principal Engineer": "Sets technical strategy across the engineering organization, solves complex scaling challenges, and drives long-term innovation.",
        },
        "learning_roadmap_phases": [
            {
                "phase": "Phase 1 — Programming & OOP Mastery",
                "focus": "Deepen mastery in Python, Java, or C++, focusing on object-oriented design, modularity, and clean code practices.",
            },
            {
                "phase": "Phase 2 — Data Structures & Algorithms",
                "focus": "Arrays, strings, hash maps, linked lists, stacks, queues, trees, searching, sorting, and Big-O computational complexity.",
            },
            {
                "phase": "Phase 3 — Databases & API Engineering",
                "focus": "Relational SQL querying, database normalization, schema design, and RESTful API development.",
            },
            {
                "phase": "Phase 4 — Software Testing & DevOps",
                "focus": "Automated unit testing (pytest/JUnit), debugging workflows, Git collaboration, and basic Docker containerization.",
            },
            {
                "phase": "Phase 5 — Engineering Portfolio",
                "focus": "Build 2–3 structured software projects demonstrating clean architecture, algorithm optimization, and automated testing.",
            },
        ],
        "targeted_project_blueprints": [
            {
                "tier": "Beginner Project",
                "name": "Algorithmic File Organizer & Text Analyzer",
                "skills": ["Python / Java", "Data Structures & Algorithms", "Object-Oriented Programming", "Git"],
                "description": "Build an algorithmic command-line tool that parses, indexes, and searches large text datasets using efficient data structures.",
            },
            {
                "tier": "Intermediate Project",
                "name": "Database-Backed Inventory & Transaction Engine",
                "skills": ["Python / Java", "SQL", "Database Management", "Software Testing", "REST API"],
                "description": "Design an object-oriented business transaction platform with SQL persistence, automated unit testing, and structured logging.",
            },
            {
                "tier": "Job-Ready Project",
                "name": "Distributed Task Queue & Microservice API",
                "skills": ["Python / Java", "REST API", "Docker", "SQL", "Software Testing", "Git"],
                "description": "Build a modular software application featuring API endpoints, relational database persistence, automated test suites, and Docker containerization.",
            },
        ],
        "project_relevance_keywords": ["software", "system", "application", "platform", "algorithm", "tool", "development", "oop", "dsa"],
    },

    # =============================================================
    # 5. PYTHON DEVELOPER
    # =============================================================
    "python_developer": {
        "role_id": "ROLE-PY-05",
        "role_name": "Python Developer",
        "category": "Software Engineering & Backend",
        "icon": "🐍",
        "description": "Python Developers use Python to build backend web applications, automation tools, data integration pipelines, and RESTful APIs. They write clean, maintainable code following object-oriented and functional paradigms.",
        "overview": (
            "Python Developers leverage Python's rich ecosystem to build backend web applications, automation scripts, "
            "data transformation pipelines, and high-performance REST APIs. They work with modern frameworks like FastAPI, Django, "
            "and Flask, connect applications to relational SQL and NoSQL databases, write automated tests using pytest, and integrate "
            "third-party APIs. Python developers write idiomatic 'Pythonic' code that is clean, readable, and highly maintainable."
        ),
        "work_activities": [
            "Developing asynchronous REST APIs and backend web services using FastAPI or Django.",
            "Writing relational database queries with SQL and managing ORM database models.",
            "Automating repetitive workflows, data extraction, and scheduled script executions.",
            "Writing automated unit and integration tests using pytest to verify business logic.",
            "Reviewing code, debugging runtime exceptions, and optimizing Python execution speed.",
            "Containerizing Python services using Docker and managing dependencies with pip.",
        ],
        "responsibilities": [
            "Design and build backend applications and REST APIs in Python.",
            "Write efficient database queries, manage ORM models, and perform data migrations.",
            "Implement automated testing suites using pytest to guarantee code reliability.",
            "Automate data extraction, transformation, and external service integrations.",
            "Maintain clean, modular code following PEP 8 conventions and OOP design principles.",
            "Collaborate with engineering teams using Git version control and code reviews.",
        ],
        "tech_stack_groups": {
            "Core Language": ["Python", "Object-Oriented Programming"],
            "Web Frameworks": ["FastAPI", "Django", "Flask"],
            "Databases": ["PostgreSQL", "SQLite", "MySQL", "SQLAlchemy", "Redis"],
            "APIs & Networking": ["REST API", "JSON", "Requests", "httpx"],
            "Testing & Tools": ["pytest", "Git", "GitHub", "Docker", "pip"],
            "Data & Automation": ["Pandas", "BeautifulSoup", "Celery"],
        },
        "skills_required": {
            "essential": ["Python", "Object-Oriented Programming", "Git", "SQL", "REST API", "Debugging", "Software Testing"],
            "common": ["FastAPI", "Django", "Flask", "JSON", "pytest", "Postman"],
            "recommended": ["Docker", "PostgreSQL", "Pandas", "Linux", "Data Structures & Algorithms"],
            "advanced": ["Asyncio / Asynchronous Python", "Celery / Background Tasks", "CI/CD", "Cloud Deployment (AWS)"],
        },
        "backend_language_flexible": False,
        "education_relevance": "Degree in Computer Science, IT, Software Engineering, Mathematics, or Data Science.",
        "experience_expectations": {
            "fresher": "Proficiency in core Python (data types, OOP, functions, file I/O), basic SQL querying, Git, and at least 2 structured Python projects.",
            "junior": "1-2 years experience building REST APIs with FastAPI/Django, writing pytest test suites, and database modeling.",
            "mid": "3-5 years experience optimizing asynchronous services, background task workers (Celery), and containerized microservices.",
            "senior": "5+ years experience designing enterprise Python architectures, managing data pipelines, and setting engineering standards.",
        },
        "competency_expectations": [
            "Write idiomatic, modular Python code following PEP 8 clean coding standards.",
            "Build complete RESTful APIs with input validation and JSON responses using FastAPI or Django.",
            "Query and manipulate relational databases using SQL and database connector libraries.",
            "Write comprehensive automated unit test suites using pytest and mock fixtures.",
        ],
        "interview_preparation": {
            "core_technical_areas": [
                "Python internals: Memory management, GIL (Global Interpreter Lock), mutable vs. immutable types.",
                "Object-Oriented Python: Dunder methods (`__init__`, `__repr__`), inheritance, decorators, and generators.",
                "FastAPI / Django architecture: Request handling, dependency injection, and ORM query optimization.",
                "SQL fundamentals: Relational joins, aggregations, transactions, and indexing.",
                "Automated testing with pytest: Test fixtures, parameterization, and mocking.",
            ],
            "coding_topics": [
                "List/dictionary comprehensions, generator expressions, and lambda functions.",
                "Custom Python class creation with property decorators and encapsulation.",
                "File parsing, JSON serialization, and structured error handling.",
            ],
            "practical_tasks": [
                "Build a REST API in FastAPI with SQLite/PostgreSQL persistence and input validation.",
                "Write a pytest suite verifying API status codes, JSON keys, and error responses.",
            ],
        },
        "not_required_yet": [
            "Kernel-level C-extension development for Python.",
            "High-scale distributed Kubernetes cluster infrastructure.",
            "Complex enterprise ERP architecture.",
        ],
        "career_progression": {
            "Junior Python Developer": "Writes Python scripts, implements API routes, fixes bugs, and writes unit tests.",
            "Mid-Level Python Developer": "Designs backend architecture, manages database schemas, and builds microservices.",
            "Senior Python Developer": "Optimizes asynchronous application throughput, sets code standards, and leads project architecture.",
            "Python Lead / Architect": "Drives enterprise technology decisions, oversees data and backend strategy, and mentors teams.",
        },
        "learning_roadmap_phases": [
            {
                "phase": "Phase 1 — Python & OOP Foundations",
                "focus": "Core data structures (lists, dicts, tuples, sets), control flow, functions, OOP classes, and PEP 8 guidelines.",
            },
            {
                "phase": "Phase 2 — Databases & SQL",
                "focus": "Relational database concepts, SQL CRUD queries, joins, and database connectivity with Python.",
            },
            {
                "phase": "Phase 3 — Modern Web API Frameworks",
                "focus": "Build REST APIs using FastAPI or Django: routing, request validation with Pydantic, and JSON responses.",
            },
            {
                "phase": "Phase 4 — Testing & Docker Containerization",
                "focus": "Automated testing with pytest, error handling, environment variables, and Dockerizing Python applications.",
            },
            {
                "phase": "Phase 5 — Production Portfolio Projects",
                "focus": "Build and deploy 2–3 complete Python backend projects with database hosting and GitHub documentation.",
            },
        ],
        "targeted_project_blueprints": [
            {
                "tier": "Beginner Project",
                "name": "Automated Data Pipeline & File Parser",
                "skills": ["Python", "Object-Oriented Programming", "Git"],
                "description": "Create an object-oriented Python application that extracts, parses, validates, and reports on complex data files.",
            },
            {
                "tier": "Intermediate Project",
                "name": "RESTful Microservice API with Database Integration",
                "skills": ["Python", "FastAPI", "SQL", "Software Testing", "Git"],
                "description": "Develop a high-performance REST API with database persistence, Swagger documentation, and automated pytest test suites.",
            },
            {
                "tier": "Job-Ready Project",
                "name": "Full-Featured Web Application Backend with Auth",
                "skills": ["Python", "FastAPI / Django", "PostgreSQL", "Docker", "REST API", "Git"],
                "description": "Engineer a production-grade backend service featuring user authentication, PostgreSQL database queries, and Docker deployment.",
            },
        ],
        "project_relevance_keywords": ["python", "automation", "api", "django", "flask", "fastapi", "backend", "script", "sqlalchemy"],
    },

    # =============================================================
    # 6. DATA ANALYST
    # =============================================================
    "data_analyst": {
        "role_id": "ROLE-DA-06",
        "role_name": "Data Analyst",
        "category": "Data & Analytics",
        "icon": "📊",
        "description": "Data Analysts collect, clean, analyze, and visualize data to identify business patterns and generate actionable insights that drive corporate decision-making.",
        "overview": (
            "Data Analysts transform raw, unstructured business data into clear, actionable executive insights. "
            "They write complex SQL queries to extract data from corporate databases, clean and manipulate datasets using Excel and Python (Pandas), "
            "perform exploratory statistical analyses, and build interactive dashboards using Power BI or Tableau. Data Analysts bridge "
            "technical data systems with strategic business decision-makers by presenting visual data stories."
        ),
        "work_activities": [
            "Extracting datasets from relational databases using multi-table SQL queries and aggregations.",
            "Cleaning, transforming, and validating raw data in Microsoft Excel and Python Pandas.",
            "Designing interactive business intelligence dashboards in Power BI or Tableau.",
            "Performing statistical analyses to identify trends, outliers, and key operational performance indicators (KPIs).",
            "Presenting analytical findings and strategic recommendations to stakeholders through visual reports.",
            "Collaborating with cross-functional teams to define business metrics and automate recurring reports.",
        ],
        "responsibilities": [
            "Extract, clean, and validate data from relational databases and flat files.",
            "Write advanced SQL queries with aggregations, window functions, and joins.",
            "Build interactive visual dashboards and KPI reports in Power BI, Tableau, or Excel.",
            "Perform exploratory data analysis and statistical validation to uncover trends.",
            "Communicate quantitative insights clearly to non-technical business stakeholders.",
            "Maintain automated data reporting pipelines and ensure data integrity.",
        ],
        "tech_stack_groups": {
            "Spreadsheets & BI": ["Microsoft Excel", "Power BI", "Tableau"],
            "Databases & Querying": ["SQL", "PostgreSQL", "MySQL", "Database Management"],
            "Programming & Analysis": ["Python", "Pandas", "NumPy", "Data Analysis"],
            "Visualization": ["Data Visualization", "Matplotlib", "Seaborn", "DAX"],
            "Mathematics": ["Statistics", "Statistical Analysis"],
        },
        "competency_matrix": [
            {
                "category": "Querying & Relational Databases",
                "tier": "CORE",
                "skills": ["SQL", "Database Management"],
                "description": "Extracting datasets using multi-table joins, aggregations, GROUP BY, subqueries, and window functions."
            },
            {
                "category": "Spreadsheet Analysis & Modeling",
                "tier": "CORE",
                "skills": ["Microsoft Excel"],
                "description": "Advanced formulas, Pivot Tables, VLOOKUP/XLOOKUP, and business financial reporting."
            },
            {
                "category": "Business Intelligence & Dashboards",
                "tier": "CORE",
                "is_alternative_group": True,
                "group_name": "BI & Visualization Tool",
                "alternatives": ["Power BI", "Tableau", "Looker", "Qlik", "Data Visualization"],
                "description": "Interactive dashboard development and KPI visualization in Power BI, Tableau, or Looker."
            },
            {
                "category": "Statistical Analysis & EDA",
                "tier": "CORE",
                "skills": ["Data Analysis", "Statistics"],
                "description": "Descriptive statistics, distribution metrics, trend identification, correlation, and exploratory data analysis."
            },
            {
                "category": "Programmatic Data Manipulation",
                "tier": "PREFERRED",
                "skills": ["Python", "Pandas", "NumPy"],
                "description": "Automated data transformation, cleaning tabular datasets, and vector operations."
            },
            {
                "category": "Advanced Analytics & ETL",
                "tier": "OPTIONAL",
                "skills": ["ETL Pipelines", "Git"],
                "description": "Automated ETL extraction pipelines and version control for analytical scripts."
            }
        ],
        "alternative_skill_clusters": [
            {
                "cluster_name": "BI & Visualization Tool",
                "options": ["Power BI", "Tableau", "Looker", "Qlik", "Data Visualization"],
                "importance": "Essential",
                "description": "Interactive business intelligence tool (Power BI, Tableau, or Looker)."
            }
        ],
        "skills_required": {
            "core": ["Microsoft Excel", "SQL", "Data Analysis", "Statistics", "BI & Visualization Tool"],
            "required": ["Data Visualization", "Database Management"],
            "preferred": ["Python", "Pandas", "NumPy", "Git"],
            "optional": ["ETL Pipelines", "Advanced Statistical Modeling", "A/B Testing"],
            "essential": ["Microsoft Excel", "SQL", "Data Analysis", "Statistics", "Data Visualization"],
            "common": ["Python", "Pandas", "Power BI", "Tableau", "Database Management"],
            "recommended": ["NumPy", "Matplotlib", "Seaborn", "Git", "Reporting"],
            "advanced": ["Advanced Statistical Modeling", "A/B Testing", "ETL Pipelines", "Big Data Analytics"],
        },
        "backend_language_flexible": False,
        "education_relevance": "Bachelor's in Computer Science, Data Science, Statistics, Mathematics, Economics, or Business Analytics.",
        "experience_expectations": {
            "fresher": "Strong command of Microsoft Excel (Pivot tables, formulas), SQL querying (joins, aggregations), and basic data visualization.",
            "junior": "1-2 years experience building business dashboards in Power BI/Tableau, performing Python Pandas analysis, and communicating insights.",
            "mid": "3-5 years experience developing automated ETL data pipelines, advanced statistical analysis, and driving strategic business decisions.",
            "senior": "5+ years experience leading corporate analytics strategy, managing BI infrastructure, and directing data teams.",
        },
        "competency_expectations": [
            "Write complex SQL queries combining data across multiple tables using joins, group by, and subqueries.",
            "Perform advanced data manipulation and financial/operational modeling in Microsoft Excel.",
            "Clean and reshape messy datasets using Python Pandas to handle missing and duplicate values.",
            "Design clear, interactive business dashboards in Power BI or Tableau that highlight critical KPIs.",
        ],
        "interview_preparation": {
            "core_technical_areas": [
                "SQL querying: INNER/LEFT/FULL joins, GROUP BY, HAVING, subqueries, and window functions (ROW_NUMBER, RANK).",
                "Excel proficiency: Pivot Tables, INDEX/MATCH, XLOOKUP, conditional formatting, and summary statistics.",
                "Python for data analysis: Pandas DataFrame filtering, groupby aggregations, and merging datasets.",
                "Data visualization best practices: Choosing the right chart type for comparison, composition, and distribution.",
                "Statistical concepts: Mean, median, mode, standard deviation, correlation vs. causation, and distributions.",
            ],
            "coding_topics": [
                "Writing multi-table SQL queries to compute monthly recurring revenue or customer retention rates.",
                "Data cleaning in Pandas: Handling NaN values, converting date strings, and creating calculated columns.",
            ],
            "practical_tasks": [
                "Build an interactive Power BI or Tableau dashboard analyzing a retail sales or financial dataset.",
                "Perform an end-to-end exploratory data analysis in a Jupyter Notebook with visualizations.",
            ],
        },
        "not_required_yet": [
            "Training deep neural networks or natural language processing transformers.",
            "Complex microservices software engineering.",
            "Low-level kernel memory tuning.",
        ],
        "career_progression": {
            "Junior Data Analyst": "Cleans datasets, writes basic SQL queries, and builds standard operational reports.",
            "Data Analyst (Mid-Level)": "Designs executive dashboards, analyzes business trends, automates data workflows, and advises teams.",
            "Senior Data Analyst": "Leads complex business analytics initiatives, defines enterprise metrics, and guides company strategy.",
            "Analytics Lead / Manager": "Oversees the corporate analytics team, manages BI tooling infrastructure, and collaborates with executive leadership.",
        },
        "learning_roadmap_phases": [
            {
                "phase": "Phase 1 — Excel & Statistical Fundamentals",
                "focus": "Master Microsoft Excel (Pivot tables, advanced formulas, charts) and descriptive statistics fundamentals.",
            },
            {
                "phase": "Phase 2 — SQL for Data Analysis",
                "focus": "Relational database querying, joins, aggregations, subqueries, and grouping techniques.",
            },
            {
                "phase": "Phase 3 — Business Intelligence Dashboards",
                "focus": "Build interactive visual reports and operational dashboards in Power BI or Tableau.",
            },
            {
                "phase": "Phase 4 — Python for Data Analytics",
                "focus": "Learn Python's Pandas and NumPy libraries for data cleaning, transformation, and visual reporting.",
            },
            {
                "phase": "Phase 5 — Analytics Portfolio & Case Studies",
                "focus": "Complete 2–3 portfolio case studies analyzing real-world business datasets and publishing interactive dashboards.",
            },
        ],
        "targeted_project_blueprints": [
            {
                "tier": "Beginner Project",
                "name": "Spreadsheet Business Performance Analysis",
                "skills": ["Microsoft Excel", "Data Analysis", "Statistics"],
                "description": "Analyze an operational business dataset in Excel using pivot tables, calculated metrics, and summary KPI charts.",
            },
            {
                "tier": "Intermediate Project",
                "name": "SQL-Driven Customer Retention & Sales Analysis",
                "skills": ["SQL", "Database Management", "Data Analysis", "Data Visualization"],
                "description": "Write advanced SQL queries to analyze customer churn, revenue trends, and product performance from a relational database.",
            },
            {
                "tier": "Job-Ready Project",
                "name": "Interactive Power BI / Python Analytics Dashboard",
                "skills": ["Power BI", "Python", "Pandas", "SQL", "Data Visualization"],
                "description": "Build an end-to-end analytics dashboard with data cleaning in Pandas, SQL extraction, and an interactive Power BI visual report.",
            },
        ],
        "project_relevance_keywords": ["data analysis", "analyst", "excel", "dashboard", "power bi", "tableau", "visualization", "analytics", "sql", "pandas"],
    },

    # =============================================================
    # 7. MACHINE LEARNING ENGINEER
    # =============================================================
    "machine_learning_engineer": {
        "role_id": "ROLE-ML-07",
        "role_name": "Machine Learning Engineer",
        "category": "Artificial Intelligence & ML",
        "icon": "🧠",
        "description": "Machine Learning Engineers design, train, evaluate, and deploy predictive AI models into software applications, bridging data science with production software engineering.",
        "overview": (
            "Machine Learning Engineers sit at the intersection of software engineering and data science. "
            "They preprocess high-volume data, design and train machine learning models using libraries like Scikit-Learn, PyTorch, "
            "and TensorFlow, evaluate model accuracy and loss metrics, and deploy inference models into production as scalable REST APIs. "
            "ML Engineers focus on model reproducibility, latency optimization, MLOps automation, and data pipeline scalability."
        ),
        "work_activities": [
            "Cleaning raw datasets, performing feature engineering, and splitting train/validation/test sets.",
            "Training, evaluating, and hyperparameter tuning machine learning algorithms for classification and regression.",
            "Wrapping trained ML models in high-speed REST API endpoints (FastAPI) for real-time inference.",
            "Monitoring production model latency, prediction accuracy, and data distribution drift.",
            "Writing automated test suites to verify data pipeline integrity and inference accuracy.",
            "Containerizing ML pipelines using Docker and managing versioned model weights.",
        ],
        "responsibilities": [
            "Preprocess structured and unstructured datasets for machine learning workflows.",
            "Train, evaluate, and optimize machine learning models for predictive performance.",
            "Deploy trained models into production as low-latency microservices and APIs.",
            "Implement automated evaluation pipelines to monitor model accuracy and data drift.",
            "Collaborate with software engineers to integrate AI models into user applications.",
            "Document model architectures, experimental benchmarks, and deployment steps.",
        ],
        "tech_stack_groups": {
            "Languages": ["Python"],
            "ML Libraries": ["Scikit-Learn", "NumPy", "Pandas", "Machine Learning"],
            "Deep Learning": ["PyTorch", "TensorFlow", "Deep Learning"],
            "Deployment & APIs": ["FastAPI", "Docker", "REST API"],
            "Mathematics": ["Statistics", "Linear Algebra", "Calculus"],
            "MLOps & Tracking": ["MLOps", "Git", "Weights & Biases"],
        },
        "skills_required": {
            "essential": ["Python", "Machine Learning", "Statistics", "Data Preprocessing", "Model Evaluation", "NumPy", "Pandas", "Scikit-Learn"],
            "common": ["REST API", "FastAPI", "SQL", "Git", "Deep Learning"],
            "recommended": ["PyTorch", "TensorFlow", "Docker", "MLOps", "Feature Engineering"],
            "advanced": ["Distributed Model Training", "Real-Time Streaming Inference", "Kubernetes", "GPU Optimization"],
        },
        "backend_language_flexible": False,
        "education_relevance": "B.E / B.Tech / M.Sc / M.Tech in Computer Science, Artificial Intelligence, Data Science, or Mathematics.",
        "experience_expectations": {
            "fresher": "Strong command of Python, NumPy, Pandas, Scikit-Learn algorithms, feature preprocessing, evaluation metrics, and at least 2 ML project repositories.",
            "junior": "1-2 years experience deploying ML models as REST APIs, optimizing hyperparameters, and managing data pipelines.",
            "mid": "3-5 years experience building production MLOps pipelines, deep learning models, and real-time inference services.",
            "senior": "5+ years experience architecting large-scale ML systems, distributed training pipelines, and leading AI initiatives.",
        },
        "competency_expectations": [
            "Preprocess and scale features, encode categorical variables, and handle imbalanced datasets.",
            "Train, cross-validate, and evaluate ML models (Random Forests, Gradient Boosting, SVMs, Linear Models).",
            "Serialize trained models (pickle/joblib/ONNX) and deploy them inside a FastAPI service.",
            "Evaluate model performance using precision, recall, F1-score, ROC-AUC, and confusion matrices.",
        ],
        "interview_preparation": {
            "core_technical_areas": [
                "Supervised vs. unsupervised learning: Classification, regression, clustering, dimensionality reduction.",
                "Bias-variance trade-off, overfitting, regularization (L1/L2), and cross-validation.",
                "Evaluation metrics: Accuracy, Precision, Recall, F1-score, ROC-AUC curve interpretation.",
                "Model algorithms: Decision Trees, Random Forests, XGBoost, Logistic Regression, K-Means.",
                "Linear algebra & calculus foundations: Matrix multiplication, dot products, gradient descent.",
            ],
            "coding_topics": [
                "Implementing data preprocessing pipelines using Scikit-Learn ColumnTransformer.",
                "Writing vectorised NumPy computations without slow Python loops.",
            ],
            "practical_tasks": [
                "Build and evaluate an end-to-end ML model on a tabular classification/regression dataset.",
                "Deploy the trained model as a FastAPI endpoint with request validation.",
            ],
        },
        "not_required_yet": [
            "Custom CUDA C++ kernel optimization for GPU clusters.",
            "Training trillion-parameter foundation LLMs from scratch.",
            "Multi-node distributed supercomputing orchestration.",
        ],
        "career_progression": {
            "Junior ML Engineer": "Preprocesses data, trains baseline models, benchmarks metrics, and assists with deployment.",
            "Machine Learning Engineer (Mid-Level)": "Designs end-to-end ML pipelines, deploys inference APIs, and optimizes model performance.",
            "Senior ML Engineer": "Architects production ML systems, establishes MLOps standards, and scales inference pipelines.",
            "Principal AI / ML Architect": "Drives enterprise AI strategy, evaluates emerging model architectures, and guides AI innovation.",
        },
        "learning_roadmap_phases": [
            {
                "phase": "Phase 1 — Python & Mathematical Foundations",
                "focus": "Python programming, NumPy array computing, linear algebra, probability, and descriptive statistics.",
            },
            {
                "phase": "Phase 2 — Data Manipulation & Feature Engineering",
                "focus": "Pandas for data cleaning, exploratory analysis, handling missing data, and feature scaling.",
            },
            {
                "phase": "Phase 3 — Machine Learning with Scikit-Learn",
                "focus": "Supervised & unsupervised algorithms, cross-validation, hyperparameter tuning, and metric evaluation.",
            },
            {
                "phase": "Phase 4 — Model Deployment & REST APIs",
                "focus": "Serialize models and build production inference endpoints with FastAPI, Docker, and input validation.",
            },
            {
                "phase": "Phase 5 — Deep Learning & MLOps",
                "focus": "Introduction to neural networks with PyTorch/TensorFlow, model tracking, and portfolio project deployment.",
            },
        ],
        "targeted_project_blueprints": [
            {
                "tier": "Beginner Project",
                "name": "Predictive Classification & Regression Model",
                "skills": ["Python", "Pandas", "Scikit-Learn", "Machine Learning", "Model Evaluation"],
                "description": "Train, evaluate, and benchmark multiple ML algorithms on a structured dataset to predict customer churn or housing prices.",
            },
            {
                "tier": "Intermediate Project",
                "name": "Real-Time Machine Learning Inference API",
                "skills": ["Python", "Scikit-Learn", "FastAPI", "REST API", "Docker"],
                "description": "Train a predictive model, serialize it, and build a containerized FastAPI service for real-time single and batch predictions.",
            },
            {
                "tier": "Job-Ready Project",
                "name": "Production MLOps End-to-End Predictive Pipeline",
                "skills": ["Python", "PyTorch / Scikit-Learn", "FastAPI", "Docker", "Git", "MLOps"],
                "description": "Build an end-to-end machine learning system with automated data preprocessing, model evaluation, and Docker deployment.",
            },
        ],
        "project_relevance_keywords": ["machine learning", "ml", "ai", "model", "scikit-learn", "tensorflow", "pytorch", "prediction", "data preprocessing"],
    },

    # =============================================================
    # 8. DATA SCIENTIST
    # =============================================================
    "data_scientist": {
        "role_id": "ROLE-DS-08",
        "role_name": "Data Scientist",
        "category": "Data & Analytics",
        "icon": "🔬",
        "description": "Data Scientists use statistical modeling, mathematical analysis, and machine learning to extract deep insights from complex data and solve strategic business challenges.",
        "overview": (
            "Data Scientists leverage advanced statistical techniques, mathematical modeling, and machine learning "
            "to solve complex analytical problems. They formulate statistical hypotheses, clean and explore large datasets, "
            "build predictive models, and design experiments (A/B testing) to validate business impact. Data Scientists combine "
            "programming in Python, SQL database querying, and visual storytelling to drive high-impact strategic decisions."
        ),
        "work_activities": [
            "Formulating statistical hypotheses and designing experimentation frameworks.",
            "Extracting, cleaning, and transforming complex datasets using SQL and Python Pandas.",
            "Building predictive machine learning models for forecasting, classification, and segmentation.",
            "Analyzing experiment results, computing confidence intervals, and evaluating statistical significance.",
            "Communicating complex quantitative findings to executive stakeholders through visual data stories.",
        ],
        "responsibilities": [
            "Perform exploratory data analysis and statistical validation on complex datasets.",
            "Develop, validate, and interpret predictive machine learning models.",
            "Design and analyze A/B tests and experimentation frameworks.",
            "Extract and transform structured and unstructured data using SQL and Python.",
            "Present data-driven insights and strategic recommendations to leadership.",
        ],
        "tech_stack_groups": {
            "Programming": ["Python", "SQL"],
            "Data & Statistics": ["Pandas", "NumPy", "Statistics", "Data Analysis"],
            "Modeling & AI": ["Scikit-Learn", "Machine Learning", "Deep Learning"],
            "Visualization": ["Data Visualization", "Matplotlib", "Seaborn", "Tableau"],
        },
        "competency_matrix": [
            {
                "category": "Scientific Programming Language",
                "tier": "CORE",
                "is_alternative_group": True,
                "group_name": "Scientific Language",
                "alternatives": ["Python", "R"],
                "description": "Programming language for scientific computation, data cleaning, and statistical modeling."
            },
            {
                "category": "Python Data Manipulation Stack",
                "tier": "CORE",
                "skills": ["Pandas", "NumPy"],
                "description": "Multi-dimensional array mathematics, tabular dataframe manipulation, and feature engineering."
            },
            {
                "category": "Probability & Statistics",
                "tier": "CORE",
                "skills": ["Statistics", "Data Analysis"],
                "description": "Hypothesis testing, probability distributions, statistical significance, correlation, and exploratory data analysis."
            },
            {
                "category": "Machine Learning & Modeling",
                "tier": "CORE",
                "skills": ["Machine Learning", "Scikit-Learn"],
                "description": "Supervised & unsupervised learning (classification, regression, clustering), cross-validation, and hyperparameter tuning."
            },
            {
                "category": "ML Frameworks & Advanced Boosting",
                "tier": "REQUIRED",
                "is_alternative_group": True,
                "group_name": "Machine Learning Framework",
                "alternatives": ["Scikit-Learn", "XGBoost", "LightGBM", "CatBoost", "Machine Learning"],
                "description": "Gradient boosting and predictive modeling algorithms (Scikit-Learn, XGBoost, or LightGBM)."
            },
            {
                "category": "Relational Data Extraction",
                "tier": "CORE",
                "skills": ["SQL"],
                "description": "Extracting datasets from operational databases using SQL joins, aggregations, and subqueries."
            },
            {
                "category": "Data Visualization & Communication",
                "tier": "REQUIRED",
                "skills": ["Data Visualization"],
                "description": "Visualizing distributions, feature correlations, and communicating findings through charts."
            },
            {
                "category": "Deep Learning & AI",
                "tier": "OPTIONAL",
                "skills": ["Deep Learning", "PyTorch", "TensorFlow"],
                "description": "Deep neural networks, NLP, or computer vision architectures."
            }
        ],
        "alternative_skill_clusters": [
            {
                "cluster_name": "Machine Learning Framework",
                "options": ["Scikit-Learn", "XGBoost", "LightGBM", "CatBoost", "Machine Learning"],
                "importance": "Essential",
                "description": "Predictive modeling and machine learning library."
            },
            {
                "cluster_name": "Scientific Language",
                "options": ["Python", "R"],
                "importance": "Essential",
                "description": "Primary data science programming language."
            }
        ],
        "skills_required": {
            "core": ["Python", "Statistics", "SQL", "Data Analysis", "Machine Learning", "Pandas", "NumPy", "Scikit-Learn"],
            "required": ["Machine Learning Framework", "Data Visualization"],
            "preferred": ["Git", "A/B Testing", "Feature Engineering", "Model Evaluation"],
            "optional": ["Deep Learning", "PyTorch", "TensorFlow", "NLP", "MLOps"],
            "essential": ["Python", "Statistics", "SQL", "Data Analysis", "Machine Learning"],
            "common": ["Pandas", "NumPy", "Scikit-Learn", "Data Visualization", "Data Preprocessing"],
            "recommended": ["Deep Learning", "Natural Language Processing", "A/B Testing", "Git"],
            "advanced": ["Causal Inference", "Big Data Analytics (Spark)", "Advanced Bayesian Modeling"],
        },
        "backend_language_flexible": False,
        "education_relevance": "Degree in Data Science, Computer Science, Statistics, Mathematics, Physics, or Economics.",
        "experience_expectations": {
            "fresher": "Strong command of Python, statistical hypothesis testing, SQL queries, Pandas exploratory analysis, and predictive modeling.",
            "junior": "1-2 years experience conducting end-to-end data science projects, interpreting business metrics, and building ML models.",
            "mid": "3-5 years experience designing A/B testing frameworks, building advanced predictive models, and advising business units.",
            "senior": "5+ years experience setting data science methodology, leading strategic analytical projects, and mentoring teams.",
        },
        "competency_expectations": [
            "Conduct thorough exploratory data analysis and communicate statistical distributions clearly.",
            "Formulate and evaluate statistical hypothesis tests and interpret p-values and confidence intervals.",
            "Train and evaluate predictive machine learning models using Scikit-Learn.",
            "Write advanced SQL queries to aggregate and join data across relational tables.",
        ],
        "interview_preparation": {
            "core_technical_areas": [
                "Probability distributions, Central Limit Theorem, and hypothesis testing (t-test, ANOVA, Chi-square).",
                "Supervised learning algorithms (Linear/Logistic Regression, Tree models, Ensemble methods).",
                "A/B testing methodology: Sample size calculation, statistical power, and significance.",
                "SQL querying for analytical metrics: Cohort retention, lifetime value, and rolling averages.",
            ],
            "coding_topics": [
                "Exploratory data analysis in Pandas with data cleaning and aggregation.",
                "Building a cross-validated predictive pipeline with Scikit-Learn.",
            ],
            "practical_tasks": [
                "Conduct an end-to-end statistical analysis and predictive modeling case study on a public dataset.",
            ],
        },
        "not_required_yet": [
            "Large-scale distributed cluster administration.",
            "Designing low-level compiler optimizations.",
        ],
        "career_progression": {
            "Junior Data Scientist": "Explores datasets, runs statistical tests, builds baseline predictive models, and creates reports.",
            "Data Scientist (Mid-Level)": "Designs experimentation frameworks, builds production predictive models, and advises business stakeholders.",
            "Senior Data Scientist": "Leads high-impact analytical initiatives, develops advanced ML algorithms, and drives data strategy.",
            "Principal Data Scientist": "Sets organizational data science vision, evaluates cutting-edge AI methodologies, and mentors scientists.",
        },
        "learning_roadmap_phases": [
            {
                "phase": "Phase 1 — Statistics & Python Foundations",
                "focus": "Python programming, NumPy, probability theory, descriptive & inferential statistics.",
            },
            {
                "phase": "Phase 2 — SQL & Data Wrangling",
                "focus": "Advanced SQL queries, data manipulation in Pandas, and exploratory data visualization.",
            },
            {
                "phase": "Phase 3 — Predictive Modeling",
                "focus": "Machine learning algorithms with Scikit-Learn, cross-validation, and metric interpretation.",
            },
            {
                "phase": "Phase 4 — Experimentation & Advanced Analytics",
                "focus": "A/B testing, hypothesis testing, feature engineering, and business storytelling.",
            },
            {
                "phase": "Phase 5 — Data Science Portfolio",
                "focus": "Publish 2–3 comprehensive case studies demonstrating statistical rigor and actionable business insights.",
            },
        ],
        "targeted_project_blueprints": [
            {
                "tier": "Beginner Project",
                "name": "Exploratory Data Analysis & Statistical Report",
                "skills": ["Python", "Pandas", "Statistics", "Data Visualization"],
                "description": "Perform comprehensive exploratory data analysis on a complex dataset and present statistical insights with visualizations.",
            },
            {
                "tier": "Intermediate Project",
                "name": "Predictive Modeling & Customer Segmentation",
                "skills": ["Python", "Scikit-Learn", "Machine Learning", "SQL"],
                "description": "Build an end-to-end predictive machine learning model with feature engineering, cross-validation, and business interpretation.",
            },
            {
                "tier": "Job-Ready Project",
                "name": "A/B Testing & Causal Impact Case Study",
                "skills": ["Python", "Statistics", "Data Analysis", "Machine Learning", "Data Visualization"],
                "description": "Design, simulate, and analyze an A/B experimentation framework evaluating feature impact on user conversion and revenue.",
            },
        ],
        "project_relevance_keywords": ["data science", "statistical", "prediction", "nlp", "clustering", "experimentation", "python", "sql", "machine learning"],
    },

    # =============================================================
    # 9. JAVA DEVELOPER
    # =============================================================
    "java_developer": {
        "role_id": "ROLE-JV-09",
        "role_name": "Java Developer",
        "category": "Software Engineering & Backend",
        "icon": "☕",
        "description": "Java Developers use Java and object-oriented design principles to build enterprise-grade backend services, distributed architectures, and scalable software applications.",
        "overview": (
            "Java Developers build mission-critical enterprise applications, high-performance microservices, and distributed backend systems. "
            "They utilize core Java, Object-Oriented design principles, and enterprise frameworks such as Spring Boot. Java Developers "
            "design database persistence layers using SQL and Hibernate/JPA, write automated test suites with JUnit, build secure REST APIs, "
            "and manage scalable enterprise applications."
        ),
        "work_activities": [
            "Writing object-oriented code in core Java adhering to SOLID engineering principles.",
            "Building RESTful microservices and enterprise backend APIs with Spring Boot.",
            "Managing relational database interactions using SQL, JDBC, and Hibernate / JPA.",
            "Writing automated unit and integration tests using JUnit and Mockito.",
            "Debugging application performance, memory leaks, and managing Maven/Gradle build configurations.",
        ],
        "responsibilities": [
            "Develop robust, scalable backend applications and microservices using Java and Spring Boot.",
            "Design relational database schemas, write SQL queries, and manage JPA persistence.",
            "Implement secure authentication, input validation, and API rate limiting.",
            "Write comprehensive automated unit and integration tests using JUnit.",
            "Participate in agile sprint ceremonies, code reviews, and Git workflows.",
        ],
        "tech_stack_groups": {
            "Language": ["Java", "Object-Oriented Programming"],
            "Frameworks": ["Spring Boot", "Spring Framework", "Hibernate"],
            "Databases & Persistence": ["SQL", "JDBC", "PostgreSQL", "MySQL"],
            "Tools & Build": ["Maven", "Gradle", "Git", "Docker"],
            "Testing": ["JUnit", "Mockito", "Software Testing"],
        },
        "skills_required": {
            "essential": ["Java", "Object-Oriented Programming", "Data Structures & Algorithms", "Git", "SQL", "JDBC"],
            "common": ["Spring Boot", "REST API", "Software Testing", "JSON", "Debugging"],
            "recommended": ["Docker", "Maven", "Gradle", "Hibernate", "PostgreSQL"],
            "advanced": ["Microservices Architecture", "Spring Cloud", "Kafka / Message Queues", "JVM Performance Tuning"],
        },
        "backend_language_flexible": False,
        "education_relevance": "B.Sc / B.Tech / B.E / MCA in Computer Science, IT, or related technical field.",
        "experience_expectations": {
            "fresher": "Strong command of core Java (OOP, collections, exception handling, multithreading basics), SQL queries, Git, and Java project evidence.",
            "junior": "1-2 years experience building REST APIs with Spring Boot, writing JUnit tests, and managing database persistence.",
            "mid": "3-5 years experience designing microservices, optimizing database transactions, and managing message queues.",
            "senior": "5+ years experience in enterprise architecture, JVM performance tuning, and high-concurrency distributed systems.",
        },
        "competency_expectations": [
            "Apply Java OOP principles, collections framework, and generics effectively.",
            "Build complete RESTful microservice APIs using Spring Boot.",
            "Connect Java applications to relational databases using JDBC and JPA.",
            "Write automated unit tests using JUnit and Mockito.",
        ],
        "interview_preparation": {
            "core_technical_areas": [
                "Java fundamentals: Memory management (Heap vs. Stack, Garbage Collection), immutability, strings.",
                "OOP principles: Polymorphism, abstract classes vs. interfaces, SOLID design.",
                "Java Collections Framework: ArrayList, LinkedList, HashMap, HashSet internal mechanics.",
                "Spring Boot: Dependency Injection, Inversion of Control, annotations, and Spring Data JPA.",
                "SQL fundamentals: Relational joins, transactions, and JDBC connections.",
            ],
            "coding_topics": [
                "Implementing custom data structures and collections in Java.",
                "Algorithmic problem solving: Array manipulation, string processing, and tree traversal.",
            ],
            "practical_tasks": [
                "Build a complete REST API using Spring Boot with SQLite/PostgreSQL persistence.",
                "Write a JUnit test suite verifying API controllers and service logic.",
            ],
        },
        "not_required_yet": [
            "Low-level JVM bytecode manipulation.",
            "Multi-datacenter global database replication.",
        ],
        "career_progression": {
            "Junior Java Developer": "Implements service endpoints, fixes bugs, and writes JUnit tests under senior guidance.",
            "Java Developer (Mid-Level)": "Designs microservices, manages database models, and implements business logic.",
            "Senior Java Developer": "Architects enterprise services, optimizes JVM performance, and ensures high availability.",
            "Java Lead / Architect": "Defines enterprise Java architecture, oversees technology stack, and guides engineering teams.",
        },
        "learning_roadmap_phases": [
            {
                "phase": "Phase 1 — Core Java & OOP",
                "focus": "Java syntax, object-oriented programming, collections framework, exception handling, and Git.",
            },
            {
                "phase": "Phase 2 — Databases & JDBC",
                "focus": "Relational SQL querying, database normalization, and Java database connectivity via JDBC.",
            },
            {
                "phase": "Phase 3 — Spring Boot & REST APIs",
                "focus": "Build RESTful microservices with Spring Boot, Spring Data JPA, and JSON endpoints.",
            },
            {
                "phase": "Phase 4 — Testing & Build Tools",
                "focus": "Automated testing with JUnit and Mockito, dependency management with Maven, and Docker.",
            },
            {
                "phase": "Phase 5 — Enterprise Portfolio Projects",
                "focus": "Build and deploy 2–3 structured Spring Boot projects with database persistence and GitHub documentation.",
            },
        ],
        "targeted_project_blueprints": [
            {
                "tier": "Beginner Project",
                "name": "Java Object-Oriented Banking / Management System",
                "skills": ["Java", "Object-Oriented Programming", "Git"],
                "description": "Build a modular console/GUI application implementing user accounts, transactions, and file persistence.",
            },
            {
                "tier": "Intermediate Project",
                "name": "Spring Boot REST API with SQL Database",
                "skills": ["Java", "Spring Boot", "SQL", "JDBC", "Software Testing"],
                "description": "Develop a Spring Boot REST API with database persistence, input validation, and JUnit test coverage.",
            },
            {
                "tier": "Job-Ready Project",
                "name": "Enterprise Microservice with Auth & PostgreSQL",
                "skills": ["Java", "Spring Boot", "PostgreSQL", "Docker", "REST API", "Git"],
                "description": "Build a production-grade enterprise service featuring JWT authentication, database migrations, and Docker deployment.",
            },
        ],
        "project_relevance_keywords": ["java", "spring", "spring boot", "oop", "jdbc", "enterprise", "sql"],
    },

    # =============================================================
    # 10. WEB DEVELOPER
    # =============================================================
    "web_developer": {
        "role_id": "ROLE-WD-10",
        "role_name": "Web Developer",
        "category": "Web & Mobile Development",
        "icon": "💻",
        "description": "Web Developers create websites and web applications, ensuring they look modern, load fast, function smoothly, and provide an engaging user experience across all devices.",
        "overview": (
            "Web Developers specialize in creating, deploying, and maintaining websites and web applications. "
            "They utilize HTML5, CSS3, and JavaScript to build responsive web pages, implement interactive UI components, "
            "ensure mobile-friendly layouts, and connect websites to backend services or content management systems. "
            "Web development provides a highly accessible and practical pathway for candidates entering the technology industry."
        ),
        "work_activities": [
            "Building responsive web pages and landing pages from design mockups.",
            "Styling modern user interfaces using CSS3 Flexbox, Grid, and CSS frameworks.",
            "Adding interactive client-side functionality using vanilla JavaScript.",
            "Testing websites for responsive layout compatibility across mobile and desktop devices.",
            "Publishing and deploying websites to web hosting servers and managing code with Git.",
        ],
        "responsibilities": [
            "Develop clean, responsive, and mobile-friendly websites.",
            "Implement responsive CSS layouts and interactive JavaScript behaviors.",
            "Ensure cross-browser compatibility and optimize page load speeds.",
            "Connect client web pages to backend APIs and web services.",
            "Manage website code and asset versions using Git.",
        ],
        "tech_stack_groups": {
            "Core Technologies": ["HTML5", "CSS3", "JavaScript"],
            "Design & Layout": ["Responsive Design", "Bootstrap", "Tailwind CSS"],
            "Tools & Deployment": ["Git", "GitHub", "npm"],
            "APIs": ["REST API", "JSON"],
        },
        "competency_matrix": [
            {
                "category": "Core Web Languages",
                "tier": "CORE",
                "skills": ["HTML5", "CSS3", "JavaScript"],
                "description": "Semantic HTML markup, modern CSS styling, and core JavaScript DOM scripting."
            },
            {
                "category": "Frontend Frameworks",
                "tier": "REQUIRED",
                "is_alternative_group": True,
                "group_name": "Frontend Framework",
                "alternatives": ["React", "Next.js", "Vue.js", "Angular", "TypeScript"],
                "description": "Building component-based web interfaces using modern frameworks."
            },
            {
                "category": "Web Technologies & APIs",
                "tier": "REQUIRED",
                "skills": ["Responsive Design", "REST APIs", "DOM Concepts", "Accessibility"],
                "description": "Responsive mobile-first layouts, REST APIs, DOM manipulation, and web accessibility."
            },
            {
                "category": "Development Tools",
                "tier": "CORE",
                "skills": ["Git", "GitHub", "VS Code", "npm", "Postman"],
                "description": "Version control workflows, package management, and API testing tools."
            },
            {
                "category": "Testing & Performance",
                "tier": "NICE_TO_HAVE",
                "skills": ["Jest", "Playwright", "Cypress", "Web Performance", "Browser DevTools"],
                "description": "Automated web testing and performance optimization."
            },
            {
                "category": "Deployment & Hosting",
                "tier": "NICE_TO_HAVE",
                "skills": ["Vercel", "Netlify", "GitHub Pages", "Cloud Platforms"],
                "description": "Hosting and deploying web applications to modern cloud hosting platforms."
            },
        ],
        "alternative_skill_clusters": [
            {
                "cluster_name": "Frontend Framework (any one)",
                "options": ["React", "Next.js", "Vue.js", "Angular", "TypeScript"],
                "required_count": 1,
            },
            {
                "cluster_name": "Web Hosting (any one)",
                "options": ["Vercel", "Netlify", "GitHub Pages", "Render", "AWS"],
                "required_count": 1,
            }
        ],
        "skills_required": {
            "essential": ["HTML5", "CSS3", "JavaScript", "Responsive Design", "Git"],
            "common": ["REST APIs", "Bootstrap", "Tailwind CSS", "DOM Concepts", "VS Code"],
            "recommended": ["React", "Next.js", "TypeScript", "Vercel", "Netlify", "Jest"],
            "advanced": ["Web Performance", "Playwright", "Cypress", "Accessibility"],
        },
        "backend_language_flexible": False,
        "education_relevance": "Degree in Computer Science, IT, or a strong portfolio of responsive live websites.",
        "experience_expectations": {
            "fresher": "Demonstrated ability to build responsive web pages using HTML5, CSS3, JavaScript, and Git.",
            "junior": "1-2 years experience building multi-page web applications and integrating REST APIs.",
            "mid": "3-5 years experience developing frontend components, managing web performance, and deploying sites.",
            "senior": "5+ years experience leading web development initiatives and architecture.",
        },
        "competency_expectations": [
            "Build responsive, multi-page websites using semantic HTML5 and modern CSS3.",
            "Implement client-side interactivity and event handling using vanilla JavaScript.",
            "Deploy live web pages to hosting services and maintain source code in Git.",
        ],
        "interview_preparation": {
            "core_technical_areas": [
                "Semantic HTML5 elements and page structure.",
                "Responsive CSS styling: Media queries, Flexbox, and CSS Grid.",
                "Basic JavaScript DOM manipulation and event listeners.",
            ],
            "coding_topics": [
                "Building a responsive navigation bar and mobile menu toggle.",
                "Form validation using client-side JavaScript.",
            ],
            "practical_tasks": [
                "Build and deploy a responsive multi-section landing page.",
            ],
        },
        "not_required_yet": [
            "Complex microservices backend architectures.",
            "Distributed Kubernetes cluster management.",
        ],
        "career_progression": {
            "Junior Web Developer": "Builds web pages, updates content, fixes CSS styling issues, and publishes sites.",
            "Web Developer (Mid-Level)": "Builds interactive web applications, integrates APIs, and optimizes mobile responsiveness.",
            "Senior Web Developer": "Leads web development projects, defines frontend standards, and ensures high performance.",
        },
        "learning_roadmap_phases": [
            {
                "phase": "Phase 1 — HTML5 & CSS3 Mastery",
                "focus": "Semantic HTML5, CSS styling, Flexbox, CSS Grid, responsive design, and Git.",
            },
            {
                "phase": "Phase 2 — JavaScript Interactivity",
                "focus": "DOM manipulation, event handling, forms, and asynchronous API calls.",
            },
            {
                "phase": "Phase 3 — UI Frameworks & Styling",
                "focus": "CSS frameworks (Tailwind CSS/Bootstrap) and basic component development.",
            },
            {
                "phase": "Phase 4 — Deployment & Web Portfolio",
                "focus": "Build and host 2–3 live responsive websites on Netlify, Vercel, or GitHub Pages.",
            },
        ],
        "targeted_project_blueprints": [
            {
                "tier": "Beginner Project",
                "name": "Responsive Multi-Page Business Website",
                "skills": ["HTML5", "CSS3", "Responsive Design", "Git"],
                "description": "Create a modern responsive website featuring navigation menus, product cards, and a contact form.",
            },
            {
                "tier": "Intermediate Project",
                "name": "Interactive Web App with API Integration",
                "skills": ["HTML5", "CSS3", "JavaScript", "REST API", "DOM Concepts"],
                "description": "Build an interactive web application that fetches and displays live data from a public REST API.",
            },
        ],
        "project_relevance_keywords": ["web", "website", "html", "css", "landing page", "frontend", "responsive"],
    },

    # =============================================================
    # 11. DEVOPS ENGINEER
    # =============================================================
    "devops_engineer": {
        "role_id": "ROLE-DO-11",
        "role_name": "DevOps Engineer",
        "category": "Cloud & Infrastructure",
        "icon": "☁️",
        "description": "DevOps Engineers automate software delivery pipelines, manage cloud infrastructure, configure container orchestration, and ensure continuous application reliability and uptime.",
        "overview": (
            "DevOps Engineers bridge software development and IT infrastructure operations. "
            "They automate continuous integration and continuous deployment (CI/CD) pipelines, manage Linux servers, "
            "containerize services with Docker, orchestrate container clusters with Kubernetes, and provision cloud infrastructure (AWS/Azure/GCP). "
            "DevOps Engineers maintain system observability, logging, and infrastructure security."
        ),
        "work_activities": [
            "Configuring automated CI/CD deployment pipelines using GitHub Actions, GitLab CI, or Jenkins.",
            "Containerizing backend services and microservices using Docker and Docker Compose.",
            "Administering Linux servers, shell scripting, and managing network security firewalls.",
            "Monitoring system health, server resource utilization, and application error logs.",
        ],
        "responsibilities": [
            "Build, maintain, and optimize automated CI/CD build and deployment pipelines.",
            "Containerize applications and manage container deployment environments.",
            "Administer Linux server environments, automate bash scripts, and manage user permissions.",
            "Monitor system performance, configure alerts, and troubleshoot infrastructure failures.",
        ],
        "tech_stack_groups": {
            "Containers & Orchestration": ["Docker", "Kubernetes"],
            "Operating Systems & Scripting": ["Linux", "Python", "Bash"],
            "CI/CD & Version Control": ["CI/CD", "Git", "GitHub"],
            "Cloud Platforms": ["AWS", "Cloud"],
        },
        "skills_required": {
            "essential": ["Linux", "Git", "Docker", "CI/CD", "Python"],
            "common": ["AWS", "Bash Scripting", "Cloud", "Software Testing"],
            "recommended": ["Kubernetes", "Terraform", "Monitoring (Prometheus/Grafana)"],
            "advanced": ["Infrastructure as Code", "Site Reliability Engineering (SRE)", "Multi-Cloud Architecture"],
        },
        "backend_language_flexible": False,
        "education_relevance": "Degree in Computer Science, IT, Systems Engineering, or cloud certification credentials.",
        "experience_expectations": {
            "fresher": "Strong command of Linux commands, shell scripting, Git workflows, Docker containerization, and basic CI/CD.",
            "junior": "1-2 years experience managing CI/CD pipelines, Docker deployments, and cloud hosting.",
            "mid": "3-5 years experience with Kubernetes cluster management, infrastructure-as-code, and cloud security.",
            "senior": "5+ years experience architecting enterprise cloud platforms and site reliability engineering.",
        },
        "competency_expectations": [
            "Write Dockerfiles to containerize applications and manage multi-container setups with Docker Compose.",
            "Configure a GitHub Actions CI/CD pipeline to automate testing and build verification.",
            "Administer Linux servers via SSH, manage systemd services, and write automation scripts.",
        ],
        "interview_preparation": {
            "core_technical_areas": [
                "Linux OS fundamentals: Process management, file permissions, networking (TCP/IP, DNS, ports).",
                "Docker architecture: Images, containers, layers, networking, and volume persistence.",
                "CI/CD pipeline concepts: Build stages, artifact management, automated testing gates.",
            ],
            "coding_topics": [
                "Writing Bash or Python scripts for log parsing and automated system health checks.",
            ],
            "practical_tasks": [
                "Containerize a full-stack application and set up an automated GitHub Actions deployment pipeline.",
            ],
        },
        "not_required_yet": [
            "Multi-region hybrid cloud mesh networking.",
        ],
        "career_progression": {
            "Junior DevOps Engineer": "Maintains CI/CD scripts, manages container images, and assists with server administration.",
            "DevOps / SRE Engineer": "Designs deployment pipelines, manages cloud infrastructure, and implements observability.",
            "Senior DevOps Engineer": "Architects resilient cloud platforms, automates security compliance, and scales infrastructure.",
        },
        "learning_roadmap_phases": [
            {
                "phase": "Phase 1 — Linux & Version Control",
                "focus": "Linux command line, shell scripting, networking basics, and advanced Git branching.",
            },
            {
                "phase": "Phase 2 — Containerization with Docker",
                "focus": "Docker images, container networking, multi-stage builds, and Docker Compose.",
            },
            {
                "phase": "Phase 3 — CI/CD Automation",
                "focus": "GitHub Actions pipelines, automated test runs, and continuous deployment workflows.",
            },
            {
                "phase": "Phase 4 — Cloud Infrastructure Basics",
                "focus": "Cloud hosting on AWS/GCP (EC2, S3, IAM), container deployment, and monitoring.",
            },
        ],
        "targeted_project_blueprints": [
            {
                "tier": "Beginner Project",
                "name": "Automated Linux Server Monitor Script",
                "skills": ["Linux", "Python", "Git"],
                "description": "Write a Python/Bash script that monitors CPU/memory utilization, parses system logs, and sends alert notifications.",
            },
            {
                "tier": "Intermediate Project",
                "name": "Dockerized Application with Automated CI/CD",
                "skills": ["Docker", "CI/CD", "Git", "Linux"],
                "description": "Containerize a web service with Docker and configure a GitHub Actions pipeline to run tests and build images automatically.",
            },
        ],
        "project_relevance_keywords": ["devops", "docker", "kubernetes", "cloud", "aws", "ci/cd", "cicd", "linux"],
    },

    # =============================================================
    # 12. QA / TEST AUTOMATION ENGINEER
    # =============================================================
    "qa_engineer": {
        "role_id": "ROLE-QA-12",
        "role_name": "QA / Test Automation Engineer",
        "category": "Quality Assurance & Testing",
        "icon": "🧪",
        "description": "QA Engineers design, develop, and execute automated test suites to ensure software applications meet functional, performance, and reliability standards before release.",
        "overview": (
            "QA and Test Automation Engineers ensure that software applications are robust, reliable, and bug-free. "
            "They write automated test scripts in Python or Java, execute end-to-end and integration test suites, validate REST API endpoints, "
            "and identify software defects early in the development lifecycle. QA engineers collaborate with developers to maintain "
            "high quality standards across releases."
        ),
        "work_activities": [
            "Writing and maintaining automated unit, integration, and UI test scripts.",
            "Testing REST API endpoints for correct status codes, response payloads, and edge cases.",
            "Documenting reproducible bug reports, stack traces, and verification steps in issue trackers.",
            "Integrating automated test runs into continuous integration (CI/CD) pipelines.",
        ],
        "responsibilities": [
            "Develop, maintain, and execute automated test suites for web and backend applications.",
            "Perform API testing and functional validation using tools like Postman and automated scripts.",
            "Identify, document, and track software defects through resolution.",
            "Collaborate with software engineers to define test plans and acceptance criteria.",
        ],
        "tech_stack_groups": {
            "Programming": ["Python", "Java", "JavaScript"],
            "Testing Frameworks": ["Software Testing", "pytest", "JUnit", "Selenium", "Playwright"],
            "Tools & APIs": ["REST API", "Postman", "Git", "JSON"],
        },
        "skills_required": {
            "essential": ["Software Testing", "Python", "Git", "REST API", "Debugging"],
            "common": ["Postman", "JSON", "SQL", "pytest", "Java"],
            "recommended": ["Selenium / Playwright", "CI/CD", "Docker"],
            "advanced": ["Performance & Load Testing (JMeter)", "Security Penetration Testing"],
        },
        "backend_language_flexible": True,
        "education_relevance": "Degree in Computer Science, Information Technology, or Software Engineering.",
        "experience_expectations": {
            "fresher": "Understanding of software testing types (unit, integration, regression), test case writing, basic Python/Java, and API testing.",
            "junior": "1-2 years experience writing automated test scripts and integrating tests with CI pipelines.",
            "mid": "3-5 years experience developing comprehensive test automation frameworks.",
        },
        "competency_expectations": [
            "Write automated test scripts verifying API responses and UI behaviors.",
            "Create structured test cases covering positive, negative, and edge-case scenarios.",
        ],
        "interview_preparation": {
            "core_technical_areas": [
                "Testing pyramid: Unit vs. Integration vs. End-to-End testing.",
                "API testing: Request methods, status codes, payload assertions.",
                "Test automation frameworks in Python (pytest) or Java (JUnit).",
            ],
            "coding_topics": [
                "Writing a parameterized automated test suite for an API.",
            ],
            "practical_tasks": [
                "Build an automated test suite verifying a REST API using pytest or Postman.",
            ],
        },
        "not_required_yet": [
            "Large-scale distributed systems architecture.",
        ],
        "career_progression": {
            "Junior QA Engineer": "Executes test cases, writes automated tests, and files bug reports.",
            "QA Automation Engineer": "Builds and maintains automated testing frameworks across services.",
            "Senior QA Lead": "Defines enterprise test automation strategy and manages quality across releases.",
        },
        "learning_roadmap_phases": [
            {
                "phase": "Phase 1 — Software Testing Fundamentals",
                "focus": "Testing concepts (unit, integration, regression), test case design, and bug reporting.",
            },
            {
                "phase": "Phase 2 — Automated API Testing",
                "focus": "Automating API test cases using Python (pytest/requests) or Postman collections.",
            },
            {
                "phase": "Phase 3 — UI Automation & CI/CD",
                "focus": "Browser UI test automation using Playwright/Selenium and CI pipeline integration.",
            },
        ],
        "targeted_project_blueprints": [
            {
                "tier": "Beginner Project",
                "name": "Automated REST API Test Suite",
                "skills": ["Python", "Software Testing", "REST API", "Git"],
                "description": "Develop a comprehensive automated test suite in Python/pytest validating a public REST API.",
            },
        ],
        "project_relevance_keywords": ["testing", "qa", "quality assurance", "pytest", "junit", "selenium", "automation", "test"],
    },

    # =============================================================
    # 13. MOBILE DEVELOPER
    # =============================================================
    "mobile_developer": {
        "role_id": "ROLE-MD-13",
        "role_name": "Mobile Developer",
        "category": "Web & Mobile Development",
        "icon": "📱",
        "description": "Mobile Developers build native and cross-platform applications for iOS and Android mobile devices, delivering responsive and engaging mobile user experiences.",
        "overview": (
            "Mobile Developers engineer user applications for smartphones and tablets. "
            "They develop mobile interfaces, manage local on-device data storage, handle mobile device hardware sensors (camera, GPS), "
            "integrate backend REST APIs, and optimize mobile app responsiveness and battery consumption."
        ),
        "work_activities": [
            "Building responsive mobile user interfaces for Android and iOS devices.",
            "Integrating backend REST APIs to synchronize data with server databases.",
            "Managing local mobile storage and offline application state.",
            "Testing applications on physical mobile devices and emulators.",
        ],
        "responsibilities": [
            "Develop cross-platform or native mobile applications.",
            "Connect mobile user interfaces to backend REST APIs.",
            "Ensure smooth animations and mobile performance optimization.",
            "Manage mobile application builds and version control.",
        ],
        "tech_stack_groups": {
            "Cross-Platform & Native Frameworks": ["React Native", "Flutter", "Android SDK", "SwiftUI", "UIKit"],
            "Languages": ["Kotlin", "Java", "Swift", "Dart", "JavaScript", "TypeScript"],
            "Mobile Concepts": ["Mobile UI", "State Management", "Navigation", "Local Storage", "Push Notifications"],
            "APIs & Networking": ["REST APIs", "JSON", "Firebase"],
            "Development Tools": ["Git", "GitHub", "Android Studio", "Xcode"],
        },
        "competency_matrix": [
            {
                "category": "Mobile Frameworks",
                "tier": "CORE",
                "is_alternative_group": True,
                "group_name": "Mobile Framework",
                "alternatives": ["React Native", "Flutter", "Android SDK", "SwiftUI", "UIKit", "Kotlin", "Swift"],
                "description": "Cross-platform (React Native/Flutter) or native mobile framework architecture."
            },
            {
                "category": "Programming Languages",
                "tier": "CORE",
                "is_alternative_group": True,
                "group_name": "Mobile Language",
                "alternatives": ["Kotlin", "Swift", "Dart", "JavaScript", "TypeScript", "Java"],
                "description": "Mobile application programming language."
            },
            {
                "category": "Mobile UI & State",
                "tier": "REQUIRED",
                "skills": ["Mobile UI", "State Management", "Responsive Design"],
                "description": "Mobile layout design, multi-screen navigation, and reactive state management."
            },
            {
                "category": "APIs & Networking",
                "tier": "REQUIRED",
                "skills": ["REST APIs", "JSON"],
                "description": "Consuming backend REST APIs, JSON serialization, and asynchronous networking."
            },
            {
                "category": "Version Control & Tooling",
                "tier": "CORE",
                "skills": ["Git"],
                "description": "Git repository management and team collaboration."
            },
            {
                "category": "Mobile IDEs & Storage",
                "tier": "REQUIRED",
                "skills": ["Android Studio", "Xcode", "Local Storage", "Firebase"],
                "description": "Mobile IDE tooling, offline persistence, and cloud services."
            },
        ],
        "alternative_skill_clusters": [
            {
                "cluster_name": "Mobile Framework (any one)",
                "options": ["React Native", "Flutter", "Android SDK", "SwiftUI", "UIKit", "Kotlin", "Swift"],
                "required_count": 1,
            },
            {
                "cluster_name": "Mobile Language (any one)",
                "options": ["Kotlin", "Swift", "Dart", "JavaScript", "TypeScript", "Java"],
                "required_count": 1,
            }
        ],
        "skills_required": {
            "essential": ["React Native or Flutter or Android SDK or Swift", "JavaScript or TypeScript or Kotlin or Swift or Dart", "Git"],
            "common": ["REST APIs", "Mobile UI", "State Management", "JSON"],
            "recommended": ["Android Studio", "Xcode", "Firebase", "Local Storage"],
            "advanced": ["Push Notifications", "Mobile Testing", "App Deployment"],
        },
        "backend_language_flexible": False,
        "education_relevance": "Degree in Computer Science, IT, or demonstrated mobile app project portfolio.",
        "experience_expectations": {
            "fresher": "Solid programming fundamentals in JavaScript/Java/Dart, responsive mobile UI design, and mobile project evidence.",
            "junior": "1-2 years experience building cross-platform mobile apps and integrating backend APIs.",
            "mid": "3-5 years experience managing state, native device modules, and offline synchronization.",
        },
        "competency_expectations": [
            "Build a responsive mobile application with multiple navigation screens.",
            "Fetch and display remote data from a REST API on a mobile device.",
        ],
        "interview_preparation": {
            "core_technical_areas": [
                "Mobile lifecycle: App states (foreground, background, suspended).",
                "Mobile UI navigation: Stack navigation, tab bars, drawer menus.",
                "Consuming REST APIs and handling offline caching.",
            ],
            "coding_topics": [
                "Component state management and asynchronous API calls on mobile.",
            ],
            "practical_tasks": [
                "Build a mobile app with API data fetching and local item bookmarking.",
            ],
        },
        "not_required_yet": [
            "Custom native C++ graphics rendering engines.",
        ],
        "career_progression": {
            "Junior Mobile Developer": "Builds mobile screens, fixes layout bugs, and connects APIs.",
            "Mobile Developer (Mid-Level)": "Architects mobile state, integrates native device features, and manages app releases.",
            "Senior Mobile Lead": "Defines mobile architecture, establishes design system patterns, and optimizes performance.",
        },
        "learning_roadmap_phases": [
            {
                "phase": "Phase 1 — Programming Foundations",
                "focus": "Master core JavaScript or Java/Kotlin and OOP fundamentals.",
            },
            {
                "phase": "Phase 2 — Mobile UI & Frameworks",
                "focus": "Learn React Native or Flutter for cross-platform mobile UI development.",
            },
            {
                "phase": "Phase 3 — API Integration & Mobile Deployment",
                "focus": "Connect mobile apps to REST APIs, manage local storage, and build portfolio apps.",
            },
        ],
        "targeted_project_blueprints": [
            {
                "tier": "Beginner Project",
                "name": "Mobile News & Weather App",
                "skills": ["JavaScript", "REST API", "Git"],
                "description": "Develop a mobile application that fetches live weather or news data and displays it across clean mobile cards.",
            },
        ],
        "project_relevance_keywords": ["mobile", "android", "ios", "react native", "flutter", "kotlin", "swift", "app"],
    },

    # =============================================================
    # 14. CLOUD ENGINEER
    # =============================================================
    "cloud_engineer": {
        "role_id": "ROLE-CL-14",
        "role_name": "Cloud Solutions Engineer",
        "category": "Cloud & Infrastructure",
        "icon": "☁️",
        "description": "Cloud Engineers design, deploy, and manage scalable cloud computing infrastructure and services across platforms like AWS, Azure, and Google Cloud.",
        "overview": (
            "Cloud Solutions Engineers architect and maintain enterprise infrastructure in the cloud. "
            "They configure virtual computing instances, manage serverless functions, configure cloud storage and relational databases, "
            "implement identity and access management (IAM) policies, and ensure cost-effective cloud resource utilization."
        ),
        "work_activities": [
            "Provisioning and managing cloud instances (AWS EC2, S3, RDS, Lambda).",
            "Configuring cloud security groups, virtual private clouds (VPC), and IAM access permissions.",
            "Deploying containerized backend applications to cloud computing platforms.",
            "Monitoring cloud infrastructure costs, resource scaling, and performance metrics.",
        ],
        "responsibilities": [
            "Design and deploy scalable cloud infrastructure solutions.",
            "Implement secure IAM identity policies and virtual private network boundaries.",
            "Deploy containerized microservices and configure automated backups.",
            "Monitor cloud resource utilization and optimize monthly infrastructure costs.",
        ],
        "tech_stack_groups": {
            "Cloud Platforms": ["AWS", "Cloud", "GCP", "Azure"],
            "Containers & Tools": ["Docker", "Linux", "Git"],
            "Programming": ["Python", "Bash"],
            "Databases": ["PostgreSQL", "SQL", "Database Management"],
        },
        "skills_required": {
            "essential": ["Cloud", "AWS", "Linux", "Git", "Python", "Networking Basics"],
            "common": ["Docker", "SQL", "Database Management", "Security Basics"],
            "recommended": ["Terraform", "CI/CD", "Serverless (Lambda)"],
            "advanced": ["Multi-Region Cloud Architecture", "Cloud Cost Governance", "Enterprise Disaster Recovery"],
        },
        "backend_language_flexible": False,
        "education_relevance": "Degree in Computer Science, IT, or cloud certification credentials (e.g. AWS Certified Solutions Architect).",
        "experience_expectations": {
            "fresher": "Understanding of cloud computing models (IaaS/PaaS/SaaS), Linux fundamentals, Python scripting, and AWS core services.",
            "junior": "1-2 years experience deploying applications and configuring cloud security in AWS/Azure.",
            "mid": "3-5 years experience designing scalable cloud architectures and infrastructure-as-code.",
        },
        "competency_expectations": [
            "Deploy and configure a virtual cloud server (EC2) with security groups and SSH access.",
            "Configure cloud object storage (S3) and connect it to backend services.",
        ],
        "interview_preparation": {
            "core_technical_areas": [
                "Cloud service models: IaaS vs. PaaS vs. Serverless.",
                "AWS core services: EC2, S3, RDS, Lambda, IAM, VPC.",
                "Cloud security: Least privilege IAM policies, security groups, and encryption at rest/in transit.",
            ],
            "coding_topics": [
                "Python scripting with Boto3 (AWS SDK) for cloud automation.",
            ],
            "practical_tasks": [
                "Deploy a containerized application to AWS with an RDS PostgreSQL database.",
            ],
        },
        "not_required_yet": [
            "Enterprise hybrid-cloud interconnect architecture.",
        ],
        "career_progression": {
            "Junior Cloud Engineer": "Deploys cloud instances, monitors resource metrics, and manages storage buckets.",
            "Cloud Solutions Engineer": "Designs cloud architectures, automates infrastructure, and implements security controls.",
            "Senior Cloud Architect": "Defines enterprise cloud strategy, oversees cloud migration, and drives multi-cloud roadmaps.",
        },
        "learning_roadmap_phases": [
            {
                "phase": "Phase 1 — Linux & Networking",
                "focus": "Linux administration, TCP/IP networking, DNS, SSH, and Python scripting.",
            },
            {
                "phase": "Phase 2 — AWS Core Services",
                "focus": "Master AWS EC2, S3, IAM, VPC, RDS, and serverless Lambda functions.",
            },
            {
                "phase": "Phase 3 — Cloud Automation & Containers",
                "focus": "Deploy Docker containers to the cloud and automate infrastructure provisioning.",
            },
        ],
        "targeted_project_blueprints": [
            {
                "tier": "Beginner Project",
                "name": "Cloud Storage & Static Web Hosting",
                "skills": ["AWS", "Cloud", "Linux", "Git"],
                "description": "Configure an AWS S3 bucket for secure asset storage and host a static web application with custom domain routing.",
            },
        ],
        "project_relevance_keywords": ["cloud", "aws", "azure", "gcp", "serverless", "infrastructure", "ec2", "s3"],
    },

    # =============================================================
    # 15. CYBERSECURITY ANALYST
    # =============================================================
    "cybersecurity_analyst": {
        "role_id": "ROLE-SEC-15",
        "role_name": "Cybersecurity Analyst",
        "category": "Security & Systems",
        "icon": "🛡️",
        "description": "Cybersecurity Analysts monitor, assess, and protect networks, servers, and applications against security vulnerabilities, malware threats, and cyberattacks.",
        "overview": (
            "Cybersecurity Analysts safeguard organizational digital assets, networks, and software applications. "
            "They analyze system logs for anomalous activity, perform vulnerability scans, implement secure authentication protocols, "
            "configure network firewalls, and ensure compliance with information security standards."
        ),
        "work_activities": [
            "Monitoring network traffic and security event logs for unauthorized access attempts.",
            "Performing vulnerability assessments and reviewing code for security flaws (OWASP Top 10).",
            "Configuring firewall rules, VPNs, and multi-factor authentication systems.",
            "Responding to security incident alerts and documenting remediation steps.",
        ],
        "responsibilities": [
            "Monitor security alerts and investigate potential security incidents.",
            "Perform vulnerability assessments on networks and web applications.",
            "Implement security best practices (password policies, encryption, access controls).",
            "Document security procedures, incident reports, and compliance guidelines.",
        ],
        "tech_stack_groups": {
            "Security & Networking": ["Cybersecurity", "Authentication", "Linux", "Networking Basics"],
            "Languages & Tools": ["Python", "Bash", "Git", "Wireshark"],
        },
        "skills_required": {
            "essential": ["Linux", "Authentication", "Networking Basics", "Python", "Git"],
            "common": ["Cybersecurity", "SQL", "Security Auditing", "Debugging"],
            "recommended": ["Vulnerability Scanning", "Cryptography", "Bash"],
            "advanced": ["Penetration Testing (Metasploit)", "SIEM Engineering (Splunk)", "Incident Response"],
        },
        "backend_language_flexible": False,
        "education_relevance": "Degree in Computer Science, Cybersecurity, Information Systems, or security certifications (Security+, CEH).",
        "experience_expectations": {
            "fresher": "Strong command of networking (TCP/IP, ports, DNS), Linux security, authentication protocols, and basic Python security scripts.",
            "junior": "1-2 years experience analyzing security logs, configuring firewalls, and conducting vulnerability scans.",
            "mid": "3-5 years experience leading incident response, penetration testing, and security architecture.",
        },
        "competency_expectations": [
            "Identify common web security vulnerabilities (SQL Injection, XSS, CSRF) and explain remediation.",
            "Inspect and analyze network packets and firewall logs for anomalous patterns.",
        ],
        "interview_preparation": {
            "core_technical_areas": [
                "OWASP Top 10 vulnerabilities and secure coding practices.",
                "Network security: Firewalls, VPNs, IDS/IPS, TLS/SSL encryption.",
                "Authentication mechanisms: Password hashing, MFA, OAuth2, and session security.",
            ],
            "coding_topics": [
                "Python script for port scanning and log analysis.",
            ],
            "practical_tasks": [
                "Perform a vulnerability assessment on a mock application and document remediation.",
            ],
        },
        "not_required_yet": [
            "Advanced nation-state cyber warfare forensics.",
        ],
        "career_progression": {
            "Junior Security Analyst": "Monitors security alerts, audits access logs, and conducts basic vulnerability scans.",
            "Cybersecurity Analyst": "Investigates security incidents, hardens infrastructure, and conducts penetration tests.",
            "Security Architect / CISO": "Defines enterprise information security strategy and leads global risk management.",
        },
        "learning_roadmap_phases": [
            {
                "phase": "Phase 1 — Networking & Linux Foundations",
                "focus": "TCP/IP networking, protocols (HTTP, SSH, DNS), Linux system administration, and permissions.",
            },
            {
                "phase": "Phase 2 — Web Security & Cryptography",
                "focus": "OWASP Top 10, symmetric/asymmetric encryption, hashing, and secure authentication.",
            },
            {
                "phase": "Phase 3 — Security Scripting & Auditing",
                "focus": "Python for security automation, log parsing, and vulnerability scanning.",
            },
        ],
        "targeted_project_blueprints": [
            {
                "tier": "Beginner Project",
                "name": "Network Port Scanner & Log Analyzer",
                "skills": ["Python", "Linux", "Authentication", "Git"],
                "description": "Build a Python security tool that scans open network ports, parses server access logs, and flags suspicious IP addresses.",
            },
        ],
        "project_relevance_keywords": ["security", "cybersecurity", "network", "firewall", "vulnerability", "encryption", "auth"],
    },

    # =============================================================
    # 16. UI DEVELOPER
    # =============================================================
    "ui_developer": {
        "role_id": "ROLE-UI-16",
        "role_name": "UI Developer",
        "category": "Web & Mobile Development",
        "icon": "✨",

        "description": "UI Developers focus on the visual design implementation, design systems, interactive animations, and accessibility of client-side web and application interfaces.",
        "overview": (
            "UI and Design Engineers bridge graphic UI/UX design and frontend web engineering. "
            "They specialize in building design systems, reusable CSS component libraries, smooth interactive micro-animations, "
            "and ensuring strict accessibility (a11y) standards across responsive web products."
        ),
        "work_activities": [
            "Building reusable design system components in CSS, Tailwind, and React.",
            "Implementing smooth CSS keyframe animations and interactive micro-interactions.",
            "Auditing web accessibility (WCAG) and optimizing keyboard navigation.",
            "Collaborating closely with UX designers to translate Figma design tokens into code.",
        ],
        "responsibilities": [
            "Develop modular, accessible, and themeable UI component libraries.",
            "Implement responsive layouts and fluid typography across screen breakpoints.",
            "Ensure compliance with WCAG 2.1 AA web accessibility standards.",
            "Maintain design tokens and style guides in code.",
        ],
        "tech_stack_groups": {
            "Frontend Languages": ["HTML5", "CSS3", "JavaScript", "TypeScript"],
            "Design & UX Tools": ["Figma", "FigJam", "Adobe XD", "Canva"],
            "UI Systems & Styling": ["Tailwind CSS", "Design Systems", "Component Design", "Typography", "Color Systems", "UI Animation"],
            "UX Methodologies": ["User Research", "User Flows", "Wireframing", "Prototyping", "Usability Testing", "Information Architecture"],
            "Web Accessibility": ["WCAG", "Keyboard Accessibility", "Screen Reader Compatibility", "Semantic HTML"],
            "Development Tools": ["Git", "GitHub", "Browser DevTools", "Chrome DevTools", "React"],
        },
        "competency_matrix": [
            {
                "category": "Core Frontend & Code",
                "tier": "CORE",
                "skills": ["HTML5", "CSS3", "JavaScript", "Responsive Design"],
                "description": "Translating UI designs into accessible, pixel-perfect semantic HTML, modern CSS, and JavaScript."
            },
            {
                "category": "Design & Prototyping Tools",
                "tier": "CORE",
                "is_alternative_group": True,
                "group_name": "Design Software",
                "alternatives": ["Figma", "FigJam", "Adobe XD", "Canva"],
                "description": "Industry-standard vector design and interactive UI prototyping tools."
            },
            {
                "category": "UX Design Principles",
                "tier": "REQUIRED",
                "skills": ["Wireframing", "Prototyping", "User Research", "User Flows", "Usability Testing", "Information Architecture"],
                "description": "User experience workflows, user journey mapping, wireframing, and usability testing."
            },
            {
                "category": "UI Systems & Interaction",
                "tier": "REQUIRED",
                "skills": ["Design Systems", "Component Design", "Typography", "Color Systems", "UI Animation", "React", "Tailwind CSS"],
                "description": "Reusable design system tokens, typography, component hierarchies, and interactive micro-animations."
            },
            {
                "category": "Web Accessibility (a11y)",
                "tier": "REQUIRED",
                "skills": ["Accessibility", "WCAG", "Keyboard Accessibility", "Screen Reader Compatibility", "Semantic HTML"],
                "description": "Strict compliance with WCAG accessibility guidelines, keyboard navigation, and screen reader compatibility."
            },
            {
                "category": "Version Control",
                "tier": "CORE",
                "skills": ["Git"],
                "description": "Git repository management and version control workflows."
            },
            {
                "category": "Engineering Tools & DevTools",
                "tier": "REQUIRED",
                "skills": ["GitHub", "Browser DevTools", "Chrome DevTools"],
                "description": "Inspecting DOM nodes, CSS computed properties, and responsive breakpoints in browser DevTools."
            },
        ],

        "alternative_skill_clusters": [
            {
                "cluster_name": "Design Tool (any one)",
                "options": ["Figma", "FigJam", "Adobe XD", "Canva", "Sketch"],
                "required_count": 1,
            },
        ],
        "skills_required": {
            "essential": ["HTML5", "CSS3", "Responsive Design", "JavaScript", "Figma", "Git"],
            "common": ["Tailwind CSS", "React", "Wireframing", "Prototyping", "Design Systems", "WCAG"],
            "recommended": ["User Research", "Usability Testing", "UI Animation", "FigJam"],
            "advanced": ["Design System Architecture", "Information Architecture", "Web Performance"],
        },
        "backend_language_flexible": False,
        "education_relevance": "Degree in Computer Science, Design, Human-Computer Interaction, or strong UI portfolio.",
        "experience_expectations": {
            "fresher": "Strong command of semantic HTML5, modern CSS3 (Flexbox/Grid), Tailwind CSS, basic JavaScript, and responsive design.",
            "junior": "1-2 years experience building reusable component libraries and implementing design tokens.",
        },
        "competency_expectations": [
            "Build pixel-perfect responsive components from Figma designs.",
            "Implement smooth CSS animations and ensure keyboard accessibility.",
        ],
        "interview_preparation": {
            "core_technical_areas": [
                "CSS Grid, Flexbox, transitions, transforms, keyframe animations.",
                "Web accessibility (ARIA attributes, semantic HTML, color contrast).",
                "Design systems and component modularity.",
            ],
            "coding_topics": [
                "Building complex responsive UI components (e.g. Accordion, Modal, Multi-step form).",
            ],
            "practical_tasks": [
                "Build a themeable UI component library with dark/light mode toggling.",
            ],
        },
        "not_required_yet": [
            "Backend database scaling and SQL query optimization.",
        ],
        "career_progression": {
            "Junior UI Developer": "Builds styling components and ensures visual fidelity to designs.",
            "Senior Design Engineer": "Architects enterprise design systems and leads UI engineering.",
        },
        "learning_roadmap_phases": [
            {
                "phase": "Phase 1 — Advanced CSS & Responsive Design",
                "focus": "Flexbox, CSS Grid, custom properties, animations, and semantic HTML5.",
            },
            {
                "phase": "Phase 2 — UI Frameworks & Design Tokens",
                "focus": "Tailwind CSS, component architecture in React, and accessibility standards.",
            },
            {
                "phase": "Phase 3 — UI/UX Design Tools & Prototyping",
                "focus": "Figma design systems, auto-layout, interactive prototyping, and component tokens.",
            },
            {
                "phase": "Phase 4 — Web Accessibility & Storybook",
                "focus": "WCAG compliance, keyboard navigation, and building component libraries with Storybook.",
            },
        ],

        "targeted_project_blueprints": [
            {
                "tier": "Beginner Project",
                "name": "Accessible UI Component Library & Showcase",
                "skills": ["HTML5", "CSS3", "Tailwind CSS", "JavaScript", "Git"],
                "description": "Create a collection of accessible, responsive UI components (buttons, modals, cards, tabs) with dark mode toggling.",
            },
        ],
        "project_relevance_keywords": ["ui", "design", "css", "tailwind", "responsive", "frontend", "html", "animation"],
    },

    # =============================================================
    # 17. DATABASE DEVELOPER
    # =============================================================
    "database_developer": {
        "role_id": "ROLE-DB-17",
        "role_name": "Database & ETL Developer",
        "category": "Data & Analytics",
        "icon": "🗄️",
        "description": "Database Developers design, optimize, and maintain relational database schemas, write high-performance stored procedures and SQL queries, and build data pipeline workflows.",
        "overview": (
            "Database Developers specialize in relational and NoSQL data architecture. "
            "They design normalized database schemas, write complex SQL queries, stored procedures, and triggers, "
            "tune query performance using execution plans and indexes, and build automated ETL pipelines for data transformation."
        ),
        "work_activities": [
            "Designing relational database schemas, table structures, and foreign key relationships.",
            "Writing complex SQL queries, stored procedures, views, and data transformation scripts.",
            "Analyzing slow database queries using EXPLAIN plans and configuring indexes.",
            "Automating data extraction, transformation, and loading (ETL) into data warehouses.",
        ],
        "responsibilities": [
            "Design, normalize, and maintain database schemas and table relationships.",
            "Write optimized SQL queries, stored procedures, and triggers.",
            "Configure database indexes and optimize query execution latency.",
            "Develop automated ETL workflows to extract and load data across systems.",
        ],
        "tech_stack_groups": {
            "Databases": ["SQL", "PostgreSQL", "MySQL", "SQLite", "Database Management"],
            "Languages & ETL": ["Python", "Bash", "Git"],
            "Tools": ["pgAdmin", "DBeaver"],
        },
        "skills_required": {
            "essential": ["SQL", "Database Management", "Python", "Git"],
            "common": ["PostgreSQL", "MySQL", "Data Analysis", "REST API"],
            "recommended": ["ETL Pipelines", "Indexing & Query Optimization", "Linux"],
            "advanced": ["Database Replication", "Sharding & Partitioning", "Data Warehousing"],
        },
        "backend_language_flexible": False,
        "education_relevance": "Degree in Computer Science, Information Systems, Data Science, or related discipline.",
        "experience_expectations": {
            "fresher": "Strong command of relational database concepts, table normalization, complex SQL joins, and Python data handling.",
            "junior": "1-2 years experience managing relational databases, writing stored procedures, and query tuning.",
        },
        "competency_expectations": [
            "Design a 3NF normalized database schema for a complex business domain.",
            "Write high-performance SQL queries with aggregations and window functions.",
        ],
        "interview_preparation": {
            "core_technical_areas": [
                "Database normalization (1NF, 2NF, 3NF, BCNF) and denormalization trade-offs.",
                "ACID transaction properties and isolation levels.",
                "B-tree index mechanics, clustered vs. non-clustered indexes, and query execution plans.",
            ],
            "coding_topics": [
                "Complex multi-table SQL queries with joins, CTEs, and window functions.",
            ],
            "practical_tasks": [
                "Design and implement a relational database schema for an e-commerce or school management system.",
            ],
        },
        "not_required_yet": [
            "Multi-datacenter distributed database consensus algorithms.",
        ],
        "career_progression": {
            "Junior Database Developer": "Writes SQL queries, builds table schemas, and assists with data migrations.",
            "Senior Database Architect": "Designs enterprise database infrastructure, tunes query performance, and manages data warehouses.",
        },
        "learning_roadmap_phases": [
            {
                "phase": "Phase 1 — Relational Database Foundations",
                "focus": "Table design, normalization, foreign keys, SQL CRUD, joins, and aggregations.",
            },
            {
                "phase": "Phase 2 — Advanced SQL & Python ETL",
                "focus": "Window functions, subqueries, indexing, and writing Python ETL data extraction scripts.",
            },
        ],
        "targeted_project_blueprints": [
            {
                "tier": "Beginner Project",
                "name": "Relational Database Schema & Query Optimization Case Study",
                "skills": ["SQL", "Database Management", "Python", "Git"],
                "description": "Design a normalized database schema in PostgreSQL/SQLite and write optimized analytical queries with index benchmarks.",
            },
        ],
        "project_relevance_keywords": ["database", "sql", "postgres", "mysql", "etl", "schema", "query", "rdbms"],
    },

    # =============================================================
    # 18. DATA ENGINEER
    # =============================================================
    "data_engineer": {
        "role_id": "ROLE-DE-18",
        "role_name": "Data Engineer",
        "category": "Data & Analytics",
        "icon": "⚡",
        "description": "Data Engineers design, construct, install, test, and maintain complete data architectures, scalable pipelines, ETL workflows, and distributed databases for analytics.",
        "overview": (
            "Data Engineers build and maintain the foundational data platforms and automated data pipelines that power modern analytics and machine learning. "
            "They write robust ETL/ELT pipelines in Python and SQL, orchestrate workflows using Apache Airflow, process large-scale batch and streaming datasets using Spark/PySpark and Kafka, "
            "and manage cloud data warehouses such as Snowflake, BigQuery, and Databricks. They ensure data quality, low pipeline latency, schema evolution, and high availability."
        ),
        "work_activities": [
            "Designing and automating ETL/ELT data pipelines using Python, SQL, and Apache Spark.",
            "Authoring and scheduling workflow DAGs in Apache Airflow or Dagster.",
            "Building streaming ingestion pipelines using Apache Kafka or AWS Kinesis.",
            "Modeling data warehouse schemas and optimizing query performance in Snowflake or BigQuery.",
            "Monitoring pipeline execution latency, data freshness, and data quality validation checks.",
            "Containerizing data services with Docker and deploying infrastructure with CI/CD.",
        ],
        "responsibilities": [
            "Build scalable, fault-tolerant batch and real-time ETL pipelines.",
            "Design normalized relational and dimensional data warehouse schemas.",
            "Orchestrate scheduled data workflows with dependency management and alerting.",
            "Transform unstructured and semi-structured datasets into clean analytical tables.",
            "Ensure high data reliability, lineage tracking, and automated testing across data pipelines.",
            "Collaborate with Data Scientists and BI Analysts to provide clean, query-ready datasets.",
        ],
        "tech_stack_groups": {
            "Languages": ["Python", "SQL", "Scala", "Java"],
            "Processing & ETL": ["Apache Spark", "PySpark", "Pandas", "ETL Pipelines"],
            "Orchestration & Streaming": ["Airflow", "Kafka", "Dagster"],
            "Warehouses & Storage": ["Snowflake", "BigQuery", "Redshift", "Databricks", "S3"],
            "DevOps & Containers": ["Docker", "Git", "Linux", "CI/CD", "AWS"],
        },
        "competency_matrix": [
            {
                "category": "Data Engineering Programming",
                "tier": "CORE",
                "skills": ["Python", "SQL"],
                "description": "Python data transformation scripts, advanced analytical SQL, and stored procedures."
            },
            {
                "category": "ETL & Pipeline Orchestration",
                "tier": "CORE",
                "skills": ["ETL Pipelines", "Airflow", "Database Management"],
                "description": "Building fault-tolerant ETL/ELT pipelines and scheduling workflow DAGs in Apache Airflow."
            },
            {
                "category": "Distributed Computing & Big Data",
                "tier": "REQUIRED",
                "is_alternative_group": True,
                "group_name": "Data Processing Engine",
                "alternatives": ["Apache Spark", "PySpark", "Pandas", "ETL Pipelines"],
                "description": "Distributed data processing and DataFrame transformations using Apache Spark or PySpark."
            },
            {
                "category": "Cloud Data Warehousing",
                "tier": "REQUIRED",
                "is_alternative_group": True,
                "group_name": "Cloud Data Warehouse",
                "alternatives": ["Snowflake", "BigQuery", "Redshift", "Databricks", "PostgreSQL"],
                "description": "Enterprise cloud data warehousing, schema design, and query optimization."
            },
            {
                "category": "DevOps & Containers",
                "tier": "PREFERRED",
                "skills": ["Docker", "Git", "Linux", "CI/CD"],
                "description": "Containerizing data pipelines with Docker, Linux shell scripting, and CI/CD automation."
            },
            {
                "category": "Event Streaming & Real-Time",
                "tier": "OPTIONAL",
                "skills": ["Kafka", "AWS"],
                "description": "High-throughput event streaming with Kafka and AWS cloud infrastructure."
            }
        ],
        "alternative_skill_clusters": [
            {
                "cluster_name": "Data Processing Engine",
                "options": ["Apache Spark", "PySpark", "Pandas", "Apache Flink", "ETL Pipelines"],
                "importance": "Essential",
                "description": "Distributed data processing framework (Apache Spark, PySpark, or Pandas ETL)."
            },
            {
                "cluster_name": "Workflow Orchestration",
                "options": ["Airflow", "Dagster", "Prefect", "CI/CD"],
                "importance": "Common",
                "description": "Pipeline scheduling and workflow DAG orchestrator (Airflow or Dagster)."
            },
            {
                "cluster_name": "Cloud Data Warehouse",
                "options": ["Snowflake", "BigQuery", "Redshift", "Databricks", "PostgreSQL"],
                "importance": "Common",
                "description": "Enterprise cloud data warehousing or query engine."
            }
        ],
        "skills_required": {
            "core": ["Python", "SQL", "ETL Pipelines", "Database Management", "Git"],
            "required": ["Data Processing Engine", "Workflow Orchestration", "Cloud Data Warehouse"],
            "preferred": ["Docker", "Linux", "REST API", "CI/CD", "AWS"],
            "optional": ["Kafka", "Distributed Systems Architecture", "Real-Time Stream Processing", "MLOps"],
            "essential": ["Python", "SQL", "ETL Pipelines", "Database Management", "Git"],
            "common": ["Apache Spark", "Airflow", "Docker", "Linux", "REST API"],
            "recommended": ["Kafka", "Snowflake", "BigQuery", "AWS", "CI/CD"],
            "advanced": ["Distributed Systems Architecture", "Real-Time Stream Processing", "Data Mesh", "MLOps"],
        },
        "backend_language_flexible": False,
        "education_relevance": "Degree in Computer Science, Data Engineering, Information Systems, or strong practical data engineering project portfolio.",
        "experience_expectations": {
            "fresher": "Strong command of Python, SQL, database modeling, basic ETL scripting, and data processing portfolio projects.",
            "junior": "1-2 years experience building production ETL pipelines, scheduling workflows with Airflow, and database performance tuning.",
            "mid": "3-5 years experience including distributed processing with Spark, streaming with Kafka, and cloud data warehouse optimization.",
            "senior": "5+ years experience architecting enterprise data lakes, real-time streaming infrastructure, and data governance frameworks.",
        },
        "competency_expectations": [
            "Write modular Python ETL scripts that extract from REST APIs/databases and load into normalized tables.",
            "Author Airflow DAGs with retries, alerts, and dependency scheduling.",
            "Optimize complex analytical SQL queries using partition pruning, clustering, and indexes.",
            "Process multi-gigabyte datasets efficiently using PySpark or vector operations.",
        ],
        "interview_preparation": {
            "core_technical_areas": [
                "ETL vs. ELT architectures and data pipeline design patterns.",
                "Star schema vs. Snowflake schema dimensional modeling for analytical warehouses.",
                "Partitioning, bucketing, and shuffle optimization in Apache Spark.",
                "Kafka topic partitions, consumer groups, and offset management.",
            ],
            "coding_topics": [
                "Complex analytical SQL queries with window functions, joins, and aggregations.",
                "Writing Python data transformation scripts with error handling and logging.",
            ],
            "practical_tasks": [
                "Build an automated data pipeline extracting public API data, transforming with Pandas/Spark, and loading into PostgreSQL/Snowflake.",
            ],
        },
        "not_required_yet": [
            "Petabyte-scale multi-datacenter data mesh orchestration.",
            "Custom distributed stream processing engine development from scratch.",
        ],
        "career_progression": {
            "Junior Data Engineer": "Writes and maintains ETL scripts, monitors pipeline runs, and creates database views.",
            "Senior Data Architect": "Architects enterprise lakehouses, designs streaming systems, and establishes company-wide data governance.",
        },
        "learning_roadmap_phases": [
            {
                "phase": "Phase 1 — Advanced SQL & Data Modeling",
                "focus": "Complex joins, window functions, CTEs, dimensional modeling, and database indexing.",
            },
            {
                "phase": "Phase 2 — Python ETL & Data Extraction",
                "focus": "Writing modular Python data extraction pipelines, handling JSON/CSV/Parquet, and API integrations.",
            },
            {
                "phase": "Phase 3 — Pipeline Orchestration & Workflow DAGs",
                "focus": "Scheduling and automating pipelines with Apache Airflow, error alerting, and Docker containerization.",
            },
            {
                "phase": "Phase 4 — Distributed Computing with Spark",
                "focus": "Big data processing with PySpark, DataFrame transformations, and partition tuning.",
            },
            {
                "phase": "Phase 5 — Cloud Warehousing & Streaming",
                "focus": "Deploying data warehouses in Snowflake/BigQuery and real-time event streaming with Kafka.",
            },
        ],
        "targeted_project_blueprints": [
            {
                "tier": "Beginner Project",
                "name": "Automated Python API to PostgreSQL ETL Pipeline",
                "skills": ["Python", "SQL", "PostgreSQL", "Git", "ETL Pipelines"],
                "description": "Build an automated Python script that fetches data from an open REST API, validates schemas, and inserts into PostgreSQL.",
            },
            {
                "tier": "Intermediate Project",
                "name": "Airflow-Orchestrated Batch Data Pipeline",
                "skills": ["Airflow", "Python", "SQL", "Docker", "Pandas"],
                "description": "Create an end-to-end Airflow DAG that schedules nightly data extractions, transforms raw records, and writes to a data mart.",
            },
            {
                "tier": "Job-Ready Project",
                "name": "Cloud Data Warehouse & Analytics Pipeline",
                "skills": ["Python", "Apache Spark", "Snowflake", "Airflow", "Docker", "AWS"],
                "description": "Design a complete Lakehouse pipeline processing multi-GB datasets with PySpark and loading into Snowflake with automated tests.",
            },
        ],
        "project_relevance_keywords": ["etl", "pipeline", "spark", "airflow", "kafka", "snowflake", "bigquery", "data engineering", "warehouse", "pyspark"],
    },

    # =============================================================
    # 19. UI/UX DESIGNER
    # =============================================================
    "ui_ux_designer": {
        "role_id": "ROLE-UX-19",
        "role_name": "UI/UX Designer",
        "category": "Design & Product",
        "icon": "✨",
        "description": "UI/UX Designers create intuitive, user-centered digital product experiences. They conduct user research, design wireframes and interactive prototypes, build cohesive design systems, and ensure seamless user journeys.",
        "overview": (
            "UI/UX Designers blend empathetic user research with sleek visual interface design. They conduct user interviews, map personas and user flows, "
            "and create low-fidelity wireframes that evolve into pixel-perfect interactive prototypes in Figma or Adobe XD. They establish comprehensive design systems "
            "featuring reusable UI components, accessible color palettes, and typographic scales compliant with WCAG accessibility standards. They collaborate closely "
            "with product managers and frontend developers to bring digital products to life."
        ),
        "work_activities": [
            "Conducting user interviews, stakeholder sessions, and usability tests to identify user friction points.",
            "Creating user personas, empathy maps, journey maps, and information architecture diagrams.",
            "Drafting low-fidelity wireframes and high-fidelity interactive prototypes in Figma.",
            "Building and maintaining design systems, component libraries, and design tokens.",
            "Conducting usability evaluations and presenting design rationales to engineering and business teams.",
            "Handing off design specs, redlines, and assets to frontend development teams.",
        ],
        "responsibilities": [
            "Design intuitive, responsive, and visually appealing user interfaces for web and mobile.",
            "Conduct generative and evaluative user research to validate design hypotheses.",
            "Create comprehensive wireframes, user flows, and interactive prototypes.",
            "Maintain design system libraries ensuring brand and visual consistency.",
            "Ensure adherence to WCAG 2.1 AA digital accessibility guidelines.",
            "Partner with frontend engineers during design implementation QA reviews.",
        ],
        "tech_stack_groups": {
            "Design & Prototyping Tools": ["Figma", "Adobe XD", "Sketch", "FigJam"],
            "UX Methods": ["User Research", "Wireframing", "Prototyping", "Usability Testing", "Information Architecture"],
            "UI & Visual Systems": ["Design Systems", "Typography", "Color Theory", "Interaction Design", "Responsive Design"],
            "Accessibility & Collaboration": ["WCAG", "Accessible Design", "Design Tokens", "Jira"],
        },
        "competency_matrix": [
            {
                "category": "UX Research & Personas",
                "tier": "CORE",
                "skills": ["User Research", "Usability Testing"],
                "description": "User interviews, persona creation, user journey mapping, and qualitative usability testing."
            },
            {
                "category": "Wireframing & Information Architecture",
                "tier": "CORE",
                "skills": ["Wireframing", "Information Architecture"],
                "description": "Low-fidelity wireframing, site tree navigation, and user flows."
            },
            {
                "category": "Interactive Prototyping & Design Tools",
                "tier": "CORE",
                "is_alternative_group": True,
                "group_name": "Design & Prototyping Software",
                "alternatives": ["Figma", "Adobe XD", "Sketch", "FigJam"],
                "description": "Vector UI design, auto-layout, and interactive clickable prototypes in Figma, Adobe XD, or Sketch."
            },
            {
                "category": "Design Systems & Visual Standards",
                "tier": "CORE",
                "skills": ["Design Systems", "Responsive Design"],
                "description": "Reusable component libraries, design tokens, typography, visual hierarchy, and WCAG accessibility."
            },
            {
                "category": "Product Design & Delivery",
                "tier": "PREFERRED",
                "skills": ["Product Design", "HTML5", "CSS3"],
                "description": "Design validation, stakeholder communication, and developer handoff specs."
            }
        ],
        "alternative_skill_clusters": [
            {
                "cluster_name": "Design & Prototyping Software",
                "options": ["Figma", "Adobe XD", "Sketch", "InVision", "FigJam"],
                "importance": "Essential",
                "description": "Vector UI design and interactive prototyping software (Figma, Adobe XD, or Sketch)."
            }
        ],
        "skills_required": {
            "core": ["Figma", "Wireframing", "Prototyping", "User Research", "Design Systems"],
            "required": ["Usability Testing", "Information Architecture", "Responsive Design"],
            "preferred": ["Product Design", "HTML5", "CSS3", "Adobe XD", "WCAG"],
            "optional": ["Advanced Design Tokens", "Design Ops", "A/B Testing"],
            "essential": ["Figma", "Wireframing", "Prototyping", "User Research", "Design Systems"],
            "common": ["Usability Testing", "Information Architecture", "Interaction Design", "Responsive Design"],
            "recommended": ["Adobe XD", "WCAG", "Product Design", "HTML5", "CSS3"],
            "advanced": ["Advanced Design Tokens", "Design Ops", "Quantitative UX Metrics", "Design Team Leadership"],
        },
        "backend_language_flexible": False,
        "education_relevance": "Degree in Graphic Design, Human-Computer Interaction (HCI), Digital Media, Computer Science, or demonstrated UI/UX design case studies.",
        "experience_expectations": {
            "fresher": "Strong command of Figma, wireframing, prototyping, user-centered design principles, and at least 2 complete design case studies.",
            "junior": "1-2 years experience creating mobile and web interfaces, collaborating with developers, and conducting usability tests.",
            "mid": "3-5 years experience leading end-to-end product design, creating design systems, and conducting multi-stage research.",
            "senior": "5+ years experience establishing enterprise design ops, mentoring designers, and shaping product strategy with executives.",
        },
        "competency_expectations": [
            "Build interactive, clickable high-fidelity prototypes in Figma with auto-layout and components.",
            "Formulate user journey maps and information architecture site trees.",
            "Conduct unmoderated and moderated usability tests and synthesize actionable insights.",
            "Create accessible color systems meeting contrast ratios and WCAG standards.",
        ],
        "interview_preparation": {
            "core_technical_areas": [
                "Walkthrough of an end-to-end UX case study: Problem statement, research, wireframes, iterations, and final prototype.",
                "Design system component architecture: Auto-layout, variants, design tokens, and developer handoff.",
                "Usability testing methodologies: Qualitative vs. quantitative metrics (SUS score, task completion rate).",
                "WCAG accessibility standards and inclusive design practices.",
            ],
            "coding_topics": [
                "App whiteboard design challenge: Solving a product friction problem in real-time.",
            ],
            "practical_tasks": [
                "Redesign a complex onboarding flow or e-commerce checkout interface with Figma prototypes and usability findings.",
            ],
        },
        "not_required_yet": [
            "Managing multi-national cross-platform DesignOps governance councils.",
        ],
        "career_progression": {
            "Junior UI/UX Designer": "Creates screen mockups, builds Figma components, and prepares design handoff specs.",
            "Senior Product Design Lead": "Leads product vision, manages design systems, conducts generative user research, and aligns executive strategy.",
        },
        "learning_roadmap_phases": [
            {
                "phase": "Phase 1 — UX Foundations & User Research",
                "focus": "User empathy, problem framing, conducting user interviews, personas, and user journey mapping.",
            },
            {
                "phase": "Phase 2 — Information Architecture & Wireframing",
                "focus": "Card sorting, site tree architecture, low-fidelity wireframing, and responsive layout grids.",
            },
            {
                "phase": "Phase 3 — Figma Mastery & Interactive Prototyping",
                "focus": "Auto-layout, reusable components, component variants, smart animations, and interactive prototypes.",
            },
            {
                "phase": "Phase 4 — Design Systems & Accessibility (WCAG)",
                "focus": "Design tokens, typographic hierarchies, color contrast compliance, and comprehensive component libraries.",
            },
            {
                "phase": "Phase 5 — Usability Testing & Developer Handoff",
                "focus": "Usability testing protocols, feedback synthesis, redline annotations, and design QA with engineering.",
            },
        ],
        "targeted_project_blueprints": [
            {
                "tier": "Beginner Project",
                "name": "Mobile E-Commerce App Wireframe & Design System",
                "skills": ["Figma", "Wireframing", "Design Systems", "Typography"],
                "description": "Design low-fidelity wireframes and a clean design system for a mobile shopping application.",
            },
            {
                "tier": "Intermediate Project",
                "name": "Healthcare Appointment Scheduling Web App Case Study",
                "skills": ["User Research", "Figma", "Prototyping", "Usability Testing"],
                "description": "Conduct user interviews, design user flows, create interactive Figma prototypes, and run usability tests.",
            },
            {
                "tier": "Job-Ready Project",
                "name": "End-to-End SaaS Dashboard & Design System",
                "skills": ["Figma", "Design Systems", "Prototyping", "WCAG", "Interaction Design"],
                "description": "Create a complete, accessible SaaS dashboard with responsive layouts, comprehensive component libraries, and dev handoff specs.",
            },
        ],
        "project_relevance_keywords": ["figma", "ui", "ux", "wireframe", "prototype", "user research", "design system", "product design", "usability", "adobe xd"],
    },

    # =============================================================
    # 20. ANDROID DEVELOPER
    # =============================================================
    "android_developer": {
        "role_id": "ROLE-AND-20",
        "role_name": "Android Developer",
        "category": "Web & Mobile Development",
        "icon": "🤖",
        "description": "Android Developers build native mobile applications for devices running Android using Kotlin, Java, Android SDK, and Jetpack Compose.",
        "overview": (
            "Android Developers specialize in creating robust, responsive, and intuitive mobile applications for the Android ecosystem. "
            "They write modern Kotlin code, design declarative UI screens using Jetpack Compose or XML layouts, manage Android Activity/Fragment lifecycles, "
            "integrate backend REST APIs with Retrofit/Ktor, store local data using Room/SQLite, and publish apps to the Google Play Store."
        ),
        "work_activities": [
            "Building responsive native Android user interfaces using Jetpack Compose and Material Design.",
            "Consuming backend REST APIs, parsing JSON payloads, and managing offline synchronization.",
            "Persisting structured local data using the Room persistence library and SQLite.",
            "Handling Android lifecycle events, background workers, and push notifications.",
            "Writing unit and UI instrumented tests and deploying release builds to the Google Play Console.",
        ],
        "responsibilities": [
            "Develop native Android applications in Kotlin adhering to modern Android architecture.",
            "Design declarative UI components using Jetpack Compose.",
            "Integrate RESTful network APIs and handle asynchronous coroutine flows.",
            "Implement local data persistence and offline-first storage with Room.",
            "Ensure mobile application performance, low battery consumption, and crash-free sessions.",
        ],
        "tech_stack_groups": {
            "Languages": ["Kotlin", "Java"],
            "Android Frameworks": ["Android SDK", "Android Studio", "Jetpack Compose", "Room"],
            "Networking & Storage": ["REST API", "JSON", "SQLite", "Room"],
            "Tools & Version Control": ["Git", "GitHub", "Gradle"],
        },
        "competency_matrix": [
            {
                "category": "Android Programming Language",
                "tier": "CORE",
                "is_alternative_group": True,
                "group_name": "Android Language",
                "alternatives": ["Kotlin", "Java"],
                "description": "Native Android programming in Kotlin or Java."
            },
            {
                "category": "Android SDK & Architecture",
                "tier": "CORE",
                "skills": ["Android SDK", "Android Studio", "Jetpack Compose"],
                "description": "Android lifecycle, UI rendering with Jetpack Compose, and Android Studio IDE."
            },
            {
                "category": "Networking & APIs",
                "tier": "CORE",
                "skills": ["REST API", "JSON"],
                "description": "Consuming REST APIs, Retrofit/Coroutines, and JSON parsing."
            },
            {
                "category": "Local Persistence",
                "tier": "REQUIRED",
                "skills": ["Room", "SQL"],
                "description": "Room database persistence, entity models, and SQLite data access."
            },
            {
                "category": "Version Control & Tooling",
                "tier": "CORE",
                "skills": ["Git"],
                "description": "Version control, branching, and collaboration."
            }
        ],
        "alternative_skill_clusters": [
            {
                "cluster_name": "Android Language",
                "options": ["Kotlin", "Java"],
                "importance": "Essential",
                "description": "Primary native Android language (Kotlin or Java)."
            }
        ],
        "skills_required": {
            "core": ["Kotlin", "Android SDK", "Android Studio", "Jetpack Compose", "REST API", "Git"],
            "required": ["Room", "JSON", "SQL"],
            "preferred": ["Java", "Software Testing", "CI/CD"],
            "optional": ["Kotlin Multiplatform", "NDK", "Compose Multiplatform"],
            "essential": ["Kotlin", "Android SDK", "Android Studio", "Jetpack Compose", "REST API", "Git"],
            "common": ["Room", "JSON", "SQL"],
            "recommended": ["Java", "Software Testing", "CI/CD"],
            "advanced": ["Kotlin Multiplatform", "NDK", "Compose Multiplatform"],
        },
        "backend_language_flexible": False,
        "education_relevance": "Degree in Computer Science, Software Engineering, or demonstrated Android app portfolio on GitHub/Play Store.",
        "experience_expectations": {
            "fresher": "Strong command of Kotlin, Android Studio, Jetpack Compose UI, REST API consumption, and at least 2 complete Android projects.",
            "junior": "1-2 years experience building production Android apps, managing state with Coroutines/Flow, and publishing to Google Play.",
            "mid": "3-5 years experience architecting Android apps using MVVM/MVI, modularization, and automated testing.",
            "senior": "5+ years experience driving mobile architecture, performance profiling, CI/CD pipelines, and SDK development.",
        },
        "competency_expectations": [
            "Build multi-screen native Android apps with navigation and reactive state in Jetpack Compose.",
            "Implement asynchronous network calls with Kotlin Coroutines and Retrofit.",
            "Persist data locally using Room with migrations and DAO operations.",
        ],
        "interview_preparation": {
            "core_technical_areas": [
                "Android Activity and Fragment lifecycles and ViewModel state retention.",
                "Kotlin Coroutines: Dispatchers, suspend functions, and Flow vs. LiveData.",
                "Jetpack Compose state hoisting, recomposition optimization, and remember keys.",
                "Room database schema design and offline caching architecture.",
            ],
            "coding_topics": [
                "Building a master-detail list screen with Jetpack Compose and API fetching.",
            ],
            "practical_tasks": [
                "Develop an Android news or weather app integrating a public REST API and local Room caching.",
            ],
        },
        "not_required_yet": [
            "Low-level C++ NDK graphics rendering pipelines.",
        ],
        "career_progression": {
            "Junior Android Developer": "Builds UI screens, connects API endpoints, and writes Room database queries.",
            "Senior Android Architect": "Architects multi-module apps, establishes mobile CI/CD pipelines, and directs mobile strategy.",
        },
        "learning_roadmap_phases": [
            {
                "phase": "Phase 1 — Kotlin & Android Studio",
                "focus": "Kotlin syntax, null safety, OOP, Android Studio setup, and basic layouts.",
            },
            {
                "phase": "Phase 2 — Jetpack Compose UI",
                "focus": "Declarative UI components, state management, modifiers, and Material 3 design.",
            },
            {
                "phase": "Phase 3 — Networking & APIs",
                "focus": "Retrofit, Coroutines, Flow, JSON serialization, and error handling.",
            },
            {
                "phase": "Phase 4 — Local Storage with Room",
                "focus": "Room entities, DAOs, TypeConverters, and repository design patterns.",
            },
        ],
        "targeted_project_blueprints": [
            {
                "tier": "Beginner Project",
                "name": "Native Android Habit Tracker with Room Persistence",
                "skills": ["Kotlin", "Android SDK", "Room", "Jetpack Compose", "Git"],
                "description": "Build an Android habit tracking application with Jetpack Compose UI and local Room database persistence.",
            },
            {
                "tier": "Intermediate Project",
                "name": "Live News & Weather App with Retrofit",
                "skills": ["Kotlin", "REST API", "Android Studio", "Jetpack Compose", "JSON"],
                "description": "Develop an Android app that fetches live articles from a REST API, supports category filtering, and caches offline.",
            },
        ],
        "project_relevance_keywords": ["android", "kotlin", "jetpack compose", "room", "android studio", "mobile", "app"],
    },

    # =============================================================
    # 21. IOS DEVELOPER
    # =============================================================
    "ios_developer": {
        "role_id": "ROLE-IOS-21",
        "role_name": "iOS Developer",
        "category": "Web & Mobile Development",
        "icon": "🍎",
        "description": "iOS Developers design and build native applications for Apple iOS devices using Swift, SwiftUI, UIKit, Core Data, and Xcode.",
        "overview": (
            "iOS Developers specialize in crafting elegant, responsive native mobile applications for iPhone and iPad. "
            "They write clean Swift code, build declarative user interfaces with SwiftUI and UIKit, manage Apple app lifecycles, "
            "connect to backend REST APIs using URLSession, store local data using Core Data or SwiftData, and publish apps to the Apple App Store."
        ),
        "work_activities": [
            "Designing declarative iOS interfaces using SwiftUI and Apple Human Interface Guidelines.",
            "Connecting iOS applications to backend REST APIs using URLSession and Codable.",
            "Managing local data persistence and object graphs using Core Data or SwiftData.",
            "Testing iOS apps for memory leaks, smooth scrolling (60/120 FPS), and accessibility.",
            "Building release archives and publishing apps to Apple TestFlight and the App Store.",
        ],
        "responsibilities": [
            "Develop native iOS applications in Swift adhering to Apple design standards.",
            "Build modern user interfaces using SwiftUI and UIKit.",
            "Integrate RESTful network APIs and handle asynchronous async/await concurrency.",
            "Implement local data storage and offline caching using Core Data.",
            "Maintain app performance, clean memory management (ARC), and crash-free sessions.",
        ],
        "tech_stack_groups": {
            "Languages": ["Swift", "Objective-C"],
            "iOS Frameworks": ["iOS SDK", "Xcode", "SwiftUI", "UIKit", "Core Data"],
            "Networking & Storage": ["REST API", "JSON", "Core Data", "URLSession"],
            "Tools": ["Git", "GitHub", "TestFlight", "Cocoapods / SPM"],
        },
        "competency_matrix": [
            {
                "category": "iOS Programming Language",
                "tier": "CORE",
                "skills": ["Swift"],
                "description": "Modern Swift programming, optionals, protocols, closures, and async/await concurrency."
            },
            {
                "category": "iOS SDK & UI Frameworks",
                "tier": "CORE",
                "skills": ["iOS SDK", "Xcode", "SwiftUI", "UIKit"],
                "description": "SwiftUI declarative layouts, UIKit compatibility, Xcode IDE, and Apple Human Interface Guidelines."
            },
            {
                "category": "Networking & APIs",
                "tier": "CORE",
                "skills": ["REST API", "JSON"],
                "description": "URLSession networking, Codable JSON parsing, and async error handling."
            },
            {
                "category": "Local Persistence",
                "tier": "REQUIRED",
                "skills": ["Core Data"],
                "description": "Core Data object graphs, entity relationships, and local data persistence."
            },
            {
                "category": "Version Control & Tooling",
                "tier": "CORE",
                "skills": ["Git"],
                "description": "Version control, branching, and repository collaboration."
            }
        ],
        "alternative_skill_clusters": [],
        "skills_required": {
            "core": ["Swift", "iOS SDK", "Xcode", "SwiftUI", "REST API", "Git"],
            "required": ["Core Data", "UIKit", "JSON"],
            "preferred": ["Software Testing", "CI/CD", "SwiftData"],
            "optional": ["VisionOS", "Combine", "Metal"],
            "essential": ["Swift", "iOS SDK", "Xcode", "SwiftUI", "REST API", "Git"],
            "common": ["Core Data", "UIKit", "JSON"],
            "recommended": ["Software Testing", "CI/CD", "SwiftData"],
            "advanced": ["VisionOS", "Combine", "Metal"],
        },
        "backend_language_flexible": False,
        "education_relevance": "Degree in Computer Science, Software Engineering, or demonstrated native iOS app portfolio on GitHub/App Store.",
        "experience_expectations": {
            "fresher": "Solid command of Swift syntax, SwiftUI views, Xcode environment, REST API integration, and at least 2 complete iOS apps.",
            "junior": "1-2 years experience delivering production iOS apps, managing state with @StateObject/@Observable, and App Store submission.",
            "mid": "3-5 years experience architecting iOS applications using MVVM, modular SPM packages, and Core Data migrations.",
            "senior": "5+ years experience establishing enterprise mobile frameworks, CI/CD pipelines, and high-performance rendering.",
        },
        "competency_expectations": [
            "Build native iOS apps with SwiftUI featuring clean view hierarchies and navigation stacks.",
            "Integrate RESTful web APIs using async/await and Codable JSON parsing.",
            "Persist offline app data with Core Data.",
        ],
        "interview_preparation": {
            "core_technical_areas": [
                "Automatic Reference Counting (ARC), strong vs. weak references, and memory retain cycles.",
                "SwiftUI state management: @State, @Binding, @ObservedObject, and the new @Observable macro.",
                "Concurrency in Swift: async/await, Task groups, and MainActor isolation.",
                "Core Data vs. SwiftData persistent storage architecture.",
            ],
            "coding_topics": [
                "Implementing a responsive SwiftUI list screen with search filtering and image caching.",
            ],
            "practical_tasks": [
                "Build an iOS crypto or stock tracker app with live API fetching and Core Data favorites.",
            ],
        },
        "not_required_yet": [
            "Custom Metal shader GPU programming.",
        ],
        "career_progression": {
            "Junior iOS Developer": "Builds SwiftUI views, connects API endpoints, and manages local Core Data models.",
            "Senior iOS Architect": "Architects large-scale apps, establishes mobile DevOps pipelines, and directs mobile strategy.",
        },
        "learning_roadmap_phases": [
            {
                "phase": "Phase 1 — Swift & Xcode Foundations",
                "focus": "Swift language, optionals, protocols, structs, classes, and Xcode navigation.",
            },
            {
                "phase": "Phase 2 — SwiftUI Declarative Layouts",
                "focus": "Views, modifiers, navigation stacks, animations, and Human Interface Guidelines.",
            },
            {
                "phase": "Phase 3 — Async Networking & APIs",
                "focus": "URLSession, async/await, Codable parsing, and image downloading.",
            },
            {
                "phase": "Phase 4 — Local Storage with Core Data",
                "focus": "Core Data entities, NSManagedObjectContext, and repository patterns.",
            },
        ],
        "targeted_project_blueprints": [
            {
                "tier": "Beginner Project",
                "name": "Native SwiftUI Task & Note Manager",
                "skills": ["Swift", "SwiftUI", "Core Data", "Xcode", "Git"],
                "description": "Create an elegant iOS task management app with SwiftUI and Core Data local persistence.",
            },
            {
                "tier": "Intermediate Project",
                "name": "Live Stock & Crypto Market Tracker",
                "skills": ["Swift", "SwiftUI", "REST API", "JSON", "Xcode"],
                "description": "Develop an iOS application that streams financial data from an API, renders charts, and caches watchlists.",
            },
        ],
        "project_relevance_keywords": ["ios", "swift", "swiftui", "xcode", "core data", "uikit", "apple", "mobile"],
    },

    # =============================================================
    # 22. APP DEVELOPER  (cross-platform & native mobile)
    # =============================================================
    "app_developer": {
        "role_id": "ROLE-APP-22",
        "role_name": "App Developer",
        "category": "Mobile & Cross-Platform Development",
        "icon": "📱",
        "description": (
            "App Developers design, develop, and publish mobile applications for Android, iOS, or both platforms "
            "using native or cross-platform frameworks. They build intuitive UIs, integrate REST APIs, manage "
            "local/cloud data, handle push notifications, and publish apps to the Google Play Store and Apple App Store."
        ),
        "overview": (
            "App Developers specialise in creating rich mobile experiences. Cross-platform engineers use React Native "
            "or Flutter/Dart to target Android and iOS from a single codebase. Native engineers prefer Kotlin + Jetpack "
            "Compose (Android) or Swift + SwiftUI (iOS). All App Developers work with REST APIs, asynchronous state "
            "management, device sensors, offline storage, and store submission pipelines."
        ),
        "work_activities": [
            "Designing and implementing mobile UIs using React Native, Flutter, Jetpack Compose, or SwiftUI.",
            "Integrating backend REST APIs, handling JSON serialization and asynchronous data flows.",
            "Managing application state with Redux, Provider, Riverpod, or ViewModel patterns.",
            "Implementing local storage using SQLite, Room, Core Data, or AsyncStorage.",
            "Publishing apps to Google Play Store and Apple App Store, handling signing and release pipelines.",
            "Debugging device-specific layout issues, optimising frame rate, and reducing APK/IPA size.",
        ],
        "responsibilities": [
            "Build cross-platform or native mobile applications.",
            "Integrate REST APIs and handle asynchronous state transitions.",
            "Implement responsive mobile layouts across different screen sizes.",
            "Set up push notifications, deep links, and authentication flows.",
            "Write unit and widget/UI tests, and publish releases to app stores.",
            "Collaborate with backend engineers and UI/UX designers.",
        ],
        "tech_stack_groups": {
            "Cross-Platform Frameworks": ["React Native", "Flutter", "Dart"],
            "Native Android": ["Kotlin", "Android SDK", "Jetpack Compose", "Android Studio"],
            "Native iOS": ["Swift", "SwiftUI", "UIKit", "Xcode"],
            "Languages": ["JavaScript", "TypeScript", "Dart", "Kotlin", "Swift"],
            "State Management": ["Redux", "Provider", "Riverpod", "MobX"],
            "APIs & Storage": ["REST APIs", "Firebase", "SQLite", "Room", "Core Data", "AsyncStorage"],
            "DevOps & Tooling": ["Git", "GitHub", "Firebase", "Play Store", "App Store"],
        },
        "competency_matrix": [
            {
                "category": "Mobile Frameworks",
                "tier": "CORE",
                "skills": ["React Native", "Flutter", "Android SDK", "Swift", "Kotlin"],
                "description": "At least one cross-platform or native mobile framework is required.",
            },
            {
                "category": "Programming Languages",
                "tier": "CORE",
                "skills": ["JavaScript", "TypeScript", "Dart", "Kotlin", "Swift"],
                "description": "A mobile-relevant programming language: JS/TS for React Native, Dart for Flutter, Kotlin for Android, Swift for iOS.",
            },
            {
                "category": "Mobile UI",
                "tier": "REQUIRED",
                "skills": ["Jetpack Compose", "SwiftUI", "UIKit", "Responsive Mobile UI", "Mobile Layouts"],
                "description": "Building native or declarative mobile user interfaces.",
            },
            {
                "category": "State Management",
                "tier": "REQUIRED",
                "skills": ["Redux", "Provider", "Riverpod", "MobX", "ViewModel", "State Management"],
                "description": "Managing UI state and data flows in mobile applications.",
            },
            {
                "category": "APIs & Networking",
                "tier": "REQUIRED",
                "skills": ["REST APIs", "JSON", "Axios", "HTTP Networking", "API Integration"],
                "description": "Consuming backend REST APIs and handling asynchronous data.",
            },
            {
                "category": "Local Storage & Databases",
                "tier": "IMPORTANT",
                "skills": ["SQLite", "Room", "Core Data", "AsyncStorage", "Firebase Firestore", "Realm"],
                "description": "Persisting data locally on the mobile device.",
            },
            {
                "category": "Authentication & Services",
                "tier": "IMPORTANT",
                "skills": ["Firebase Authentication", "OAuth2", "JWT Authentication", "Push Notifications", "Deep Linking"],
                "description": "Implementing user authentication, notifications, and deep links.",
            },
            {
                "category": "Development Tooling",
                "tier": "IMPORTANT",
                "skills": ["Git", "GitHub", "Android Studio", "Xcode", "VS Code", "Expo"],
                "description": "Essential development environment tooling for mobile projects.",
            },
            {
                "category": "Store Deployment",
                "tier": "NICE_TO_HAVE",
                "skills": ["Google Play Store", "Apple App Store", "App Signing", "CI/CD", "Fastlane"],
                "description": "Publishing apps and managing release pipelines.",
            },
            {
                "category": "Testing",
                "tier": "NICE_TO_HAVE",
                "skills": ["Jest", "Detox", "Flutter Test", "Espresso", "XCTest"],
                "description": "Mobile unit, widget, and end-to-end testing.",
            },
        ],
        "alternative_skill_clusters": [
            {
                "cluster_name": "Mobile Framework (any one)",
                "options": ["React Native", "Flutter", "Android SDK", "Swift", "Kotlin"],
                "required_count": 1,
            },
            {
                "cluster_name": "State Management (any one)",
                "options": ["Redux", "Provider", "Riverpod", "MobX", "ViewModel", "Context API"],
                "required_count": 1,
            },
        ],
        "skills_required": {
            "essential": ["React Native or Flutter or Kotlin or Swift", "JavaScript or TypeScript or Dart or Kotlin", "REST APIs", "Git"],
            "common": ["State Management", "Local Storage", "Mobile UI", "JSON"],
            "recommended": ["Firebase", "Push Notifications", "Authentication", "App Store Deployment"],
            "advanced": ["CI/CD Mobile Pipelines", "Performance Profiling", "Accessibility", "App Security"],
        },
        "backend_language_flexible": False,
        "education_relevance": "B.Tech / B.Sc Computer Science preferred; strong portfolio of published apps is highly valued.",
        "experience_expectations": "2+ mobile projects (personal, academic, or professional) with store submissions preferred.",
        "competency_expectations": [
            "Build a cross-platform or native mobile app from scratch.",
            "Integrate REST APIs with proper loading and error state handling.",
            "Implement persistent local storage using SQLite or equivalent.",
            "Publish an app to the Play Store or App Store.",
        ],
        "interview_preparation": {
            "topics": [
                "React Native architecture vs Flutter vs native",
                "State management patterns (Redux, Provider, Riverpod)",
                "Mobile navigation (React Navigation, Navigator)",
                "Handling async operations and API calls",
                "App lifecycle and background tasks",
                "Mobile performance optimisation",
                "App store review guidelines and signing",
            ],
            "coding_exercises": [
                "Build a FlatList / ListView with API data.",
                "Implement offline caching with SQLite.",
                "Handle authentication flow with JWT tokens.",
            ],
        },
        "not_required_yet": [
            "Advanced ARKit / ARCore development",
            "Native module bridging (C++ / Objective-C)",
            "ML on-device with Core ML / TensorFlow Lite",
        ],
        "career_progression": {
            "0_6_months": "Build 2-3 cross-platform apps (React Native or Flutter) with API integration.",
            "6_12_months": "Publish a polished app on Google Play or App Store with authentication.",
            "1_2_years": "Contribute to a production mobile app team; explore native Android/iOS skills.",
            "2_plus_years": "Lead mobile development for a product team; set up CI/CD and automated test pipelines.",
        },
        "learning_roadmap_phases": [
            {
                "phase": "Phase 1 — Choose a Framework",
                "focus": "Start with React Native (if you know JS/React) or Flutter (Dart). Build your first counter/todo app.",
            },
            {
                "phase": "Phase 2 — State & Navigation",
                "focus": "Add state management (Redux Toolkit or Provider) and multi-screen navigation.",
            },
            {
                "phase": "Phase 3 — APIs & Authentication",
                "focus": "Connect to a REST API, handle login/JWT tokens, and manage async loading states.",
            },
            {
                "phase": "Phase 4 — Persistence & Publishing",
                "focus": "Add SQLite offline storage; prepare app for Play Store / App Store submission.",
            },
        ],
        "targeted_project_blueprints": [
            {
                "tier": "Beginner Project",
                "name": "Cross-Platform To-Do App",
                "skills": ["React Native", "AsyncStorage", "React Navigation", "Git"],
                "description": "Build a React Native (or Flutter) task manager with local persistence and multi-screen navigation.",
            },
            {
                "tier": "Intermediate Project",
                "name": "Weather & News Feed App",
                "skills": ["React Native", "REST APIs", "Redux", "Push Notifications", "Git"],
                "description": "A production-quality app consuming two public APIs, with push notifications and offline caching.",
            },
        ],
        "project_relevance_keywords": [
            "react native", "flutter", "android", "ios", "mobile", "dart", "kotlin", "swift",
            "expo", "play store", "app store", "firebase", "mobile ui", "cross-platform",
        ],
    },
}


# ===========================================================
# MANDATORY 10-ROLE EVALUATION SET
# The recommender MUST always evaluate and return ALL of these
# roles regardless of match score.
# ===========================================================
MANDATORY_10_ROLE_IDS: List[str] = [
    "web_developer",        # ROLE-WD-10
    "app_developer",        # ROLE-APP-22
    "ui_developer",         # ROLE-UI-16  (UI/UX Developer)
    "frontend_developer",   # ROLE-FE-01
    "backend_developer",    # ROLE-BE-02
    "full_stack_developer", # ROLE-FS-03
    "software_engineer",    # ROLE-SE-04  (Software Developer)
    "data_analyst",         # ROLE-DA-06
    "data_scientist",       # ROLE-DS-08
    "data_engineer",        # ROLE-DE-18
]

# Display names for the mandatory 10 roles (canonical)
MANDATORY_10_DISPLAY_NAMES: Dict[str, str] = {
    "web_developer": "Web Developer",
    "app_developer": "App Developer",
    "ui_developer": "UI/UX Developer",
    "frontend_developer": "Frontend Developer",
    "backend_developer": "Backend Developer",
    "full_stack_developer": "Full Stack Developer",
    "software_engineer": "Software Developer",
    "data_analyst": "Data Analyst",
    "data_scientist": "Data Scientist",
    "data_engineer": "Data Engineer",
}


def get_all_job_roles() -> List[Dict[str, Any]]:
    """Retrieve all structured job roles from the knowledge base."""
    return list(JOB_ROLES_KNOWLEDGE_BASE.values())


def get_job_role_by_id(role_id_or_name: str) -> Optional[Dict[str, Any]]:
    """Lookup job role by exact ID, key name, or normalized role name."""
    if not role_id_or_name:
        return None
    raw = role_id_or_name.strip().lower()
    norm = raw.replace(" ", "_").replace("-", "_").replace("/", "_")
    if norm in JOB_ROLES_KNOWLEDGE_BASE:
        return JOB_ROLES_KNOWLEDGE_BASE[norm]
    if raw in JOB_ROLES_KNOWLEDGE_BASE:
        return JOB_ROLES_KNOWLEDGE_BASE[raw]
    for key, data in JOB_ROLES_KNOWLEDGE_BASE.items():
        rid = data.get("role_id", "").lower()
        rname = data.get("role_name", "").lower()
        if rid == raw or rid.replace("-", "_") == norm or rname == raw or rname.replace(" ", "_") == norm:
            return data
    
    # Common aliases mapping
    alias_map = {
        "ui_ux_developer": "ui_developer",
        "ui_ux_engineer": "ui_developer",
        "ui_developer": "ui_developer",
        "ui_designer": "ui_ux_designer",
        "ux_designer": "ui_ux_designer",
        "fullstack_developer": "full_stack_developer",
        "software_developer": "software_engineer",
    }
    if norm in alias_map:
        return JOB_ROLES_KNOWLEDGE_BASE.get(alias_map[norm])
    return None
