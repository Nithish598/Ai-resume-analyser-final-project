"""Tests for LLMExtractor and ResultMerger — AI Recruitment Platform.

Tests 2-pass extraction orchestration and merge logic without real API calls.
Uses mock providers to simulate LLM responses.
"""
import os
import sys
import pytest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.llm.base import LLMProvider, LLMResponse
from services.llm.llm_extractor import LLMExtractor, LLMExtractionResult
from services.llm.result_merger import ResultMerger
from src.resume.profile_schema import (
    CandidateProfile, PersonalInfo, Skills, Education, EducationStatus,
    QualificationType, Certification, Project, Experience,
)


def _make_mock_provider(response: LLMResponse) -> MagicMock:
    """Create a mock LLMProvider that returns the given response."""
    provider = MagicMock(spec=LLMProvider)
    provider.is_available.return_value = True
    provider.complete_json.return_value = response
    provider.provider_name = "MockProvider"
    provider.model_name = "mock-model"
    return provider


@pytest.fixture(autouse=True)
def _reset_llm_cache():
    LLMExtractor.clear_cache()
    yield
    LLMExtractor.clear_cache()


SAMPLE_RESUME_TEXT = """
JOSHIKA M
Phone: 8015886407 | Location: Chennai 600128
Email: joshikamurugan9@gmail.com

PROFESSIONAL SUMMARY
Enthusiastic, detail-oriented, and highly motivated B.Com student with a strong foundation
in accounting, finance, business management, and commerce principles.

SKILLS
Microsoft Word | Microsoft Excel | Tally ERP9 | GST Knowledge | Communication | Teamwork

EDUCATION
B.Com (Bachelor of Commerce) - Sri Ram College of Commerce
2024 - 2027 (Expected)
"""

SAMPLE_LLM_JSON = {
    "personal_info": {
        "full_name": "Joshika M",
        "email": "joshikamurugan9@gmail.com",
        "phone": "8015886407",
        "location": "Chennai 600128",
        "linkedin": None,
        "github": None,
    },
    "professional_summary": {
        "text": "Enthusiastic, detail-oriented, and highly motivated B.Com student with a strong foundation in accounting, finance, business management, and commerce principles.",
    },
    "skills": {
        "programming_languages": [],
        "technical": [],
        "office_productivity": ["Microsoft Word", "Microsoft Excel", "Tally ERP9"],
        "soft_skills": ["Communication", "Teamwork"],
        "other": ["GST Knowledge"],
    },
    "education": [
        {
            "qualification_type": "degree",
            "degree": "B.Com",
            "institution": "Sri Ram College of Commerce",
            "start_year": "2024",
            "end_year": "2027",
            "expected_year": "2027",
            "status": "Currently Pursuing",
            "source_text": "B.Com - Sri Ram College of Commerce 2024-2027",
        }
    ],
    "internships": [],
    "projects": [],
    "certifications": [],
    "awards_achievements": [],
    "languages": [],
    "interests": [],
}


class TestLLMExtractor:
    """Test the 2-pass LLM extraction orchestrator."""

    def test_returns_failure_when_no_provider(self):
        """LLMExtractor with no provider returns success=False."""
        extractor = LLMExtractor(extraction_provider=None)
        result = extractor.extract(resume_text="some text")
        assert result.success is False

    def test_successful_pass1_and_pass2(self):
        """Both passes succeed → result has pass1_used=True, pass2_used=True."""
        pass1_resp = LLMResponse(success=True, content=SAMPLE_LLM_JSON, provider="Mock", model="mock")
        pass2_resp = LLMResponse(success=True, content=SAMPLE_LLM_JSON, provider="Mock", model="mock")

        extraction_provider = _make_mock_provider(pass1_resp)
        validation_provider = _make_mock_provider(pass2_resp)

        extractor = LLMExtractor(
            extraction_provider=extraction_provider,
            validation_provider=validation_provider,
        )
        result = extractor.extract(resume_text=SAMPLE_RESUME_TEXT)

        assert result.success is True
        assert result.pass1_used is True
        assert result.pass2_used is True
        assert result.llm_json is not None
        assert result.llm_json["personal_info"]["full_name"] == "Joshika M"

    def test_falls_back_to_pass1_when_pass2_fails(self):
        """If Pass 2 fails, result still uses Pass 1 JSON."""
        pass1_resp = LLMResponse(success=True, content=SAMPLE_LLM_JSON, provider="Mock", model="mock")
        pass2_resp = LLMResponse(success=False, error="Timeout")

        extraction_provider = _make_mock_provider(pass1_resp)
        validation_provider = _make_mock_provider(pass2_resp)

        extractor = LLMExtractor(
            extraction_provider=extraction_provider,
            validation_provider=validation_provider,
        )
        result = extractor.extract(resume_text=SAMPLE_RESUME_TEXT)

        assert result.success is True
        assert result.pass1_used is True
        assert result.pass2_used is False  # Pass 2 failed but we have Pass 1
        assert result.llm_json is SAMPLE_LLM_JSON

    def test_complete_failure_returns_false(self):
        """If Pass 1 fails, result.success is False."""
        pass1_resp = LLMResponse(success=False, error="API key invalid")
        provider = _make_mock_provider(pass1_resp)

        extractor = LLMExtractor(extraction_provider=provider)
        result = extractor.extract(resume_text=SAMPLE_RESUME_TEXT)

        assert result.success is False
        assert result.llm_json is None

    def test_deterministic_hints_passed_to_provider(self):
        """Deterministic hints are included in the LLM user message."""
        resp = LLMResponse(success=True, content=SAMPLE_LLM_JSON)
        provider = _make_mock_provider(resp)

        extractor = LLMExtractor(extraction_provider=provider)
        result = extractor.extract(
            resume_text=SAMPLE_RESUME_TEXT,
            deterministic_hints={"email": "joshikamurugan9@gmail.com", "phone": "8015886407"},
        )

        # Check the user message contained the hints
        call_args = provider.complete_json.call_args
        user_message = call_args[1].get("user_message", "") or call_args[0][1]
        assert "joshikamurugan9@gmail.com" in user_message
        assert "8015886407" in user_message


class TestResultMerger:
    """Test the ResultMerger deterministic + LLM merge logic."""

    def _make_empty_profile(self) -> CandidateProfile:
        return CandidateProfile()

    def test_fills_missing_personal_info(self):
        """ResultMerger fills missing personal info from LLM."""
        profile = CandidateProfile()
        profile.personal_info.name = "Joshika M"  # Already set by deterministic
        profile.personal_info.email = "joshikamurugan9@gmail.com"
        # Phone NOT set — LLM should fill it

        llm_json = {
            "personal_info": {
                "full_name": "Joshika M",
                "email": "joshikamurugan9@gmail.com",
                "phone": "8015886407",
                "location": "Chennai 600128",
            },
            "professional_summary": {"text": "Enthusiastic student."},
            "skills": {},
            "education": [],
            "internships": [], "projects": [], "certifications": [],
            "awards_achievements": [], "languages": [], "interests": [],
        }

        merged = ResultMerger.merge(profile, llm_json, SAMPLE_RESUME_TEXT)
        assert merged.personal_info.phone == "8015886407"
        assert merged.personal_info.location == "Chennai 600128"

    def test_deterministic_name_not_overridden(self):
        """Deterministic name always wins over LLM name."""
        profile = CandidateProfile()
        profile.personal_info.name = "JOSHIKA M"  # Deterministic (uppercase)

        llm_json = {
            "personal_info": {"full_name": "Joshika M LLM VERSION", "email": None, "phone": None, "location": None},
            "professional_summary": {"text": None},
            "skills": {}, "education": [], "internships": [], "projects": [],
            "certifications": [], "awards_achievements": [], "languages": [], "interests": [],
        }

        merged = ResultMerger.merge(profile, llm_json, SAMPLE_RESUME_TEXT)
        # Deterministic name must be preserved (LLM should NOT override)
        assert merged.personal_info.name == "JOSHIKA M"

    def test_summary_filled_from_llm_when_missing(self):
        """If deterministic extracted no summary, use LLM summary."""
        profile = CandidateProfile()
        profile.summary = None  # Deterministic missed it

        llm_json = {
            "personal_info": {"full_name": None, "email": None, "phone": None, "location": None},
            "professional_summary": {"text": "Enthusiastic, detail-oriented, and highly motivated B.Com student"},
            "skills": {}, "education": [], "internships": [], "projects": [],
            "certifications": [], "awards_achievements": [], "languages": [], "interests": [],
        }

        merged = ResultMerger.merge(profile, llm_json, SAMPLE_RESUME_TEXT)
        assert merged.summary is not None
        assert "Enthusiastic" in merged.summary

    def test_llm_summary_longer_replaces_shorter_det(self):
        """LLM summary replaces shorter deterministic summary when source-grounded."""
        profile = CandidateProfile()
        profile.summary = "Enthusiastic student."  # Short (deterministic missed)

        full_summary = "Enthusiastic, detail-oriented, and highly motivated B.Com student with a strong foundation in accounting, finance, business management, and commerce principles."

        llm_json = {
            "personal_info": {"full_name": None, "email": None, "phone": None, "location": None},
            "professional_summary": {"text": full_summary},
            "skills": {}, "education": [], "internships": [], "projects": [],
            "certifications": [], "awards_achievements": [], "languages": [], "interests": [],
        }

        merged = ResultMerger.merge(profile, llm_json, SAMPLE_RESUME_TEXT)
        assert len(merged.summary) > len("Enthusiastic student.")
        assert "detail-oriented" in merged.summary

    def test_education_status_corrected_future_year(self):
        """Education with future end year must be Currently Pursuing after merge."""
        profile = CandidateProfile()
        llm_json = {
            "personal_info": {"full_name": None, "email": None, "phone": None, "location": None},
            "professional_summary": {"text": None},
            "skills": {}, "internships": [], "projects": [],
            "certifications": [], "awards_achievements": [], "languages": [], "interests": [],
            "education": [
                {
                    "qualification_type": "degree",
                    "degree": "B.Com",
                    "institution": "Sri Ram College of Commerce",
                    "start_year": "2024",
                    "end_year": "2027",
                    "status": "Completed",  # LLM incorrectly said Completed
                    "source_text": "B.Com 2024-2027",
                }
            ],
        }

        merged = ResultMerger.merge(profile, llm_json, SAMPLE_RESUME_TEXT)
        # Merger must correct: 2027 is future → Currently Pursuing
        assert len(merged.education) > 0
        edu = merged.education[0]
        assert edu.status == EducationStatus.CURRENTLY_PURSUING.value

    def test_skills_merged_union(self):
        """Skills from LLM and deterministic are unioned (no duplicates)."""
        profile = CandidateProfile()
        profile.skills.office_productivity = ["Microsoft Word", "Microsoft Excel"]
        profile.skills.soft_skills = ["Communication"]

        llm_json = {
            "personal_info": {"full_name": None, "email": None, "phone": None, "location": None},
            "professional_summary": {"text": None},
            "skills": {
                "office_productivity": ["Microsoft Excel", "Tally ERP9"],  # Excel is duplicate
                "soft_skills": ["Teamwork"],  # new
            },
            "education": [], "internships": [], "projects": [],
            "certifications": [], "awards_achievements": [], "languages": [], "interests": [],
        }

        merged = ResultMerger.merge(profile, llm_json, SAMPLE_RESUME_TEXT)
        # Excel should appear only once
        excel_count = sum(1 for s in merged.skills.office_productivity if "Excel" in str(s))
        assert excel_count == 1
        # Tally should be added
        tally_count = sum(1 for s in merged.skills.office_productivity if "Tally" in str(s))
        assert tally_count == 1
        # Teamwork should be added to soft_skills
        teamwork_count = sum(1 for s in merged.skills.soft_skills if "Teamwork" in str(s))
        assert teamwork_count == 1

    def test_no_hallucinated_urls_accepted(self):
        """LLM URLs that don't start with http:// or https:// are rejected."""
        profile = CandidateProfile()
        profile.personal_info.github = None

        llm_json = {
            "personal_info": {
                "full_name": None, "email": None, "phone": None, "location": None,
                "github": "github.com/joshika",  # No http:// prefix → should be rejected
            },
            "professional_summary": {"text": None},
            "skills": {}, "education": [], "internships": [], "projects": [],
            "certifications": [], "awards_achievements": [], "languages": [], "interests": [],
        }

        merged = ResultMerger.merge(profile, llm_json, SAMPLE_RESUME_TEXT)
        assert merged.personal_info.github is None  # Rejected (no http prefix)


class TestLLMSchemaNormalizer:
    """Test the LLM Schema Normalizer direct mapping to CandidateProfile."""

    def test_direct_profile_normalization(self):
        from services.llm.schema_normalizer import normalize_llm_json_to_profile

        profile = normalize_llm_json_to_profile(
            llm_json=SAMPLE_LLM_JSON,
            raw_text=SAMPLE_RESUME_TEXT,
            cleaned_text=SAMPLE_RESUME_TEXT,
            file_name="joshika.pdf",
            file_type="pdf",
        )

        assert profile.personal_info.name == "Joshika M"
        assert profile.personal_info.email == "joshikamurugan9@gmail.com"
        assert profile.personal_info.phone == "8015886407"
        assert profile.personal_info.location == "Chennai 600128"
        assert "Enthusiastic" in profile.summary
        assert len(profile.education) == 1
        assert profile.education[0].degree == "B.Com"
        assert profile.education[0].institution == "Sri Ram College of Commerce"
        assert profile.education[0].status == EducationStatus.CURRENTLY_PURSUING.value
        assert "Communication" in profile.skills.soft_skills
        assert "Microsoft Excel" in profile.skills.office_productivity

    def test_education_percentage_score_typing(self):
        from services.llm.schema_normalizer import normalize_llm_json_to_profile

        custom_json = dict(SAMPLE_LLM_JSON)
        custom_json["education"] = [
            {
                "degree": "Class XII",
                "institution": "Sri RKM Sarada Vidhyalaya",
                "score": "92.33%",
                "score_type": "GPA",  # LLM erroneously labeled score_type as GPA
                "status": "Completed",
                "end_year": "2024",
            }
        ]

        profile = normalize_llm_json_to_profile(
            llm_json=custom_json,
            raw_text=SAMPLE_RESUME_TEXT,
            cleaned_text=SAMPLE_RESUME_TEXT,
        )

        assert len(profile.education) == 1
        edu = profile.education[0]
        assert edu.score_type == "Percentage"
        assert edu.percentage == "92.33%"
        assert edu.gpa is None
        assert edu.status == EducationStatus.COMPLETED.value


class TestLLMFirstArchitecture:
    """Test LLM-first pipeline orchestration with fallback."""

    def test_llm_primary_success_sets_metadata(self):
        from src.resume.pipeline import ResumeExtractionPipeline

        pass1_resp = LLMResponse(success=True, content=SAMPLE_LLM_JSON, provider="MockGemini", model="gemini-2.5-flash")
        provider = _make_mock_provider(pass1_resp)

        pipeline = ResumeExtractionPipeline()
        pipeline._llm_initialized = True
        pipeline._llm_extraction_provider = provider
        pipeline._llm_validation_provider = None

        profile = pipeline.process(SAMPLE_RESUME_TEXT.encode("utf-8"), "test_resume.txt")
        assert profile.metadata.extraction_engine == "llm"
        assert profile.metadata.llm_enhanced is True
        assert profile.metadata.fallback_used is False
        assert (profile.personal_info.name or "").upper() == "JOSHIKA M"

    def test_llm_failure_triggers_deterministic_fallback(self):
        from src.resume.pipeline import ResumeExtractionPipeline

        pass1_resp = LLMResponse(success=False, error="QuotaExceeded")
        provider = _make_mock_provider(pass1_resp)

        pipeline = ResumeExtractionPipeline()
        pipeline._llm_initialized = True
        pipeline._llm_extraction_provider = provider
        pipeline._llm_validation_provider = None

        profile = pipeline.process(SAMPLE_RESUME_TEXT.encode("utf-8"), "test_resume.txt")
        assert profile.metadata.extraction_engine in ["deterministic_fallback", "deterministic"]
        assert profile.metadata.final_result_source == "DETERMINISTIC"
        # Deterministic fallback still extracts candidate name
        assert "JOSHIKA" in (profile.personal_info.name or "").upper()
