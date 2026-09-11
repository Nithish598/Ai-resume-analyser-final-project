# Golden Regression Test for DEEPIGA S Scanned OCR Resume.
import os
import re
import pytest
from src.resume.pipeline import extract_candidate_profile
from src.validation.resume_validator import ResumeValidator

SAMPLE_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'sample_resumes', '14_deepiga_scanned_resume.pdf')


@pytest.fixture(scope='module')
def deepiga_profile():
    assert os.path.exists(SAMPLE_PATH), f'Golden sample PDF not found at {SAMPLE_PATH}'
    profile = extract_candidate_profile(SAMPLE_PATH)
    return profile


def test_personal_info(deepiga_profile):
    p = deepiga_profile.personal_info
    assert p.name is not None
    assert 'deepiga' in p.name.strip().lower()
    assert p.email == 'deepiga2006@gmail.com'
    assert p.phone == '7339605257'
    assert p.location is not None
    assert '102, Srinivasa Nagar, Mangadu-6000122' in p.location or 'Mangadu' in p.location or 'Chennai' in p.location
    assert p.linkedin is not None
    assert 'deepiga-s' in p.linkedin.lower()

    # Source spans consistency check
    src_loc = deepiga_profile.source_spans.get('location')
    assert src_loc is not None
    assert src_loc.get('value') is not None


def test_professional_summary(deepiga_profile):
    s = deepiga_profile.summary
    assert s is not None
    assert 'career goal is to work in a reputed' in s or 'technical skills and gain' in s
    assert 'software industry' in s
    # Ensure no education, certifications or skills are in summary
    assert 'SDNBVC' not in s
    assert 'Java' not in s
    assert 'Declaration' not in s


def test_education_rows_isolation(deepiga_profile):
    edu_list = deepiga_profile.education
    assert len(edu_list) == 3, f'Expected 3 education records, found {len(edu_list)}'

    # Record 1: B.Com Computer Applications (2024-2027, SDNBVC, CGPA 7.3, Pursuing)
    bcom = next((e for e in edu_list if re.search(r'\bB\.?Com\b', e.degree or '', re.IGNORECASE)), None)
    assert bcom is not None, 'B.Com education record not found'
    assert bcom.institution is not None and 'SDNBVC' in bcom.institution
    assert bcom.score == '7.3'
    assert bcom.score_type == 'CGPA'
    assert bcom.start_year == '2024'
    assert bcom.end_year == '2027'
    assert bcom.status == 'Currently Pursuing'
    assert len(bcom.details) == 0, f'B.Com details should have 0 contamination, got: {bcom.details}'

    # Record 2: Class 12th (2023-2024, Sri Sarada Vidhyalaya, 87.8%, Completed)
    hsc = next((e for e in edu_list if re.search(r'\b(?:XII|12th|Higher Secondary)\b', e.degree or '', re.IGNORECASE)), None)
    assert hsc is not None, 'Class XII education record not found'
    assert hsc.institution is not None and 'Sri Sarada' in hsc.institution
    assert '87.8' in str(hsc.score)
    assert hsc.score_type in ['Percentage', 'percentage'], f"Unexpected score_type: {hsc.score_type}"
    assert hsc.start_year == '2023'
    assert hsc.end_year == '2024'
    assert hsc.status == 'Completed'
    assert len(hsc.details) == 0, f'Class XII details should have 0 contamination, got: {hsc.details}'

    # Record 3: Class 10th (2021-2022, Sri Sarada Vidhyalaya, 82.4%, Completed)
    sslc = next((e for e in edu_list if re.search(r'\b(?:Class\s*X|10th|SSLC)\b', e.degree or '', re.IGNORECASE)), None)
    assert sslc is not None, 'Class X education record not found'
    assert sslc.institution is not None and 'Sri Sarada' in sslc.institution
    assert '82.4' in str(sslc.score)
    assert sslc.score_type in ['Percentage', 'percentage'], f"Unexpected score_type: {sslc.score_type}"
    assert sslc.start_year == '2021'
    assert sslc.end_year == '2022'
    assert sslc.status == 'Completed'
    assert len(sslc.details) == 0, f'Class X details should have 0 contamination, got: {sslc.details}'


def test_no_unrelated_sections_in_education_details(deepiga_profile):
    for edu in deepiga_profile.education:
        for detail in edu.details:
            d_lower = detail.lower()
            assert 'certification' not in d_lower
            assert 'excel' not in d_lower
            assert 'powerpoint' not in d_lower
            assert 'social media' not in d_lower
            assert 'wordprocessing' not in d_lower
            assert 'java' not in d_lower
            assert 'python' not in d_lower
            assert 'address' not in d_lower
            assert 'date of birth' not in d_lower
            assert 'declaration' not in d_lower
            assert 'hobbies' not in d_lower
            assert 'languages' not in d_lower


def test_certifications_isolation(deepiga_profile):
    certs = deepiga_profile.certifications
    assert len(certs) >= 1, f'Expected certifications, found {len(certs)}'
    cert_names = [c.name.lower() for c in certs if c.name]
    assert any('excel' in c or 'powerpoint' in c or 'social media' in c or 'wordprocessing' in c for c in cert_names)


def test_skills_extraction(deepiga_profile):
    skills = deepiga_profile.skills
    all_tech = [p.lower() for p in (skills.programming_languages + skills.technical + skills.tools + skills.other_technical_skills)]
    soft = [s.lower() for s in (skills.soft_skills + skills.other + skills.business_skills)]
    assert 'java' in all_tech
    assert 'python' in all_tech
    assert any('leadership' in s for s in soft)
    assert any('teamwork' in s for s in soft)
    assert any('communication' in s for s in soft)
    assert any('analytical' in s for s in soft)


def test_additional_qualifications_isolated(deepiga_profile):
    # Education and certifications must not be dumped into additional_qualifications
    for a in deepiga_profile.additional_qualifications:
        a_str = str(a).lower()
        assert 'b.sc' not in a_str and 'class xii' not in a_str and 'class x' not in a_str


def test_interests_and_declaration_isolated(deepiga_profile):
    interests = [i.lower() for i in deepiga_profile.interests]
    assert any('drawing' in i for i in interests)
    assert any('reading' in i or 'books' in i for i in interests)
    # Declaration must never be inside interests
    assert not any('declare' in i for i in interests)

    # Declaration must be isolated
    decl = deepiga_profile.declaration
    assert decl is not None
    assert 'declare' in decl.get('text', '').lower()
    assert decl.get('date') == '22/05/2026' or '2026' in str(decl.get('date'))
    assert 'Deepiga' in str(decl.get('signature'))


def test_metadata_and_validation(deepiga_profile):
    assert deepiga_profile.metadata.is_scanned is True
    assert deepiga_profile.metadata.extraction_method == 'ocr'
    report = ResumeValidator.validate_profile(deepiga_profile)
    assert report.is_valid is True
    assert report.quality_score >= 0.80