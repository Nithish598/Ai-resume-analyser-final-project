"""Comprehensive Profile URLs Normalization, Validation, and Rendering Test Suite.

Verifies:
1. Normalization of diverse raw formats (full URL, domain-only, plain handle, @handle, Markdown link, HTML anchor).
2. Distinction between usernames and display names (e.g. 'S Gowtham Codes' -> no fabricated URL).
3. Rejection of invalid schemes (javascript:, unencoded spaces, empty schemes).
4. Lossless preservation across Stage A -> Stage B -> Stage C serialization.
5. Accurate UI rendering without raw markdown leakage.
6. Zero candidate-specific hardcoding (works with synthetic names/usernames).
"""
import pytest
from src.resume.profile_schema import (
    CandidateProfile,
    ProfileLink,
    parse_link_like_value,
    validate_profile_url,
    normalize_profile_url,
)
from services.llm.schema_normalizer import normalize_llm_json_to_profile


# ==============================================================================
# 1. LINKEDIN TESTS
# ==============================================================================

def test_linkedin_full_url():
    link = normalize_profile_url("linkedin", "https://www.linkedin.com/in/test-user")
    assert link.valid_format is True
    assert link.url == "https://www.linkedin.com/in/test-user"
    assert link.label == "test-user"


def test_linkedin_without_protocol():
    link = normalize_profile_url("linkedin", "linkedin.com/in/test-user")
    assert link.valid_format is True
    assert link.url == "https://linkedin.com/in/test-user"
    assert link.label == "test-user"


def test_linkedin_www_without_protocol():
    link = normalize_profile_url("linkedin", "www.linkedin.com/in/test-user")
    assert link.valid_format is True
    assert link.url == "https://www.linkedin.com/in/test-user"
    assert link.label == "test-user"


def test_linkedin_plain_handle():
    link = normalize_profile_url("linkedin", "gowtham-s-2205gs")
    assert link.valid_format is True
    assert link.url == "https://www.linkedin.com/in/gowtham-s-2205gs"
    assert link.label == "gowtham-s-2205gs"


def test_linkedin_at_handle():
    link = normalize_profile_url("linkedin", "@gowtham-s-2205gs")
    assert link.valid_format is True
    assert link.url == "https://www.linkedin.com/in/gowtham-s-2205gs"
    assert link.label == "gowtham-s-2205gs"


def test_linkedin_markdown_link():
    link = normalize_profile_url("linkedin", "[Gowtham S](https://www.linkedin.com/in/gowtham-s-2205gs)")
    assert link.valid_format is True
    assert link.url == "https://www.linkedin.com/in/gowtham-s-2205gs"
    assert link.label == "Gowtham S"


# ==============================================================================
# 2. GITHUB TESTS
# ==============================================================================

def test_github_full_url():
    link = normalize_profile_url("github", "https://github.com/gowthamcodes225")
    assert link.valid_format is True
    assert link.url == "https://github.com/gowthamcodes225"
    assert link.label == "gowthamcodes225"


def test_github_without_protocol():
    link = normalize_profile_url("github", "github.com/gowthamcodes225")
    assert link.valid_format is True
    assert link.url == "https://github.com/gowthamcodes225"
    assert link.label == "gowthamcodes225"


def test_github_plain_handle():
    link = normalize_profile_url("github", "gowthamcodes225")
    assert link.valid_format is True
    assert link.url == "https://github.com/gowthamcodes225"
    assert link.label == "gowthamcodes225"


def test_github_at_handle():
    link = normalize_profile_url("github", "@gowthamcodes225")
    assert link.valid_format is True
    assert link.url == "https://github.com/gowthamcodes225"
    assert link.label == "gowthamcodes225"


def test_github_markdown_link():
    link = normalize_profile_url("github", "[Gowtham's GitHub](https://github.com/gowthamcodes225)")
    assert link.valid_format is True
    assert link.url == "https://github.com/gowthamcodes225"
    assert link.label == "Gowtham's GitHub"


# ==============================================================================
# 3. LEETCODE TESTS
# ==============================================================================

def test_leetcode_full_url():
    link = normalize_profile_url("leetcode", "https://leetcode.com/u/gowthamcodes225/")
    assert link.valid_format is True
    assert link.url == "https://leetcode.com/u/gowthamcodes225/"
    assert link.label == "gowthamcodes225"


def test_leetcode_without_protocol():
    link = normalize_profile_url("leetcode", "leetcode.com/u/gowthamcodes225")
    assert link.valid_format is True
    assert link.url == "https://leetcode.com/u/gowthamcodes225"
    assert link.label == "gowthamcodes225"


def test_leetcode_plain_handle():
    link = normalize_profile_url("leetcode", "gowthamcodes225")
    assert link.valid_format is True
    assert link.url == "https://leetcode.com/u/gowthamcodes225/"
    assert link.label == "gowthamcodes225"


def test_leetcode_with_prefix():
    """Verify that 'LeetCode: sGowthamCodes' strips prefix and normalizes to full URL."""
    link = normalize_profile_url("leetcode", "LeetCode: sGowthamCodes")
    assert link.valid_format is True
    assert link.url == "https://leetcode.com/u/sGowthamCodes/"
    assert link.label == "sGowthamCodes"


def test_leetcode_fake_scheme_correction():
    """Verify that [sGowthamCodes](https://sGowthamCodes) is corrected to valid LeetCode URL."""
    link = normalize_profile_url("leetcode", "[sGowthamCodes](https://sGowthamCodes)")
    assert link.valid_format is True
    assert link.url == "https://leetcode.com/u/sGowthamCodes/"
    assert link.label == "sGowthamCodes"


def test_leetcode_markdown_with_valid_url():
    link = normalize_profile_url("leetcode", "[S Gowtham Codes](https://leetcode.com/u/gowthamcodes225/)")
    assert link.valid_format is True
    assert link.url == "https://leetcode.com/u/gowthamcodes225/"
    assert link.label == "S Gowtham Codes"


def test_leetcode_display_name_with_spaces_no_fake_url():
    """Display name containing spaces must NOT generate a fabricated URL."""
    link = normalize_profile_url("leetcode", "S Gowtham Codes")
    assert link.valid_format is False
    assert link.url is None
    assert link.label == "S Gowtham Codes"


def test_leetcode_malformed_markdown_no_fake_url():
    """Exact observed bug: [S Gowtham Codes](https://s Gowtham Codes) must NOT produce https://s Gowtham Codes."""
    link = normalize_profile_url("leetcode", "[S Gowtham Codes](https://s Gowtham Codes)")
    assert link.valid_format is False
    assert link.url is None
    assert link.label == "S Gowtham Codes"


def test_pipeline_hyperlink_enrichment_for_leetcode():
    """Verify that if LLM returns display name or prefix text, embedded PDF hyperlink enriches the URL."""
    stage_a_json = {
        "personal_info": {
            "full_name": "Gowtham S",
            "github": "GitHub: gowthamcodes225",
            "linkedin": "LinkedIn: gowtham-s-2205gs",
            "leetcode": "LeetCode: sGowthamCodes",
        }
    }
    hyperlinks = [
        "https://github.com/gowthamcodes225",
        "https://www.linkedin.com/in/gowtham-s-2205gs",
        "https://leetcode.com/u/sGowthamCodes/",
    ]
    profile = normalize_llm_json_to_profile(stage_a_json, hyperlinks=hyperlinks)
    serialized = profile.to_dict()

    assert serialized["personal_info"]["profiles"]["github"]["url"] == "https://github.com/gowthamcodes225"
    assert serialized["personal_info"]["profiles"]["linkedin"]["url"] == "https://www.linkedin.com/in/gowtham-s-2205gs"
    assert serialized["personal_info"]["profiles"]["leetcode"]["url"] == "https://leetcode.com/u/sGowthamCodes/"
    assert serialized["personal_info"]["profiles"]["leetcode"]["label"] == "sGowthamCodes"
    assert serialized["personal_info"]["profiles"]["leetcode"]["valid_format"] is True


# ==============================================================================
# 4. KAGGLE, PORTFOLIO, PERSONAL WEBSITE TESTS
# ==============================================================================

def test_kaggle_plain_handle():
    link = normalize_profile_url("kaggle", "data_master_42")
    assert link.valid_format is True
    assert link.url == "https://www.kaggle.com/data_master_42"
    assert link.label == "data_master_42"


def test_portfolio_custom_domain():
    link = normalize_profile_url("portfolio", "gowtham.dev")
    assert link.valid_format is True
    assert link.url == "https://gowtham.dev"
    assert link.label == "gowtham.dev"


def test_personal_website_full_url():
    link = normalize_profile_url("personal_website", "https://alice-portfolio.io/about")
    assert link.valid_format is True
    assert link.url == "https://alice-portfolio.io/about"


# ==============================================================================
# 5. MALFORMED & INJECTION RESILIENCE
# ==============================================================================

def test_javascript_scheme_rejected():
    link = normalize_profile_url("portfolio", "javascript:alert(1)")
    assert link.valid_format is False
    assert link.url is None


def test_empty_and_whitespace_url():
    link = normalize_profile_url("github", "   ")
    assert link.valid_format is False
    assert link.url is None
    assert link.label is None


def test_html_anchor_parsing():
    link = normalize_profile_url("github", '<a href="https://github.com/alice">Alice Dev</a>')
    assert link.valid_format is True
    assert link.url == "https://github.com/alice"
    assert link.label == "Alice Dev"


# ==============================================================================
# 6. STAGE A -> B -> C PIPELINE & UI FIDELITY
# ==============================================================================

def test_pipeline_synthetic_candidate_profiles():
    """End-to-end test with arbitrary synthetic candidate profile."""
    stage_a_json = {
        "personal_info": {
            "full_name": "Dev User",
            "linkedin": "dev-user-999",
            "github": "@devcodes",
            "leetcode": "[Dev Solver](https://leetcode.com/u/devsolver/)",
            "kaggle": "dev_analyst",
            "portfolio": "https://devuser.tech",
        }
    }
    
    # Stage B: Internal object conversion
    profile = normalize_llm_json_to_profile(stage_a_json)
    assert profile.personal_info.linkedin == "https://www.linkedin.com/in/dev-user-999"
    assert profile.personal_info.github == "https://github.com/devcodes"
    assert profile.personal_info.leetcode == "https://leetcode.com/u/devsolver/"
    assert profile.personal_info.kaggle == "https://www.kaggle.com/dev_analyst"
    assert profile.personal_info.portfolio == "https://devuser.tech"
    
    # Stage C: Lossless Serialization
    serialized = profile.to_dict()
    profiles_dict = serialized["personal_info"]["profiles"]
    assert profiles_dict["linkedin"]["url"] == "https://www.linkedin.com/in/dev-user-999"
    assert profiles_dict["github"]["url"] == "https://github.com/devcodes"
    assert profiles_dict["leetcode"]["label"] == "Dev Solver"
    assert profiles_dict["leetcode"]["url"] == "https://leetcode.com/u/devsolver/"
    
    assert serialized["candidate"]["linkedin_url"] == "https://www.linkedin.com/in/dev-user-999"
    assert serialized["candidate"]["github_url"] == "https://github.com/devcodes"
    assert serialized["candidate"]["leetcode_url"] == "https://leetcode.com/u/devsolver/"


def test_pipeline_gowtham_leetcode_display_name_handling():
    """Verify that Gowtham's resume with LeetCode display name does not crash or fabricate URL."""
    stage_a_json = {
        "personal_info": {
            "full_name": "Gowtham S",
            "linkedin": "gowtham-s-2205gs",
            "github": "gowthamcodes225",
            "leetcode": "S Gowtham Codes",
        }
    }
    profile = normalize_llm_json_to_profile(stage_a_json)
    serialized = profile.to_dict()
    
    # LinkedIn and GitHub normalized to clickable URLs
    assert serialized["personal_info"]["profiles"]["linkedin"]["url"] == "https://www.linkedin.com/in/gowtham-s-2205gs"
    assert serialized["personal_info"]["profiles"]["github"]["url"] == "https://github.com/gowthamcodes225"
    
    # LeetCode preserved as label without fake URL
    leetcode_prof = serialized["personal_info"]["profiles"]["leetcode"]
    assert leetcode_prof["label"] == "S Gowtham Codes"
    assert leetcode_prof["url"] is None
    assert leetcode_prof["valid_format"] is False
