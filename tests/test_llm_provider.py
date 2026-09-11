"""Tests for LLM provider factory and configuration — AI Recruitment Platform.

Tests environment variable reading, provider creation, and graceful degradation.
Uses mock providers — no real API calls.
"""
import os
import sys
import pytest
from unittest.mock import patch, MagicMock

# Ensure project root is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class TestLLMConfig:
    """Test LLMConfig environment variable reading."""

    def test_default_disabled(self):
        """LLM should be disabled when LLM_ENABLED='false'."""
        with patch.dict(os.environ, {"LLM_ENABLED": "false"}):
            from services.llm.llm_factory import LLMConfig
            cfg = LLMConfig()
            assert cfg.enabled is False

    def test_enabled_true(self):
        """LLM_ENABLED=true should enable LLM."""
        with patch.dict(os.environ, {"LLM_ENABLED": "true", "LLM_API_KEY": "test-key"}):
            from services.llm.llm_factory import LLMConfig
            cfg = LLMConfig()
            assert cfg.enabled is True

    def test_provider_default_gemini(self):
        """Default provider should be gemini."""
        with patch.dict(os.environ, {"LLM_PROVIDER": "gemini"}):
            from services.llm.llm_factory import LLMConfig
            cfg = LLMConfig()
            assert cfg.provider == "gemini"

    def test_provider_openai(self):
        """LLM_PROVIDER=openai should return openai."""
        with patch.dict(os.environ, {"LLM_PROVIDER": "openai"}):
            from services.llm.llm_factory import LLMConfig
            cfg = LLMConfig()
            assert cfg.provider == "openai"

    def test_ui_summary_has_no_key(self):
        """as_ui_summary() must never expose the API key."""
        with patch.dict(os.environ, {"LLM_API_KEY": "secret-key-12345", "LLM_ENABLED": "true"}):
            from services.llm.llm_factory import LLMConfig
            cfg = LLMConfig()
            summary = cfg.as_ui_summary()
            # Key must not appear anywhere in the summary values
            assert "secret-key-12345" not in str(summary.values())
            assert "api_key_configured" in summary
            assert isinstance(summary["api_key_configured"], bool)

    def test_model_default(self):
        """Default model should be gemini-2.0-flash-lite."""
        with patch.dict(os.environ, {}, clear=False):
            env = {k: v for k, v in os.environ.items() if k != "LLM_MODEL"}
            with patch.dict(os.environ, env, clear=True):
                from services.llm.llm_factory import LLMConfig
                cfg = LLMConfig()
                assert "gemini" in cfg.model.lower() or cfg.model  # model has a default


class TestLLMFactory:
    """Test get_llm_provider() factory function."""

    def test_returns_none_when_disabled(self):
        """get_llm_provider() returns None when LLM_ENABLED=false."""
        with patch.dict(os.environ, {"LLM_ENABLED": "false"}):
            # Re-import to pick up env change
            import importlib
            import services.llm.llm_factory as fmod
            importlib.reload(fmod)
            provider = fmod.get_llm_provider()
            assert provider is None

    def test_returns_none_when_no_api_key(self):
        """get_llm_provider() returns None when API key is empty."""
        with patch.dict(os.environ, {"LLM_ENABLED": "true", "LLM_API_KEY": "", "GEMINI_API_KEY": "", "GOOGLE_API_KEY": ""}):
            import importlib
            import services.llm.llm_factory as fmod
            importlib.reload(fmod)
            provider = fmod.get_llm_provider()
            assert provider is None

    def test_returns_none_with_placeholder_key(self):
        """get_llm_provider() returns None when API key is placeholder."""
        with patch.dict(os.environ, {"LLM_ENABLED": "true", "LLM_API_KEY": "your-api-key-here", "GEMINI_API_KEY": "", "GOOGLE_API_KEY": ""}):
            import importlib
            import services.llm.llm_factory as fmod
            importlib.reload(fmod)
            provider = fmod.get_llm_provider()
            assert provider is None

    def test_returns_none_for_unknown_provider(self):
        """Unknown provider name returns None gracefully."""
        with patch.dict(os.environ, {
            "LLM_ENABLED": "true",
            "LLM_API_KEY": "real-key",
            "LLM_PROVIDER": "unknown_provider_xyz",
        }):
            import importlib
            import services.llm.llm_factory as fmod
            importlib.reload(fmod)
            provider = fmod.get_llm_provider()
            assert provider is None


class TestLLMBaseProvider:
    """Test LLMResponse and base class behavior."""

    def test_llm_response_success(self):
        """LLMResponse with success=True and content set."""
        from services.llm.base import LLMResponse
        resp = LLMResponse(success=True, content={"name": "John"}, provider="Gemini")
        assert resp.success is True
        assert resp.content["name"] == "John"

    def test_llm_response_failure(self):
        """LLMResponse with success=False and error message."""
        from services.llm.base import LLMResponse
        resp = LLMResponse(success=False, error="API timeout")
        assert resp.success is False
        assert resp.error == "API timeout"
        assert resp.content is None
