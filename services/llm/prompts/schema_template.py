"""JSON output schema template for LLM extraction prompts.

Defines the exact JSON structure the LLM must return.
This is injected into both Pass 1 (extraction) and Pass 2 (validation) prompts.
"""

EXTRACTION_JSON_SCHEMA = """{
  "personal_info": {
    "full_name": null,
    "email": null,
    "phone": null,
    "location": null,
    "address": null,
    "date_of_birth": null,
    "age": null,
    "linkedin": null,
    "github": null,
    "leetcode": null,
    "kaggle": null,
    "portfolio": null,
    "personal_website": null,
    "professional_title": null,
    "other_profile_links": []
  },

  "professional_summary": {
    "heading": "Professional Summary",
    "text": null,
    "source_text": null,
    "source": "ocr"
  },

  "skills": {
    "technical": [],
    "programming_languages": [],
    "frameworks": [],
    "libraries": [],
    "databases": [],
    "cloud": [],
    "platforms": [],
    "tools": [],
    "ui_ux_tools": [],
    "office_productivity": [],
    "soft_skills": [],
    "business_skills": [],
    "other": []
  },

  "experience": {
    "full_time": [
      {
        "title": null,
        "company": null,
        "location": null,
        "start_date": null,
        "end_date": null,
        "duration": null,
        "responsibilities": [],
        "technologies": [],
        "source_text": null
      }
    ]
  },

  "internships": [
    {
      "role": null,
      "company": null,
      "location": null,
      "start_date": null,
      "end_date": null,
      "duration": null,
      "responsibilities": [],
      "technologies": [],
      "source_text": null
    }
  ],

  "education": [
    {
      "qualification_type": null,
      "degree": null,
      "field_of_study": null,
      "specialization": null,
      "institution": null,
      "university": null,
      "location": null,
      "start_year": null,
      "end_year": null,
      "expected_year": null,
      "status": null,
      "score_type": null,
      "score": null,
      "grade": null,
      "percentage": null,
      "gpa": null,
      "cgpa": null,
      "stream": null,
      "canonical_education_category": null,
      "education_classification": null,
      "details": [],
      "source_text": null
    }
  ],

  "projects": [
    {
      "name": null,
      "description": null,
      "technologies": [],
      "programming_languages": [],
      "url": null,
      "details": [],
      "source_text": null
    }
  ],

  "certifications": [
    {
      "name": null,
      "issuer": null,
      "date": null,
      "credential_id": null,
      "url": null,
      "details": null,
      "source_text": null
    }
  ],

  "awards_achievements": [],

  "publications": [
    {
      "title": null,
      "authors": [],
      "conference": null,
      "journal": null,
      "publisher": null,
      "date": null,
      "year": null,
      "description": null,
      "details": [],
      "url": null,
      "source_text": null
    }
  ],

  "additional_qualifications": [],

  "languages": [],

  "interests": [],

  "strengths": [],

  "declaration": {
    "text": null,
    "source_text": null
  },

  "signature": {
    "present": false,
    "text": null
  },

  "other_sections": []
}"""


PUBLICATION_RULES = """
PUBLICATION EXTRACTION RULES:
- Capture EVERY research publication, paper, conference proceeding, journal article, or academic manuscript.
- Preserve: title, authors, conference (if conference), journal (if journal), publisher (if publisher or organizing body), date, year, description, and all details bullets.
- NEVER omit publication details or bullet points. Preserve full bullet point text in details[].
- If publication venue is a conference, populate conference.
- If publication venue is a journal, populate journal.
- If publisher or organizing body is mentioned, populate publisher.
- Preserve exact wording and dates.
"""


EDUCATION_STATUS_RULES = """
IMPORTANT EDUCATION EXTRACTION RULES (STRICTLY ENFORCE):
1. Every distinct educational qualification/level MUST be represented as a separate object in the `education` array.
2. DO NOT merge different education levels just because they were completed at the same institution.
3. The following are separate education records:
   - Undergraduate / Bachelor's degree (e.g. B.Sc., B.Tech, B.E., B.Com, BBA, BCA)
   - Higher Secondary / HSC / 12th Standard / Class XII
   - Secondary / SSLC / 10th Standard / Class X
   - Diploma / Polytechnic
   - Master's degree (e.g. M.Sc., M.Tech, M.E., MBA, MCA)
   - PhD / Doctorate
   - Any other distinct academic qualification
4. If the same school appears for both HSC and SSLC, create TWO separate education objects with the same `institution` value.
5. NEVER put a distinct qualification such as "SSLC: 86%" into `details[]` if it represents a separate academic level.
6. For example, if the resume contains:
   "Little Flower Matric Hr. Sec. School
    Higher Secondary: 77%
    2023
    SSLC: 86%"
   this MUST be extracted as TWO education records:
   Record 1:
   qualification_type: "Higher Secondary"
   degree: "Higher Secondary"
   institution: "Little Flower Matric Hr. Sec. School"
   end_year: "2023"
   percentage: "77%"
   status: "Completed"

   Record 2:
   qualification_type: "Secondary"
   degree: "SSLC"
   field_of_study: null
   institution: "Little Flower Matric Hr. Sec. School"
   percentage: "86%"
   status: "Completed"

7. SSLC means Secondary School Leaving Certificate / 10th Standard. Treat it as a separate school-level education record.
8. HSC means Higher Secondary / 12th Standard. Treat it as a separate school-level education record.
9. The same institution name MUST NOT be used as a reason to merge records.
10. `details[]` is ONLY for additional information that does NOT represent another qualification. Do not store another academic level, degree, diploma, HSC, SSLC, 10th, or 12th qualification inside `details[]`.
11. Do not invent missing information. If a field is not explicitly present in the resume, return null.
12. Do not change, normalize, infer, or hallucinate percentages, years, institution names, degree names, or qualification levels.
13. Preserve the original extracted values as faithfully as possible.
14. The number of education objects must equal the number of distinct academic qualifications explicitly present in the resume.
15. STATUS RULES:
   - status = "Completed" ONLY when source explicitly says: "Completed", "Graduated", "Passed", "Degree awarded", "Class of YYYY" (past year), or the end year is clearly in the past AND completion is implied by context.
   - status = "Currently Pursuing" when source says: "Expected", "Pursuing", "Currently studying", "Final year", "Present", or end year is in the future (e.g. 2025, 2026, 2027 from today's perspective).
   - status = "Currently Pursuing" for date ranges like "2024–2027" or "2024-2027" because the end year 2027 is in the future.
   - status = "Not specified" when NO year is mentioned and NO completion/pursuing language exists.
   - NEVER default to "Completed" just because a degree name is present with no year.
   - NEVER mark a future year as Completed.
"""

SKILL_RULES = """
SKILLS EXTRACTION RULES (CRITICAL — EVIDENCE-BASED ONLY):
- MENTIONED TECHNOLOGY != CONFIRMED SKILL.
- NEVER extract a technology mentioned ONLY inside career objectives or aspiration sentences (e.g. "I want to become a Java developer", "Seeking a Python developer role", "Aspiring React developer", "Currently learning Python"). These are aspirations, NOT confirmed skills.
- NEVER extract a technology from explicit negative mentions (e.g. "I did not work with Java", "Never used C++").
- Extract skills supported by actual evidence: dedicated Skills sections, or active usage in Experience/Projects/Certifications ("Developed APIs using Python and Flask").
- Controlled Canonical Taxonomy:
  * programming_languages: Python, Java, C, C++, C#, JavaScript, TypeScript, Go, Rust, Ruby, PHP, Kotlin, Swift, Dart, R, Scala, Perl, MATLAB, SQL, PL/SQL, T-SQL, Bash, Shell Scripting, Assembly. (NOTE: SQL and PL/SQL belong in programming_languages, NOT databases).
  * databases: MySQL, PostgreSQL, Oracle Database, Microsoft SQL Server, MongoDB, SQLite, Redis, Cassandra, DynamoDB, MariaDB, Firebase Firestore, Neo4j, CouchDB, Elasticsearch, Snowflake, Amazon Redshift.
  * frameworks: React, Angular, Vue.js, Django, Flask, FastAPI, Spring, Spring Boot, Express.js, Next.js, Nuxt.js, Svelte, Laravel, Ruby on Rails, .NET, ASP.NET, Flutter, React Native, Tailwind CSS, Bootstrap, Django REST Framework (DRF).
  * libraries: NumPy, Pandas, Matplotlib, Seaborn, Plotly, Scikit-learn, TensorFlow, PyTorch, Keras, OpenCV, jQuery, Requests, BeautifulSoup, LangChain, Three.js, Framer Motion.
  * ui_ux_tools: Figma, Adobe XD, Sketch, Adobe Photoshop, Adobe Illustrator, Canva, Framer, InVision, Balsamiq, Axure.
  * office_productivity: Microsoft Excel, Microsoft Word, Microsoft PowerPoint, Microsoft Office, Google Docs, Google Sheets, Google Slides, Microsoft Outlook.
  * tools: Git, GitHub, GitLab, Docker, Kubernetes, Jenkins, Postman, VS Code, IntelliJ IDEA, Eclipse, Jira, Power BI, Tableau, Tally, SPSS, Basic Computer Knowledge.
  * cloud: AWS, Microsoft Azure, Google Cloud, Oracle Cloud, IBM Cloud, DigitalOcean, Heroku, Vercel, Netlify.
  * platforms: Android, iOS, Windows, Linux, Unix, macOS, Salesforce, WordPress, Shopify.
  * soft_skills: Communication, Leadership, Problem Solving, Teamwork, Time Management, Adaptability, Quick Learner.
  * business_skills: Marketing Analytics, Competitor Analysis, Business Process Improvement, Accounting, Finance.
- For combined expressions: "MS Office (Word, Excel, PowerPoint)" → extract: "Microsoft Word", "Microsoft Excel", "Microsoft PowerPoint" into office_productivity.
- Each skill must appear in its single most appropriate canonical category. Do NOT duplicate across categories.
- NEVER put soft skills in programming_languages/technical.
- NEVER hallucinate a skill not present in the source.
"""

LOCATION_RULES = """
LOCATION EXTRACTION RULES:
- Extract the location EXACTLY as it appears in the resume header/contact area.
- "Chennai 600128" → location = "Chennai 600128" (preserve the postal code).
- "Chennai, Tamil Nadu, India" → location = "Chennai, Tamil Nadu, India" (preserve fully).
- Do NOT infer state/country if not present in source.
- Do NOT add information to location that is not in the source.
- Location appears near: candidate name, phone, email, in the header block.
"""
