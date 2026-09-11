"""OpenAI LLM Provider for AI Recruitment Platform.

Uses the OpenAI Python SDK to perform structured JSON extraction.
"""
import json
import logging
import time

from services.llm.base import LLMProvider, LLMResponse

logger = logging.getLogger(__name__)

_OPENAI_AVAILABLE = False
try:
    from openai import OpenAI
    _OPENAI_AVAILABLE = True
except ImportError:
    OpenAI = None


class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider with JSON mode and retry support."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini", timeout: int = 30):
        self._api_key = api_key
        self._model = model
        self._timeout = timeout
        self._client = None
        self._initialized = False

        if not _OPENAI_AVAILABLE:
            logger.warning("openai package not installed. OpenAI provider unavailable.")
            return

        if not api_key or api_key == "your-api-key-here":
            logger.warning("OpenAI API key not configured. OpenAI provider unavailable.")
            return

        try:
            self._client = OpenAI(api_key=api_key, timeout=timeout)
            self._initialized = True
            logger.info(f"OpenAI provider initialized with model: {model}")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI provider: {e}")
            self._initialized = False

    def is_available(self) -> bool:
        return _OPENAI_AVAILABLE and self._initialized and self._client is not None

    @property
    def provider_name(self) -> str:
        return "OpenAI"

    @property
    def model_name(self) -> str:
        return self._model

    def complete_json(
        self,
        system_prompt: str,
        user_message: str,
        max_tokens: int = 8192,
    ) -> LLMResponse:
        """
        Send extraction prompt to OpenAI and return parsed JSON.

        Uses JSON response_format mode for reliable structured output.
        Retries up to 3 times with exponential backoff on transient errors.
        """
        if not self.is_available():
            return LLMResponse(
                success=False,
                error="OpenAI provider not available.",
                provider=self.provider_name,
                model=self._model,
            )

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self._client.chat.completions.create(
                    model=self._model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message},
                    ],
                    response_format={"type": "json_object"},
                    max_tokens=max_tokens,
                    temperature=0.0,
                )

                raw_text = response.choices[0].message.content.strip()
                tokens_used = response.usage.total_tokens if response.usage else None

                parsed = json.loads(raw_text)
                return LLMResponse(
                    success=True,
                    content=parsed,
                    raw_text=raw_text,
                    provider=self.provider_name,
                    model=self._model,
                    tokens_used=tokens_used,
                )

            except json.JSONDecodeError as e:
                logger.warning(f"OpenAI returned invalid JSON (attempt {attempt+1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    return LLMResponse(
                        success=False,
                        error=f"Invalid JSON from OpenAI: {e}",
                        provider=self.provider_name,
                        model=self._model,
                    )

            except Exception as e:
                logger.warning(f"OpenAI API error (attempt {attempt+1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    return LLMResponse(
                        success=False,
                        error=f"OpenAI API error: {e}",
                        provider=self.provider_name,
                        model=self._model,
                    )

        return LLMResponse(
            success=False,
            error="Max retries exceeded.",
            provider=self.provider_name,
            model=self._model,
        )
