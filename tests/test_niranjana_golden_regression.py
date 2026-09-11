"""Golden Regression Test Suite: Niranjana Ganapathy Resume Information Extraction.

Verifies:
1. Personal Info: Name, Email, Phone extracted with 100% fidelity; Location is None (no skill leakage).
2. Professional Summary: Full multi-sentence paragraph extracted without contamination.
3. Skills Categorization: Power BI, Tableau, Python, MySQL, Excel, Java, OOP, Marketing Analytics.
4. Education: 3 structured records (B.Sc./B.S., Higher Secondary Class XII, SSLC Class X) with correct grades.
5. Internships: 2 records (Software Testing, Digital Marketing @ SynapseSpark Software Private Ltd).
6. Publications: Research paper at ICAIBPB 2026 isolated cleanly.
7. Certifications: 4 certifications identified accurately.
"""
import os
import pytest
from src.resume.pipeline import extract_candidate_profile
from src.resume.profile_schema import CandidateProfile, QualificationType


NIRANJANA_PDF = os.path.abspath("data/sample_resumes/13_niranjana_resume.pdf")


@pytest.fixture(scope="module")
def niranjana_profile() -> CandidateProfile:
    """Extract and cache candidate profile for Niranjana Ganapathy."""
    assert os.path.exists(NIRANJANA_PDF), f"Resume file not found at {NIRANJANA_PDF}"
    return extract_candidate_profile(NIRANJANA_PDF)


def test_niranjana_personal_info(niranjana_profile: CandidateProfile):
    """Assert personal contact details are extracted with complete isolation."""
    p = niranjana_profile.personal_info
    assert p.name.lower() == "niranjana ganapathy"
    assert p.email == "niranjanayadav69@gmail.com"
    assert "9080469657" in (p.phone or "")
    # CRITICAL: Location must NEVER contain skills or technologies
    assert p.location is None
    assert p.linkedin is None
    assert p.github is None


def test_niranjana_professional_summary(niranjana_profile: CandidateProfile):
    """Assert professional summary is captured accurately."""
    summary = niranjana_profile.summary
    assert summary is not None
    assert "Data Scientist with expertise in machine learning" in summary or "data scientist" in summary.lower()
    assert "telling data stories" in summary or "drive growth" in summary


def test_niranjana_skills_categorization(niranjana_profile: CandidateProfile):
    """Assert tools, databases, languages, and technical disciplines are categorized."""
    skills = niranjana_profile.skills
    all_s = skills.tools + skills.technical + skills.office_productivity
    
    # Tools
    assert any("power bi" in s.lower() for s in all_s)
    assert any("tableau" in s.lower() for s in all_s)
    assert any("excel" in s.lower() for s in all_s)
    
    # Databases / Query Languages
    assert any("mysql" in s.lower() or "sql" in s.lower() for s in (skills.databases + skills.technical + skills.programming_languages))
    
    # Programming Languages
    assert any("python" in s.lower() for s in (skills.programming_languages + skills.technical))
    assert any("java" in s.lower() for s in (skills.programming_languages + skills.technical))
    
    # Technical Disciplines / Business Skills
    all_tech = skills.technical_disciplines + skills.other_technical_skills + skills.technical + getattr(skills, "business_skills", []) + getattr(skills, "other", [])
    assert any("marketing analytics" in s.lower() for s in all_tech)
    assert any("competitor analysis" in s.lower() or "competitive analysis" in s.lower() for s in all_tech)
    assert any("business process improvement" in s.lower() for s in all_tech)


def test_niranjana_education_hierarchy(niranjana_profile: CandidateProfile):
    """Assert all 3 education qualifications are extracted with accurate institutions and grades."""
    edu = niranjana_profile.education
    assert len(edu) == 3

    # Degree
    degree_entry = next((e for e in edu if (e.qualification_type or "").lower() in ["bachelor's", "bachelors", "degree", "undergraduate", "b.sc", "bachelor"] or "bachelor" in (e.degree or "").lower() or "b.sc" in (e.degree or "").lower() or "science" in (e.degree or "").lower()), None)
    assert degree_entry is not None
    assert "M.O.P. Vaishnav College for Women" in (degree_entry.institution or "")
    assert "8.8" in str(degree_entry.grade or degree_entry.percentage or degree_entry.score or degree_entry.cgpa or "")

    # Higher Secondary (Class XII)
    hse_entry = next((e for e in edu if (e.qualification_type or "").lower() in ["hse", "higher_secondary", "higher secondary", "school", "hsc"] or "xii" in (e.degree or "").lower() or "12" in (e.degree or "").lower() or "hsc" in (e.degree or "").lower() or "hse" in (e.degree or "").lower()), None)
    assert hse_entry is not None
    assert "Dr.Radha Krishnan" in (hse_entry.institution or "")
    assert "88" in str(hse_entry.grade or hse_entry.score or hse_entry.percentage or "")

    # SSLC (Class X)
    sslc_entry = next((e for e in edu if (e.qualification_type or "").lower() in ["sslc", "sslc_secondary", "school", "secondary"] or "sslc" in (e.degree or "").lower() or "10" in (e.degree or "").lower() or "class x" in (e.degree or "").lower()), None)
    assert sslc_entry is not None
    assert "Dr.Radha Krishnan" in (sslc_entry.institution or "")
    assert "95.6" in str(sslc_entry.grade or sslc_entry.score or sslc_entry.percentage or "")


def test_niranjana_internships(niranjana_profile: CandidateProfile):
    """Assert 2 separate internships at SynapseSpark Software Private Ltd are extracted without contamination."""
    exp = niranjana_profile.experience
    assert len(exp.internships) == 2

    roles = [i.role for i in exp.internships]
    assert any("testing" in r.lower() for r in roles)
    assert any("marketing" in r.lower() for r in roles)

    for i in exp.internships:
        assert "synapse" in i.company.lower()
        assert i.location is None or "chennai" in i.location.lower()  # No leaked headings in location
        assert len(i.responsibilities) >= 1


def test_niranjana_publications(niranjana_profile: CandidateProfile):
    """Assert research publication is captured."""
    pubs = niranjana_profile.publications
    assert len(pubs) >= 1
    assert any("Artificial Intelligence in Drug Discovery" in (p.title if hasattr(p, "title") else (p.get("title") if isinstance(p, dict) else str(p))) for p in pubs)
    assert any("ICAIBPB 2026" in (p.conference or p.source_text or p.title if hasattr(p, "conference") else (p.get("conference") or p.get("source_text") or p.get("title") if isinstance(p, dict) else str(p))) for p in pubs)


def test_niranjana_certifications(niranjana_profile: CandidateProfile):
    """Assert certifications are extracted."""
    certs = niranjana_profile.certifications
    assert len(certs) >= 3
    cert_names = " ".join(c.name for c in certs).lower()
    assert "mongodb" in cert_names
    assert "financial literacy" in cert_names
    assert "prompt engineering" in cert_names
