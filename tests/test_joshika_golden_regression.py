# Golden Regression Test for JOSHIKA M Multi-Column Native PDF Resume.
import os
import re
import pytest
from src.resume.pipeline import extract_candidate_profile
from src.validation.resume_validator import ResumeValidator

SAMPLE_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'sample_resumes', '12_joshika_multicolumn_resume.pdf')


@pytest.fixture(scope='module')
def joshika_profile():
    assert os.path.exists(SAMPLE_PATH), f'Golden sample PDF not found at {SAMPLE_PATH}'
    profile = extract_candidate_profile(SAMPLE_PATH)
    return profile


def test_personal_info(joshika_profile):
    p = joshika_profile.personal_info
    assert p.name is not None
    assert p.name.strip().lower() == 'joshika m'
    assert p.email == 'joshikamurugan9@gmail.com'
    assert p.phone == '8015886407'
    assert p.location == 'Chennai 600128'
    assert p.linkedin is None
    assert p.github is None


def test_professional_summary(joshika_profile):
    s = joshika_profile.summary
    assert s is not None
    assert s.startswith('Enthusiastic, detail-oriented, and highly motivated B.Com student')
    assert 'accounting, finance, business Management' in s or 'accounting, finance, business management' in s.lower()
    assert 'communication, analytical, and problem-solving abilities' in s or 'communication, analytical' in s.lower()
    assert 'supporting the achievement of organizational goals' in s
    assert '8015886407' not in s
    assert 'spss' not in s.lower(), "SPSS from skills section must not appear in summary"


def test_skills_extraction(joshika_profile):
    skills = joshika_profile.skills
    all_skills = (
        skills.tools +
        skills.office_productivity +
        skills.soft_skills +
        skills.other_technical_skills +
        skills.programming_languages +
        skills.technical
    )
    all_skills_lower = [sk.lower() for sk in all_skills]

    # Required skills from both columns
    assert any('basic computer' in sk for sk in all_skills_lower)
    assert any('word' in sk for sk in all_skills_lower)
    assert any('excel' in sk for sk in all_skills_lower)
    assert any('powerpoint' in sk for sk in all_skills_lower)
    assert any('tally' in sk for sk in all_skills_lower)
    assert any('spss' in sk for sk in all_skills_lower)
    assert any('communication' in sk for sk in all_skills_lower)

    # Canonical deduplication check: no duplicate aliases
    assert not ('ms excel' in all_skills_lower and 'microsoft excel' in all_skills_lower)
    assert not ('ms word' in all_skills_lower and 'microsoft word' in all_skills_lower)
    assert any('communication' in s.lower() for s in skills.soft_skills)


def test_education_hierarchy(joshika_profile):
    edu_list = joshika_profile.education
    assert len(edu_list) == 3, f'Expected 3 education records, found {len(edu_list)}'

    # Record 1: Tertiary degree (B.Com)
    bcom = next((e for e in edu_list if re.search(r'\bB\.?Com\b', e.degree or '', re.IGNORECASE)), None)
    assert bcom is not None, 'B.Com education entry not found'
    assert 'Shrimathi Devkunvar' in (bcom.institution or '')
    assert bcom.status in [None, 'Not specified']

    # Record 2: Class XII (HSLC)
    hsc = next((e for e in edu_list if re.search(r'\b(?:XII|HSLC|12th)\b', e.degree or '', re.IGNORECASE)), None)
    assert hsc is not None, 'Class XII education entry not found'
    assert 'Sri RKM Sarada' in (hsc.institution or '')
    assert '92.33%' in str(hsc.percentage or hsc.score)
    assert hsc.score_type.lower() == 'percentage', f"Unexpected score_type for Class XII: {hsc.score_type}"
    assert hsc.gpa is None, f"gpa was not null for Class XII: {hsc.gpa}"
    assert hsc.status in [None, 'Not specified', 'Completed']

    # Record 3: Class X (SSLC)
    sslc = next((e for e in edu_list if re.search(r'\b(?:Class\s*X\b|SSLC|10th)\b', e.degree or '', re.IGNORECASE) and not re.search(r'\b(?:XII|X\s*II|12th)\b', e.degree or '', re.IGNORECASE)), None)
    assert sslc is not None, 'Class X education entry not found'
    assert 'Sri RKM Sarada' in (sslc.institution or '')
    assert '88.8%' in str(sslc.percentage or sslc.score)
    assert sslc.score_type.lower() == 'percentage', f"Unexpected score_type for Class X: {sslc.score_type}"
    assert sslc.gpa is None, f"gpa was not null for Class X: {sslc.gpa}"
    assert sslc.status in [None, 'Not specified', 'Completed']



def test_no_hallucinated_internships_or_achievements(joshika_profile):
    # JOSHIKA_M_Resume_2 does not contain internships or achievements — never hallucinate
    assert len(joshika_profile.experience.internships) == 0
    assert len(joshika_profile.achievements) == 0
    assert len(joshika_profile.projects) == 0


def test_languages_and_interests(joshika_profile):
    langs = [l.lower() for l in joshika_profile.languages]
    assert 'tamil' in langs
    assert 'english' in langs

    interests = [i.lower() for i in joshika_profile.interests]
    assert any('music' in i for i in interests)
    assert any('travelling' in i or 'traveling' in i for i in interests)
    assert any('craft' in i for i in interests)


def test_declaration(joshika_profile):
    decl = joshika_profile.declaration
    assert decl is not None
    assert 'true and correct' in decl['text'].lower()


def test_source_spans_provenance(joshika_profile):
    spans = joshika_profile.source_spans
    assert 'name' in spans and 'joshika' in spans['name']['value'].lower()
    assert 'location' in spans and spans['location']['value'] == 'Chennai 600128'
    assert 'summary' in spans
    assert 'education' in spans and len(spans['education']) == 3
    assert 'skills' in spans
    assert len(joshika_profile.projects) == 0


def test_metadata_and_validation(joshika_profile):
    assert joshika_profile.metadata.extraction_method == 'native'
    assert joshika_profile.metadata.is_scanned is False
    report = ResumeValidator.validate_profile(joshika_profile)
    assert report.is_valid is True
    assert report.quality_score >= 0.85
