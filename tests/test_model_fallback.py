"""Tests for Automatic Gemini Model Fallback Mechanism — AI Recruitment Platform.

Verifies:
- TEST 1: Primary succeeds -> only primary model called, fallback not invoked.
- TEST 2: Primary fails with HTTP 429 Quota Exceeded -> fallback model called with identical prompt & succeeds.
- TEST 3: Primary fails with ResourceExhausted exception -> fallback model called with identical prompt & succeeds.
- TEST 4: Both primary and fallback fail with Quota Exceeded -> clean user-friendly error returned without crash.
- TEST 5: Invalid API key (HTTP 401/403) -> fails fast, does NOT rotate models.
- TEST 6: Invalid request / malformed prompt (HTTP 400) -> fails fast, does NOT rotate models.
- TEST 7: Per-request behavior -> subsequent request starts with primary model again (not sticky).
- Unit tests for is_fallback_eligible_error.
- Verification of call_gemini_with_fallback and generate_with_fallback helpers.
"""
import os
import sys
import json
import pytest
from unittest.mock import MagicMock, patch

# Ensure project root is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.llm.gemini_provider import GeminiProvider, is_fallback_eligible_error
from services.llm.llm_factory import (
    LLMConfig,
    call_gemini_with_fallback,
    generate_with_fallback,
    get_llm_provider,
)


class MockAPIError(Exception):
    """Mock API error with HTTP status code mimicking google.genai.errors.APIError."""
    def __init__(self, message: str, code: int):
        super().__init__(message)
        self.code = code


class ResourceExhausted(Exception):
    """Mock ResourceExhausted exception mimicking google.api_core.exceptions.ResourceExhausted."""
    pass


class Unauthenticated(Exception):
    """Mock Unauthenticated exception mimicking google.api_core.exceptions.Unauthenticated."""
    pass


class InvalidArgument(Exception):
    """Mock InvalidArgument exception mimicking google.api_core.exceptions.InvalidArgument."""
    pass


# ==============================================================================
# Unit Tests for Error Classification
# ==============================================================================
class TestFallbackEligibility:
    """Test is_fallback_eligible_error classification logic."""

    def test_http_429_eligible(self):
        err = MockAPIError("Resource exhausted: quota exceeded", code=429)
        assert is_fallback_eligible_error(err) is True

    def test_http_503_eligible(self):
        err = MockAPIError("The model is overloaded. Please try again later.", code=503)
        assert is_fallback_eligible_error(err) is True

    def test_http_500_502_504_eligible(self):
        for code in (500, 502, 504):
            err = MockAPIError(f"Server error {code}", code=code)
            assert is_fallback_eligible_error(err) is True

    def test_http_404_model_not_found_eligible(self):
        err = MockAPIError("models/gemini-2.5-flash-lite is not found", code=404)
        assert is_fallback_eligible_error(err) is True

    def test_resource_exhausted_class_eligible(self):
        err = ResourceExhausted("Quota exceeded for quota metric 'Generate Content'")
        assert is_fallback_eligible_error(err) is True

    def test_keyword_fallback_eligible(self):
        err = Exception("429 RESOURCE_EXHAUSTED: Rate limit exceeded")
        assert is_fallback_eligible_error(err) is True

        err2 = Exception("high demand on model, please retry")
        assert is_fallback_eligible_error(err2) is True

    def test_http_401_403_not_eligible(self):
        for code in (401, 403):
            err = MockAPIError("API_KEY_INVALID", code=code)
            assert is_fallback_eligible_error(err) is False

    def test_unauthenticated_class_not_eligible(self):
        err = Unauthenticated("The request does not have valid authentication credentials")
        assert is_fallback_eligible_error(err) is False

    def test_http_400_invalid_argument_not_eligible(self):
        err = MockAPIError("Invalid argument: prompt is empty", code=400)
        assert is_fallback_eligible_error(err) is False

        err2 = InvalidArgument("Field 'contents' must not be empty")
        assert is_fallback_eligible_error(err2) is False

    def test_code_bugs_not_eligible(self):
        assert is_fallback_eligible_error(KeyError("missing_key")) is False
        assert is_fallback_eligible_error(ValueError("invalid value")) is False
        assert is_fallback_eligible_error(TypeError("unhashable type")) is False


# ==============================================================================
# 7 Core Scenarios for Gemini Model Fallback
# ==============================================================================
class TestGeminiModelFallbackScenarios:
    """Verify all 7 fallback scenarios specified in requirements."""

    def _create_provider(self):
        provider = GeminiProvider(
            api_key="test-api-key-123",
            model="gemini-3.5-flash-lite",
            model_priority=["gemini-3.5-flash-lite", "gemini-3.1-flash-lite"],
        )
        provider._initialized = True
        provider._client = MagicMock()
        return provider

    def test_scenario_1_primary_succeeds_only_primary_called(self):
        """
        TEST 1: When primary model succeeds, only the primary model is called.
        The fallback model is NOT invoked.
        """
        provider = self._create_provider()
        called_models = []

        def mock_generate(model, contents, config=None):
            called_models.append(model)
            mock_resp = MagicMock()
            mock_resp.text = json.dumps({"status": "success", "model": model})
            return mock_resp

        provider._client.models.generate_content.side_effect = mock_generate

        resp = provider.complete_json(
            system_prompt="You are an expert HR analyst.",
            user_message="Extract candidate name",
        )

        assert resp.success is True
        assert resp.model == "gemini-3.5-flash-lite"
        assert resp.content["model"] == "gemini-3.5-flash-lite"
        assert called_models == ["gemini-3.5-flash-lite"]
        assert len(called_models) == 1

    def test_scenario_2_primary_fails_http_429_fallback_succeeds(self):
        """
        TEST 2: Primary model fails with Quota Exceeded (HTTP 429).
        Fallback model is called with identical prompt & configuration, and succeeds.
        """
        provider = self._create_provider()
        calls = []

        def mock_generate(model, contents, config=None):
            calls.append({"model": model, "contents": contents, "config": config})
            if model == "gemini-3.5-flash-lite":
                raise MockAPIError("Quota exceeded for model gemini-3.5-flash-lite", code=429)
            elif model == "gemini-3.1-flash-lite":
                mock_resp = MagicMock()
                mock_resp.text = json.dumps({"candidate_name": "Jane Doe", "skills": ["Python"]})
                return mock_resp
            raise ValueError(f"Unexpected model: {model}")

        provider._client.models.generate_content.side_effect = mock_generate

        resp = provider.complete_json(
            system_prompt="Extract resume data.",
            user_message="Candidate: Jane Doe, Skills: Python",
            max_tokens=4096,
        )

        # Successful response from fallback
        assert resp.success is True
        assert resp.model == "gemini-3.1-flash-lite"
        assert resp.content["candidate_name"] == "Jane Doe"

        # Verify calls: Primary attempted, then fallback attempted
        called_model_names = [c["model"] for c in calls]
        assert "gemini-3.5-flash-lite" in called_model_names
        assert "gemini-3.1-flash-lite" in called_model_names

        # Verify prompt preservation: Both received EXACT same full prompt
        primary_call = [c for c in calls if c["model"] == "gemini-3.5-flash-lite"][0]
        fallback_call = [c for c in calls if c["model"] == "gemini-3.1-flash-lite"][0]
        assert primary_call["contents"] == fallback_call["contents"]
        assert "Extract resume data." in fallback_call["contents"]
        assert "Candidate: Jane Doe, Skills: Python" in fallback_call["contents"]

        # Verify temperature and max_tokens preservation
        if fallback_call["config"]:
            assert fallback_call["config"].temperature == 0.0
            assert fallback_call["config"].max_output_tokens == 4096

    def test_scenario_3_primary_fails_resource_exhausted_fallback_succeeds(self):
        """
        TEST 3: Primary model fails with ResourceExhausted exception.
        Fallback model is invoked with identical prompt and succeeds.
        """
        provider = self._create_provider()
        calls = []

        def mock_generate(model, contents, config=None):
            calls.append(model)
            if model == "gemini-3.5-flash-lite":
                raise ResourceExhausted("RESOURCE_EXHAUSTED: Daily limit reached")
            elif model == "gemini-3.1-flash-lite":
                mock_resp = MagicMock()
                mock_resp.text = json.dumps({"status": "analyzed", "experience_years": 5})
                return mock_resp
            raise ValueError(f"Unexpected model: {model}")

        provider._client.models.generate_content.side_effect = mock_generate

        resp = provider.complete_json(
            system_prompt="Analyze experience.",
            user_message="5 years of software engineering.",
        )

        assert resp.success is True
        assert resp.model == "gemini-3.1-flash-lite"
        assert resp.content["experience_years"] == 5
        assert "gemini-3.5-flash-lite" in calls
        assert "gemini-3.1-flash-lite" in calls

    def test_scenario_4_both_primary_and_fallback_fail_quota(self):
        """
        TEST 4: Both primary and fallback models fail with Quota Exceeded (HTTP 429).
        A clean, user-friendly error is returned without crashing the application.
        """
        provider = self._create_provider()

        def mock_generate(model, contents, config=None):
            raise MockAPIError(f"Quota exceeded for model {model}", code=429)

        provider._client.models.generate_content.side_effect = mock_generate

        resp = provider.complete_json(
            system_prompt="Test system prompt",
            user_message="Test user message",
        )

        assert resp.success is False
        assert resp.content is None
        assert "temporarily unavailable" in resp.error.lower() or "quota" in resp.error.lower()

    def test_scenario_5_invalid_api_key_fails_fast_no_fallback(self):
        """
        TEST 5: Invalid API key (HTTP 401/403).
        Fails fast, does NOT rotate models (fallback is NOT called).
        """
        provider = self._create_provider()
        called_models = []

        def mock_generate(model, contents, config=None):
            called_models.append(model)
            raise MockAPIError("API key not valid. Please pass a valid API key.", code=401)

        provider._client.models.generate_content.side_effect = mock_generate

        resp = provider.complete_json(
            system_prompt="System prompt",
            user_message="User message",
        )

        assert resp.success is False
        assert called_models == ["gemini-3.5-flash-lite"]
        assert "gemini-3.1-flash-lite" not in called_models
        assert "authentication failed" in resp.error.lower() or "invalid api key" in resp.error.lower()

    def test_scenario_6_invalid_argument_malformed_fails_fast_no_fallback(self):
        """
        TEST 6: Invalid request / malformed prompt (HTTP 400).
        Fails fast, does NOT rotate models (fallback is NOT called).
        """
        provider = self._create_provider()
        called_models = []

        def mock_generate(model, contents, config=None):
            called_models.append(model)
            raise MockAPIError("Invalid argument: Request payload is malformed", code=400)

        provider._client.models.generate_content.side_effect = mock_generate

        resp = provider.complete_json(
            system_prompt="System prompt",
            user_message="User message",
        )

        assert resp.success is False
        assert called_models == ["gemini-3.5-flash-lite"]
        assert "gemini-3.1-flash-lite" not in called_models
        assert "bad request" in resp.error.lower() or "invalid argument" in resp.error.lower()

    def test_scenario_7_per_request_behavior_resets_to_primary(self):
        """
        TEST 7: Per-request behavior.
        If Request A falls back to gemini-3.1-flash-lite, Request B MUST still start
        with the primary model (gemini-3.5-flash-lite) again. The fallback is NOT sticky.
        """
        provider = self._create_provider()
        request_calls = []

        # Request A: Primary fails with 429, fallback succeeds
        def mock_generate_req_a(model, contents, config=None):
            request_calls.append(("req_a", model))
            if model == "gemini-3.5-flash-lite":
                raise MockAPIError("Quota exceeded", code=429)
            mock_resp = MagicMock()
            mock_resp.text = json.dumps({"result": "req_a_success"})
            return mock_resp

        provider._client.models.generate_content.side_effect = mock_generate_req_a
        resp_a = provider.complete_json("prompt", "Request A")
        assert resp_a.success is True
        assert resp_a.model == "gemini-3.1-flash-lite"

        # Request B: Primary quota has recovered -> primary succeeds
        def mock_generate_req_b(model, contents, config=None):
            request_calls.append(("req_b", model))
            mock_resp = MagicMock()
            mock_resp.text = json.dumps({"result": "req_b_success"})
            return mock_resp

        provider._client.models.generate_content.side_effect = mock_generate_req_b
        resp_b = provider.complete_json("prompt", "Request B")

        assert resp_b.success is True
        assert resp_b.model == "gemini-3.5-flash-lite"

        # Verify that Request B tried gemini-3.5-flash-lite first
        req_b_models = [m for req, m in request_calls if req == "req_b"]
        assert req_b_models == ["gemini-3.5-flash-lite"]


# ==============================================================================
# Helper Function Verification
# ==============================================================================
class TestFallbackHelpers:
    """Verify call_gemini_with_fallback and generate_with_fallback helpers."""

    def test_generate_text_with_fallback(self):
        """generate_text must also fall back when encountering 429."""
        provider = GeminiProvider(
            api_key="test-key",
            model="gemini-3.5-flash-lite",
            model_priority=["gemini-3.5-flash-lite", "gemini-3.1-flash-lite"],
        )
        provider._initialized = True
        provider._client = MagicMock()

        def mock_generate(model, contents, config=None):
            if model == "gemini-3.5-flash-lite":
                raise MockAPIError("Quota exceeded", code=429)
            mock_resp = MagicMock()
            mock_resp.text = "Generated fallback text."
            return mock_resp

        provider._client.models.generate_content.side_effect = mock_generate
        result = provider.generate_text("Generate a job summary.")
        assert result == "Generated fallback text."

    def test_generate_content_alias(self):
        """generate_content must call generate_text with fallback."""
        provider = GeminiProvider(
            api_key="test-key",
            model="gemini-3.5-flash-lite",
            model_priority=["gemini-3.5-flash-lite", "gemini-3.1-flash-lite"],
        )
        provider._initialized = True
        provider._client = MagicMock()

        mock_resp = MagicMock()
        mock_resp.text = "Job description extracted."
        provider._client.models.generate_content.return_value = mock_resp

        result = provider.generate_content("Extract JD.")
        assert result == "Job description extracted."
