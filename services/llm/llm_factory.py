"""LLM Provider Factory for AI Recruitment Platform.

Reads configuration from environment variables and instantiates the appropriate LLM provider.
Never exposes API keys to the UI layer.
"""
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

# Load .env file if present (silently ignored if not found)
try:
    from dotenv import load_dotenv
    load_dotenv(override=False)
except ImportError:
    pass  # python-dotenv optional — env vars can be set another way


class LLMConfig:
    """Centralized LLM configuration read from environment variables and Streamlit secrets."""

    @property
    def enabled(self) -> bool:
        val = os.getenv("LLM_ENABLED", "").strip().lower()
        if not val:
            try:
                import streamlit as st
                val = str(st.secrets.get("LLM_ENABLED", "")).strip().lower()
            except Exception:
                pass
        if val:
            return val in ("true", "1", "yes")
        # Default to True if valid API key is present
        return bool(self.api_key)

    @property
    def provider(self) -> str:
        prov = os.getenv("LLM_PROVIDER", "").strip().lower()
        if not prov:
            try:
                import streamlit as st
                prov = str(st.secrets.get("LLM_PROVIDER", "")).strip().lower()
            except Exception:
                pass
        return prov or "gemini"

    @property
    def api_key(self) -> str:
        # Check standard env vars first, then Google/Gemini aliases, then Streamlit secrets
        for env_var in ("LLM_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY", "GOOGLE_GENAI_API_KEY"):
            val = os.getenv(env_var, "").strip()
            if val and val != "your-api-key-here":
                return val

        try:
            import streamlit as st
            for sec_key in ("LLM_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY", "GOOGLE_GENAI_API_KEY"):
                val = str(st.secrets.get(sec_key, "")).strip()
                if val and val != "your-api-key-here":
                    return val
        except Exception:
            pass

        return ""

    @property
    def model(self) -> str:
        m = os.getenv("LLM_MODEL", "").strip()
        if not m:
            try:
                import streamlit as st
                m = str(st.secrets.get("LLM_MODEL", "")).strip()
            except Exception:
                pass
        return m or "gemini-3.5-flash-lite"

    @property
    def validation_model(self) -> str:
        m = os.getenv("LLM_VALIDATION_MODEL", "").strip()
        if not m:
            try:
                import streamlit as st
                m = str(st.secrets.get("LLM_VALIDATION_MODEL", "")).strip()
            except Exception:
                pass
        return m or self.model

    @property
    def max_output_tokens(self) -> int:
        try:
            return int(os.getenv("LLM_MAX_OUTPUT_TOKENS", "8192"))
        except ValueError:
            return 8192

    @property
    def timeout_seconds(self) -> int:
        try:
            return int(os.getenv("LLM_TIMEOUT_SECONDS", "30"))
        except ValueError:
            return 30

    def as_ui_summary(self) -> dict:
        """Return safe (no API key) config info for UI display."""
        return {
            "enabled": self.enabled,
            "provider": self.provider,
            "model": self.model,
            "validation_model": self.validation_model,
            "api_key_configured": bool(self.api_key),
        }


# Singleton config instance
llm_config = LLMConfig()


def get_llm_provider(model_override: Optional[str] = None):
    """
    Build and return the configured LLM provider instance.

    Returns None if:
    - LLM_ENABLED=false
    - No API key configured
    - Provider package not installed
    - Initialization fails

    Callers must check `provider is None` before use.
    """
    if not llm_config.enabled:
        logger.info("LLM is disabled (LLM_ENABLED=false). Using deterministic extraction only.")
        return None

    api_key = llm_config.api_key
    if not api_key:
        logger.warning("LLM API key not configured (set LLM_API_KEY or GEMINI_API_KEY in .env).")
        return None

    model = model_override or llm_config.model
    provider_name = llm_config.provider

    try:
        if provider_name in ("gemini", "google", "google_gemini"):
            from services.llm.gemini_provider import GeminiProvider
            p = GeminiProvider(api_key=api_key, model=model, timeout=llm_config.timeout_seconds)
            if p.is_available():
                return p
            logger.warning("Gemini provider initialized but reported unavailable.")
            return None

        elif provider_name == "openai":
            from services.llm.openai_provider import OpenAIProvider
            p = OpenAIProvider(api_key=api_key, model=model, timeout=llm_config.timeout_seconds)
            if p.is_available():
                return p
            logger.warning("OpenAI provider initialized but reported unavailable.")
            return None

        else:
            logger.error(f"Unknown LLM_PROVIDER: '{provider_name}'. Supported: 'gemini', 'openai'.")
            return None

    except Exception as e:
        logger.error(f"Failed to create LLM provider '{provider_name}': {e}")
        return None


def get_validation_provider():
    """Build provider for the Pass 2 validation model (may differ from extraction model)."""
    return get_llm_provider(model_override=llm_config.validation_model)
