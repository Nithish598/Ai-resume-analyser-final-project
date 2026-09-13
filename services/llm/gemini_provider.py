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


def is_fallback_eligible_error(exc: Exception) -> bool:
    """
    Determine if an exception is eligible for automatic Gemini model fallback.

    Eligible errors (triggers fallback):
      - HTTP 429: Quota exceeded, ResourceExhausted, RateLimitExceeded, TooManyRequests
      - HTTP 503: ServiceUnavailable, model overloaded, high demand
      - HTTP 500/502/504: Internal server error, bad gateway, gateway timeout
      - Model availability/deprecated errors for a specific model (e.g. 404 model not found)

    NOT eligible errors (fails immediately without rotating models):
      - HTTP 401/403: Invalid API key, unauthenticated, permission denied
      - HTTP 400: Malformed prompt, invalid argument
      - Python runtime/application code bugs (ValueError, TypeError, KeyError, etc.)
    """
    if exc is None:
        return False

    # Check for google.genai errors.APIError
    status_code = getattr(exc, "code", None)
    if status_code is not None:
        if status_code in (401, 403):
            return False
        if status_code == 400:
            return False
        if status_code in (429, 503, 500, 502, 504, 404):
            return True

    # Check google.api_core.exceptions if present
    exc_type_name = exc.__class__.__name__
    if exc_type_name in ("Unauthenticated", "PermissionDenied", "InvalidArgument"):
        return False
    if exc_type_name in ("ResourceExhausted", "ServiceUnavailable", "InternalServerError", "TooManyRequests", "NotFound"):
        return True

    err_str = str(exc).lower()

    # Explicit non-fallback keywords (auth / syntax / argument)
    if any(k in err_str for k in ("invalid api key", "api key not valid", "unauthenticated", "permissiondenied", "api_key_invalid", "forbidden", "401", "403")):
        return False
    if any(k in err_str for k in ("invalid argument", "bad request", "malformed")):
        return False

    # Explicit fallback keywords (quota, rate limit, service unavailable, high demand)
    if any(k in err_str for k in (
        "quota", "resourceexhausted", "resource_exhausted", "429", "rate limit",
        "too many requests", "unavailable", "service unavailable", "503",
        "high demand", "overloaded", "server error", "500", "502", "504",
        "not found", "not_found", "model not supported", "is no longer available"
    )):
        return True

    return False


class GeminiProvider(LLMProvider):
    """Google Gemini LLM provider with automatic model fallback, health check, and structured JSON output."""

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-3.5-flash-lite",
        model_priority: Optional[list] = None,
        timeout: int = 30,
    ):
        self._api_key = api_key
        self._model = model or "gemini-3.5-flash-lite"
        self._timeout = timeout
        self._client = None
        self._initialized = False
        self._init_error = None

        if model_priority:
            # Preserve priority order while deduplicating
            seen = set()
            cleaned_priority = []
            for m in model_priority:
                if m and m not in seen:
                    cleaned_priority.append(m)
                    seen.add(m)
            if self._model not in seen:
                cleaned_priority.insert(0, self._model)
            self._model_priority = cleaned_priority
        else:
            self._model_priority = [self._model]

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
            priority_str = " -> ".join(self._model_priority)
            logger.info(f"Gemini provider initialized: [{priority_str}] ({sdk_label} SDK)")

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

    @property
    def model_priority(self) -> list:
        return list(self._model_priority)

    def complete_json(
        self,
        system_prompt: str,
        user_message: str,
        max_tokens: int = 8192,
    ) -> LLMResponse:
        """
        Send extraction prompt to Gemini and return parsed JSON,
        automatically falling back to secondary models if quota or rate limit is reached.
        """
        if not self.is_available():
            err_msg = self._init_error or "Gemini provider is not available or not initialized."
            return LLMResponse(
                success=False,
                error=err_msg,
                provider=self.provider_name,
                model=self._model,
            )

        full_prompt = f"{system_prompt}\n\n---\n\n{user_message}"
        last_error = None

        # Per-request model evaluation: always try models in configured priority order
        for model_idx, target_model in enumerate(self._model_priority):
            is_primary = (model_idx == 0)
            role_label = "primary" if is_primary else f"fallback #{model_idx}"
            logger.info(f"[Gemini] Trying {role_label} model: '{target_model}'")

            raw_text = ""
            max_attempts = 2
            model_failed_due_to_fallback_reason = False

            for attempt in range(max_attempts):
                try:
                    if _USE_NEW_SDK and new_genai is not None and genai_types is not None:
                        response = self._client.models.generate_content(
                            model=target_model,
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
                            gen_model = old_genai.GenerativeModel(
                                model_name=target_model,
                                generation_config=old_genai.GenerationConfig(
                                    response_mime_type="application/json",
                                    max_output_tokens=max_tokens,
                                    temperature=0.0,
                                ),
                            )
                            response = gen_model.generate_content(full_prompt)
                        raw_text = response.text.strip() if response and response.text else ""

                    # Strip markdown code fences if present
                    if raw_text.startswith("```"):
                        parts = raw_text.split("```")
                        if len(parts) >= 2:
                            raw_text = parts[1]
                            if raw_text.startswith("json"):
                                raw_text = raw_text[4:].strip()

                    parsed = json.loads(raw_text)
                    if not is_primary:
                        logger.info(f"[Gemini] Fallback model '{target_model}' succeeded.")
                    else:
                        logger.debug(f"[Gemini] Primary model '{target_model}' succeeded.")

                    return LLMResponse(
                        success=True,
                        content=parsed,
                        raw_text=raw_text,
                        provider=self.provider_name,
                        model=target_model,
                    )

                except json.JSONDecodeError as e:
                    logger.warning(f"[Gemini] Bad JSON from model '{target_model}' (attempt {attempt+1}/{max_attempts}): {e}")
                    if attempt < max_attempts - 1:
                        time.sleep(1)
                    else:
                        last_error = f"Invalid JSON from Gemini model '{target_model}': {e}"
                        # JSON decode errors are format errors, not quota errors - do not rotate models
                        return LLMResponse(
                            success=False,
                            raw_text=raw_text,
                            error=last_error,
                            provider=self.provider_name,
                            model=target_model,
                        )

                except Exception as e:
                    err_str = str(e)
                    last_error = err_str

                    # Check whether this error qualifies for model fallback
                    if not is_fallback_eligible_error(e):
                        logger.error(f"[Gemini] Non-fallback error on model '{target_model}': {e}")
                        safe_err = err_str
                        err_lower = err_str.lower()
                        if getattr(e, "code", None) in (401, 403) or any(k in err_lower for k in ("invalid api key", "api key not valid", "api_key_invalid", "unauthenticated", "401", "403")):
                            safe_err = "Gemini API authentication failed (invalid API key)."
                        elif getattr(e, "code", None) == 400 or any(k in err_lower for k in ("invalid argument", "bad request", "400")):
                            safe_err = f"Gemini API bad request on model '{target_model}'."
                        return LLMResponse(
                            success=False,
                            error=safe_err,
                            provider=self.provider_name,
                            model=target_model,
                        )

                    # Quota / Rate-limit / Temporary 503 error detected
                    logger.warning(
                        f"[Gemini] Model '{target_model}' failed with quota/transient error: {e}. "
                        f"{'Retrying transient drop...' if attempt < max_attempts - 1 else 'Proceeding to fallback...'}"
                    )
                    model_failed_due_to_fallback_reason = True
                    if attempt < max_attempts - 1:
                        time.sleep(1)
                        continue
                    else:
                        break

            # If quota / transient error was encountered and more models exist in priority list, fall back
            if model_failed_due_to_fallback_reason and model_idx < len(self._model_priority) - 1:
                next_model = self._model_priority[model_idx + 1]
                logger.info(f"[Gemini] Quota/rate-limit hit on '{target_model}'. Automatically trying fallback model: '{next_model}'")
                continue
            elif not model_failed_due_to_fallback_reason:
                break

        # All configured models in priority list were exhausted
        logger.error(f"[Gemini] All configured Gemini models failed. Last error: {last_error}")
        return LLMResponse(
            success=False,
            error="AI analysis is temporarily unavailable due to high demand or quota limits. Please try again later.",
            provider=self.provider_name,
            model=self._model,
        )

    def generate_text(self, prompt: str, max_tokens: int = 8192) -> str:
        """Send prompt to Gemini and return plain text response with automatic model fallback."""
        if not self.is_available():
            return ""

        for model_idx, target_model in enumerate(self._model_priority):
            is_primary = (model_idx == 0)
            logger.info(f"[Gemini] Generating text with {'primary' if is_primary else 'fallback'} model: '{target_model}'")
            try:
                if _USE_NEW_SDK and new_genai is not None and genai_types is not None:
                    response = self._client.models.generate_content(
                        model=target_model,
                        contents=prompt,
                        config=genai_types.GenerateContentConfig(
                            max_output_tokens=max_tokens,
                            temperature=0.0,
                        ),
                    )
                    return response.text.strip() if response and response.text else ""
                else:
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        gen_model = old_genai.GenerativeModel(model_name=target_model)
                        response = gen_model.generate_content(prompt)
                    return response.text.strip() if response and response.text else ""
            except Exception as e:
                if is_fallback_eligible_error(e) and model_idx < len(self._model_priority) - 1:
                    next_model = self._model_priority[model_idx + 1]
                    logger.warning(f"[Gemini] Model '{target_model}' failed: {e}. Switching to fallback model '{next_model}'...")
                    continue
                logger.error(f"[Gemini] Text generation failed on model '{target_model}': {e}")
                break
        return ""

    def generate_content(self, prompt: str, **kwargs) -> str:
        """Alias for generate_text for compatibility with callers like jd_parser."""
        max_tokens = kwargs.get("max_tokens", 8192)
        return self.generate_text(prompt, max_tokens=max_tokens)

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
