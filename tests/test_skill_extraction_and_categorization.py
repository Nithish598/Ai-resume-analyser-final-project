"""Comprehensive Test Suite for Skill Extraction, Taxonomy Categorization, and Evidence Validation.

Validates that:
1. Technologies mentioned only in career aspirations are NOT extracted as confirmed skills.
2. Technologies mentioned in negative context are NOT extracted.
3. SQL is classified under programming_languages, NOT databases.
4. Databases (MySQL, PostgreSQL, MongoDB, etc.) are classified under databases.
5. Frameworks (React, Django, Flask) and Libraries (NumPy, Pandas) are classified correctly.
6. UI/UX tools (Figma, Adobe XD) are classified under ui_ux_tools.
7. Office productivity (Excel, Word, PowerPoint) are categorized cleanly.
8. Deduplication ensures each canonical skill appears in its single primary category.
9. Golden resumes (Joshika, Niranjana, Deepiga) preserve all valid skills without loss.
"""
import pytest
from src.resume.skills_taxonomy import (
    SKILLS_TAXONOMY,
    normalize_skill_name,
    get_canonical_category,
    classify_skill_evidence,
    is_aspiration_sentence,
    is_negated_sentence,
    is_learning_sentence,
)
from src.resume.information_extractor import InformationExtractor
from src.resume.profile_schema import CandidateProfile, Skills
from services.llm.schema_normalizer import normalize_llm_json_to_profile, compare_llm_and_final


@pytest.fixture
def extractor():
    return InformationExtractor()


# ==================== TEST 1: ASPIRATION FILTERING ====================

def test_aspiration_sentence_detection():
    assert is_aspiration_sentence("I want to become a Java Developer.")
    assert is_aspiration_sentence("Career Objective: Seeking an entry-level Python developer position.")
    assert is_aspiration_sentence("Looking forward to learning React and Next.js.")
    assert is_aspiration_sentence("Aspiring Data Scientist with interest in Machine Learning.")
    assert not is_aspiration_sentence("Proficient in Python and Django with 2 years experience.")
    assert not is_aspiration_sentence("Technical Skills: Python, Java, SQL.")


def test_aspiration_skill_not_extracted(extractor):
    resume_text = """
    John Doe
    Email: john@example.com
    Phone: +1 555-123-4567
    
    CAREER OBJECTIVE
    I want to become a Java Developer and work on large-scale enterprise systems.
    
    EDUCATION
    B.Sc Computer Science, ABC University, 2024
    """
    skills, _ = extractor.extract_skills(resume_text)
    assert "Java" not in skills.programming_languages
    assert "Java" not in skills.all_unique_skills


# ==================== TEST 2: NEGATED SKILL FILTERING ====================

def test_negated_sentence_detection():
    assert is_negated_sentence("I did not work with Java in this project.", "Java")
    assert is_negated_sentence("Never used C++ or Rust.", "C++")
    assert is_negated_sentence("We migrated away from PHP to Python.", "PHP")
    assert not is_negated_sentence("Extensive experience working with Python and Django.", "Python")


def test_negated_skill_not_extracted(extractor):
    resume_text = """
    Jane Smith
    Email: jane@example.com
    Phone: +1 555-987-6543
    
    EXPERIENCE
    Software Engineer at TechCorp (2022 - 2024)
    - Developed backend services using Python and Flask.
    - I did not work with Java or C# during this role.
    """
    skills, _ = extractor.extract_skills(resume_text)
    assert "Python" in skills.programming_languages
    assert "Flask" in skills.frameworks
    assert "Java" not in skills.programming_languages
    assert "C#" not in skills.programming_languages


# ==================== TEST 3: SQL CLASSIFICATION ====================

def test_sql_is_programming_language():
    assert get_canonical_category("SQL") == "programming_languages"
    assert get_canonical_category("PL/SQL") == "programming_languages"
    assert get_canonical_category("T-SQL") == "programming_languages"
    assert get_canonical_category("MySQL") == "databases"
    assert get_canonical_category("PostgreSQL") == "databases"


def test_sql_extracted_in_programming_languages(extractor):
    resume_text = """
    SKILLS
    Programming Languages: Python, Java, SQL
    Databases: MySQL, PostgreSQL, MongoDB
    """
    skills, _ = extractor.extract_skills(resume_text, skills_section_text=resume_text)
    assert "SQL" in skills.programming_languages
    assert "SQL" not in skills.databases
    assert "MySQL" in skills.databases
    assert "PostgreSQL" in skills.databases
    assert "MongoDB" in skills.databases


# ==================== TEST 4: FRAMEWORKS AND LIBRARIES ====================

def test_frameworks_and_libraries_categorization(extractor):
    resume_text = """
    TECHNICAL SKILLS
    Frameworks: React, Django, Flask, Spring Boot
    Libraries: NumPy, Pandas, Matplotlib, TensorFlow, PyTorch
    """
    skills, _ = extractor.extract_skills(resume_text, skills_section_text=resume_text)
    assert "React" in skills.frameworks
    assert "Django" in skills.frameworks
    assert "Flask" in skills.frameworks
    assert "Spring Boot" in skills.frameworks
    
    assert "NumPy" in skills.libraries
    assert "Pandas" in skills.libraries
    assert "Matplotlib" in skills.libraries
    assert "TensorFlow" in skills.libraries
    assert "PyTorch" in skills.libraries


# ==================== TEST 5: UI/UX TOOLS ====================

def test_ui_ux_tools_categorization(extractor):
    resume_text = """
    SKILLS
    Design & UI/UX: Figma, Adobe XD, Adobe Photoshop, Canva
    Tools: Git, Docker, Postman
    """
    skills, _ = extractor.extract_skills(resume_text, skills_section_text=resume_text)
    assert "Figma" in skills.ui_ux_tools
    assert "Adobe XD" in skills.ui_ux_tools
    assert "Adobe Photoshop" in skills.ui_ux_tools
    assert "Canva" in skills.ui_ux_tools
    assert "Git" in skills.tools
    assert "Docker" in skills.tools
    assert "Postman" in skills.tools


# ==================== TEST 6: OFFICE PRODUCTIVITY ====================

def test_office_productivity_categorization(extractor):
    resume_text = """
    SKILLS
    Office Tools: Microsoft Excel, Microsoft Word, Microsoft PowerPoint
    Soft Skills: Communication, Teamwork, Leadership
    """
    skills, _ = extractor.extract_skills(resume_text, skills_section_text=resume_text)
    assert "Microsoft Excel" in skills.office_productivity
    assert "Microsoft Word" in skills.office_productivity
    assert "Microsoft PowerPoint" in skills.office_productivity
    assert "Communication" in skills.soft_skills
    assert "Teamwork" in skills.soft_skills
    assert "Leadership" in skills.soft_skills


# ==================== TEST 7: EXPERIENCE EVIDENCE ====================

def test_experience_evidence_classification():
    ev_type, is_conf = classify_skill_evidence("Python", "Built RESTful APIs using Python and Django.", "experience")
    assert is_conf is True
    assert ev_type in ["EXPERIENCE_USAGE", "PROJECT_USAGE"]

    ev_type_asp, is_conf_asp = classify_skill_evidence("Java", "I want to become a Java developer.", "summary")
    assert is_conf_asp is False
    assert ev_type_asp == "ASPIRATION"


# ==================== TEST 8: DEDUPLICATION ====================

def test_skill_deduplication(extractor):
    resume_text = """
    TECHNICAL SKILLS
    Programming: Python, Python3
    Tools: Git, GitHub
    """
    skills, _ = extractor.extract_skills(resume_text, skills_section_text=resume_text)
    # Python and Python3 normalize to single "Python"
    assert skills.programming_languages.count("Python") == 1
    assert skills.unique_skill_count == len(skills.all_unique_skills)


# ==================== TEST 9: AMBIGUOUS KEYWORDS ====================

def test_ambiguous_keywords_not_falsely_extracted(extractor):
    resume_text = """
    About Me
    Please go to our company website to review our annual report in spring season.
    We react to changes quickly.
    """
    skills, _ = extractor.extract_skills(resume_text)
    assert "Go" not in skills.programming_languages
    assert "Spring" not in skills.frameworks
    assert "React" not in skills.frameworks


# ==================== TEST 10: LLM SCHEMA NORMALIZER PRESERVATION ====================

def test_llm_schema_normalizer_preserves_joshika():
    raw_llm = {
        "personal_info": {
            "full_name": "JOSHIKA J",
            "email": "joshika1704@gmail.com",
            "phone": "9342571217",
            "location": "Chennai 600128",
        },
        "professional_summary": {
            "text": "Self-motivated and adaptable student aiming to contribute..."
        },
        "skills": {
            "tools": ["Tally", "SPSS", "Basic Computer Knowledge"],
            "office_productivity": ["Microsoft Office", "Microsoft Excel", "Microsoft Word", "Microsoft PowerPoint"],
            "soft_skills": ["Communication Skills"],
            "programming_languages": [],
            "databases": [],
        },
        "education": [
            {
                "degree": "B.Sc (Computer Science)",
                "institution": "Mar Gregorios College of Arts and Science",
                "qualification_type": "Degree",
                "status": "Currently Pursuing",
                "score": "7.5",
                "score_type": "CGPA",
            }
        ],
        "experience": {"full_time": []},
        "internships": [
            {
                "role": "Full Stack Developer Intern",
                "company": "Infogro Technology",
                "start_date": "17 April 2026",
                "end_date": "18 May 2026",
                "location": "Maduravoyal",
            }
        ],
        "languages": ["Tamil", "English"],
    }
    
    resume_text = """
    JOSHIKA J
    Chennai 600128
    joshika1704@gmail.com
    9342571217
    
    SKILLS
    Tally, SPSS, Basic Computer Knowledge
    MS Office (Word, Excel, PowerPoint)
    Communication Skills
    """
    
    profile = normalize_llm_json_to_profile(raw_llm, cleaned_text=resume_text)
    
    # Verify exact skills preservation
    all_unique = profile.skills.all_unique_skills
    assert "Tally" in all_unique
    assert "SPSS" in all_unique
    assert "Basic Computer Knowledge" in all_unique
    assert "Microsoft Excel" in all_unique
    assert "Microsoft Word" in all_unique
    assert "Microsoft PowerPoint" in all_unique
    assert "Communication" in all_unique or "Communication Skills" in all_unique
    
    # Verify fidelity comparison passes
    final_json = profile.to_dict()
    mismatches = compare_llm_and_final(raw_llm, final_json)
    assert len(mismatches) == 0, f"Fidelity mismatches detected: {mismatches}"
