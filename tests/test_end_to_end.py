"""End-to-End integration tests for all 10 sample test resumes across formats."""
import os
import json
import pytest
from src.resume.pipeline import ResumeExtractionPipeline, extract_candidate_profile
from src.resume.profile_schema import ParsingStatus, CandidateProfile


SAMPLE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "sample_resumes")


def test_01_fresher_software_engineer_pdf():
    """Test 01: Fresher Software Engineer PDF."""
    path = os.path.join(SAMPLE_DIR, "01_fresher_software_engineer.pdf")
    profile = extract_candidate_profile(path, "01_fresher_software_engineer.pdf")
    
    assert profile.metadata.status == ParsingStatus.SUCCESS.value
    assert profile.personal_info.name == "Alex Rivera"
    assert profile.personal_info.email == "alex.rivera@email.com"
    assert "Python" in profile.skills.programming_languages
    assert len(profile.education) >= 1
    assert "Berkeley" in (profile.education[0].institution or "")
    assert len(profile.projects) >= 1

    # Verify JSON export
    data_dict = profile.to_dict()
    json_str = json.dumps(data_dict, indent=2)
    assert len(json_str) > 200
    
    # Verify deserialization round-trip
    reconstructed = CandidateProfile.from_dict(json.loads(json_str))
    assert reconstructed.personal_info.name == profile.personal_info.name


def test_02_experienced_fullstack_dev_docx():
    """Test 02: Experienced Full Stack Developer DOCX."""
    path = os.path.join(SAMPLE_DIR, "02_experienced_fullstack_dev.docx")
    profile = extract_candidate_profile(path, "02_experienced_fullstack_dev.docx")
    
    assert profile.metadata.status == ParsingStatus.SUCCESS.value
    assert "Sarah Jenkins" in (profile.personal_info.name or "")
    assert "sarah.jenkins" in (profile.personal_info.email or "")
    assert profile.experience.total_years is not None or len(profile.experience.full_time) >= 1
    assert "TypeScript" in profile.skills.programming_languages or "TypeScript" in profile.skills.technical
    assert any("React" in f for f in profile.skills.frameworks) or any("React" in f for f in profile.skills.frontend)
    assert len(profile.certifications) >= 1


def test_03_data_scientist_ml_engineer_pdf():
    """Test 03: Data Scientist / ML Engineer PDF."""
    path = os.path.join(SAMPLE_DIR, "03_data_scientist_ml_engineer.pdf")
    profile = extract_candidate_profile(path, "03_data_scientist_ml_engineer.pdf")
    
    assert profile.metadata.status == ParsingStatus.SUCCESS.value
    assert "Marcus Vance" in (profile.personal_info.name or "") or "Marcus" in (profile.personal_info.name or "")
    assert "PyTorch" in profile.skills.libraries or "PyTorch" in profile.skills.technical
    assert len(profile.education) >= 1


def test_04_missing_sections_resume_txt():
    """Test 04: Minimal Resume with Missing Sections TXT."""
    path = os.path.join(SAMPLE_DIR, "04_missing_sections_resume.txt")
    profile = extract_candidate_profile(path, "04_missing_sections_resume.txt")
    
    assert profile.metadata.status == ParsingStatus.SUCCESS.value
    assert "David Chen" in (profile.personal_info.name or "")
    assert "david.chen" in (profile.personal_info.email or "")
    assert len(profile.experience.details) >= 1 or len(profile.experience.full_time) >= 1


def test_05_unusual_headers_resume_docx():
    """Test 05: Resume with Unusual Header Names DOCX."""
    path = os.path.join(SAMPLE_DIR, "05_unusual_headers_resume.docx")
    profile = extract_candidate_profile(path, "05_unusual_headers_resume.docx")
    
    assert profile.metadata.status == ParsingStatus.SUCCESS.value
    assert "Elena Rostova" in (profile.personal_info.name or "")
    assert len(profile.skills.frameworks) >= 1 or len(profile.skills.frontend) >= 1


def test_06_multi_education_academic_cv_pdf():
    """Test 06: Academic CV with Multiple Degrees PDF."""
    path = os.path.join(SAMPLE_DIR, "06_multi_education_academic_cv.pdf")
    profile = extract_candidate_profile(path, "06_multi_education_academic_cv.pdf")
    
    assert profile.metadata.status == ParsingStatus.SUCCESS.value
    assert "Robert Sterling" in (profile.personal_info.name or "")
    assert len(profile.education) >= 2
    degrees = [e.degree for e in profile.education if e.degree]
    assert any("Ph.D" in d or "M.S" in d or "B.S" in d or "Doctor" in d or "Master" in d or "Bachelor" in d or "Philosophy" in d for d in degrees)


def test_07_dense_skills_devops_docx():
    """Test 07: Dense Skills DevOps Engineer DOCX."""
    path = os.path.join(SAMPLE_DIR, "07_dense_skills_devops.docx")
    profile = extract_candidate_profile(path, "07_dense_skills_devops.docx")
    
    assert profile.metadata.status == ParsingStatus.SUCCESS.value
    assert "Karthik Subramanian" in (profile.personal_info.name or "")
    assert "Docker" in profile.skills.tools or "Docker" in profile.skills.technical
    assert "Kubernetes" in profile.skills.tools or "Kubernetes" in profile.skills.technical
    assert "AWS" in profile.skills.cloud or "AWS" in profile.skills.technical


def test_08_no_skills_section_embedded_txt():
    """Test 08: Resume with No Explicit Skills Section (Embedded in Text) TXT."""
    path = os.path.join(SAMPLE_DIR, "08_no_skills_section_embedded.txt")
    profile = extract_candidate_profile(path, "08_no_skills_section_embedded.txt")
    
    assert profile.metadata.status == ParsingStatus.SUCCESS.value
    assert "Emily Watson" in (profile.personal_info.name or "")
    # Even without a "Skills" header, embedded skills should be extracted
    assert "Python" in profile.skills.programming_languages or "Python" in profile.skills.technical


def test_09_irregular_spacing_formatting_txt():
    """Test 09: Irregular Spacing & Formatting TXT."""
    path = os.path.join(SAMPLE_DIR, "09_irregular_spacing_formatting.txt")
    profile = extract_candidate_profile(path, "09_irregular_spacing_formatting.txt")
    
    assert profile.metadata.status == ParsingStatus.SUCCESS.value
    assert "rahul sharma" in (profile.personal_info.name or "").lower()
    assert "rahul.sharma" in (profile.personal_info.email or "")
    assert "Django" in profile.skills.frameworks or "Python" in profile.skills.programming_languages


def test_10_scanned_image_only_simulation_pdf():
    """Test 10: Image-Only Scanned PDF Simulation with Automatic OCR Fallback."""
    path = os.path.join(SAMPLE_DIR, "10_scanned_image_only_simulation.pdf")
    profile = extract_candidate_profile(path, "10_scanned_image_only_simulation.pdf")
    
    assert profile.metadata.status == ParsingStatus.SUCCESS.value
    assert profile.metadata.is_scanned is True
    assert profile.metadata.extraction_method == "ocr"
    assert profile.metadata.ocr_pages_count == 1
    assert profile.metadata.ocr_confidence is not None
    assert "OCR" in profile.metadata.status_message
