"""Gemini LLM Provider for AI Recruitment Platform.

Supports both `google-generativeai` (legacy, currently installed) and
`google-genai` (new SDK) automatically.
"""
import json
import logging
import time
import warnings
from typing import Optional

from services.llm.base import LLMProvider, LLMResponse

logger = logging.getLogger(__name__)

# Try new google-genai SDK first, then fall back to legacy google-generativeai
_GENAI_AVAILABLE = False
_USE_NEW_SDK = False
new_genai = None
genai_types = None
old_genai = None

try:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        from google import genai as new_genai
        from google.genai import types as genai_types
    _GENAI_AVAILABLE = True
    _USE_NEW_SDK = True
    logger.debug("Using google-genai (new SDK).")
except ImportError:
    pass

if not _GENAI_AVAILABLE:
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            import google.generativeai as old_genai
        _GENAI_AVAILABLE = True
        _USE_NEW_SDK = False
        logger.debug("Using google-generativeai (legacy SDK).")
    except ImportError:
        pass


class GeminiProvider(LLMProvider):
    """Google Gemini LLM provider with fast-fail retry, health check, and structured JSON output."""

    def __init__(self, api_key: str, model: str = "gemini-3.5-flash-lite", timeout: int = 30):
        self._api_key = api_key
        self._model = model or "gemini-3.5-flash-lite"
        self._timeout = timeout
        self._client = None
        self._initialized = False
        self._init_error = None

        if not _GENAI_AVAILABLE:
            self._init_error = "No Gemini SDK available. Install google-genai or google-generativeai."
            logger.warning(self._init_error)
            return

        if not api_key or api_key == "your-api-key-here":
            self._init_error = "Gemini API key not configured."
            logger.warning(self._init_error)
            return

        try:
            if _USE_NEW_SDK and new_genai is not None:
                self._client = new_genai.Client(api_key=api_key)
            elif old_genai is not None:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    old_genai.configure(api_key=api_key)
                    self._client = old_genai.GenerativeModel(
                        model_name=self._model,
                        generation_config=old_genai.GenerationConfig(
                            response_mime_type="application/json",
                            max_output_tokens=8192,
                            temperature=0.0,
                            top_p=1.0,
                            top_k=1,
                        ),
                    )
            else:
                self._init_error = "No Gemini client SDK could be loaded."
                logger.error(self._init_error)
                return

            self._initialized = True
            sdk_label = "new" if _USE_NEW_SDK else "legacy"
            logger.info(f"Gemini provider initialized: {self._model} ({sdk_label} SDK)")

        except Exception as e:
            self._init_error = f"Failed to initialize Gemini client: {e}"
            logger.error(self._init_error)
            self._initialized = False

    def is_available(self) -> bool:
        return _GENAI_AVAILABLE and self._initialized and self._client is not None

    @property
    def provider_name(self) -> str:
        return "Gemini"

    @property
    def model_name(self) -> str:
        return self._model

    def complete_json(
        self,
        system_prompt: str,
        user_message: str,
        max_tokens: int = 8192,
    ) -> LLMResponse:
        """Send extraction prompt to Gemini and return parsed JSON."""
        if not self.is_available():
            err_msg = self._init_error or "Gemini provider is not available or not initialized."
            return LLMResponse(
                success=False,
                error=err_msg,
                provider=self.provider_name,
                model=self._model,
            )

        full_prompt = f"{system_prompt}\n\n---\n\n{user_message}"
        raw_text = ""

        # Use 1 primary attempt, with at most 1 fast retry for transient network hiccups
        max_attempts = 2
        for attempt in range(max_attempts):
            try:
                if _USE_NEW_SDK and new_genai is not None and genai_types is not None:
                    response = self._client.models.generate_content(
                        model=self._model,
                        contents=full_prompt,
                        config=genai_types.GenerateContentConfig(
                            response_mime_type="application/json",
                            max_output_tokens=max_tokens,
                            temperature=0.0,
                        ),
                    )
                    raw_text = response.text.strip() if response and response.text else ""
                else:
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        response = self._client.generate_content(full_prompt)
                    raw_text = response.text.strip() if response and response.text else ""

                # Strip markdown code fences if present
                if raw_text.startswith("```"):
                    parts = raw_text.split("```")
                    if len(parts) >= 2:
                        raw_text = parts[1]
                        if raw_text.startswith("json"):
                            raw_text = raw_text[4:].strip()

                parsed = json.loads(raw_text)
                return LLMResponse(
                    success=True,
                    content=parsed,
                    raw_text=raw_text,
                    provider=self.provider_name,
                    model=self._model,
                )

            except json.JSONDecodeError as e:
                logger.warning(f"Gemini bad JSON (attempt {attempt+1}/{max_attempts}): {e}")
                if attempt < max_attempts - 1:
                    time.sleep(1)
                else:
                    return LLMResponse(
                        success=False,
                        raw_text=raw_text,
                        error=f"Invalid JSON from Gemini: {e}",
                        provider=self.provider_name,
                        model=self._model,
                    )

            except Exception as e:
                err_str = str(e)
                err_lower = err_str.lower()

                # Fail fast on non-transient errors (auth, quota, not found)
                if any(k in err_lower for k in ("quota", "resourceexhausted", "429", "rate limit")):
                    safe_err = "Gemini API quota or rate limit exceeded. Please try again in a few moments."
                    logger.error(f"Gemini quota exceeded: {e}")
                    return LLMResponse(success=False, error=safe_err, provider=self.provider_name, model=self._model)

                if any(k in err_lower for k in ("invalid api key", "unauthenticated", "permissiondenied", "401", "403", "api_key_invalid")):
                    safe_err = "Gemini API authentication failed (invalid API key)."
                    logger.error(f"Gemini authentication failed: {e}")
                    return LLMResponse(success=False, error=safe_err, provider=self.provider_name, model=self._model)

                if any(k in err_lower for k in ("not found", "404", "invalid argument", "model not supported")):
                    safe_err = f"Gemini model '{self._model}' is not available or unsupported."
                    logger.error(f"Gemini model not found: {e}")
                    return LLMResponse(success=False, error=safe_err, provider=self.provider_name, model=self._model)

                logger.warning(f"Gemini API transient error (attempt {attempt+1}/{max_attempts}): {e}")
                if attempt < max_attempts - 1:
                    time.sleep(1)
                else:
                    return LLMResponse(
                        success=False,
                        error=f"Gemini API error: {err_str}",
                        provider=self.provider_name,
                        model=self._model,
                    )

        return LLMResponse(
            success=False,
            error="Gemini request failed after retries.",
            provider=self.provider_name,
            model=self._model,
        )

    def ping_alive(self) -> dict:
        """Fast, lightweight health check with minimal token usage."""
        if not self.is_available():
            return {
                "reachable": False,
                "response_received": False,
                "parsed": False,
                "latency_ms": 0,
                "error": self._init_error or "Gemini client not initialized or SDK unavailable.",
            }
        t0 = time.time()
        try:
            resp = self.complete_json(
                system_prompt="Return a JSON object: {\"status\": \"ok\", \"candidate_name\": \"Test Candidate\"}",
                user_message="Test prompt",
                max_tokens=64,
            )
            latency = int((time.time() - t0) * 1000)
            if resp.success and resp.content:
                return {
                    "reachable": True,
                    "response_received": True,
                    "parsed": True,
                    "candidate_name": resp.content.get("candidate_name", "Test Candidate"),
                    "latency_ms": latency,
                    "error": None,
                }
            return {
                "reachable": bool(resp.raw_text),
                "response_received": bool(resp.raw_text),
                "parsed": False,
                "latency_ms": latency,
                "error": resp.error or "Ping failed to parse JSON.",
            }
        except Exception as e:
            latency = int((time.time() - t0) * 1000)
            return {
                "reachable": False,
                "response_received": False,
                "parsed": False,
                "latency_ms": latency,
                "error": str(e),
            }
