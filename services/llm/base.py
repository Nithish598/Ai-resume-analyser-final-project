"""Abstract base class for LLM providers used in AI Recruitment Platform.

Defines the interface that all LLM provider implementations must satisfy.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class LLMResponse:
    """Structured result from an LLM completion call."""
    success: bool
    content: Optional[Dict[str, Any]] = None
    raw_text: Optional[str] = None
    error: Optional[str] = None
    model: Optional[str] = None
    tokens_used: Optional[int] = None
    provider: Optional[str] = None


class LLMProvider(ABC):
    """Abstract interface for LLM provider implementations.

    All providers must implement:
    - complete_json(): Call the LLM and return structured JSON result
    - is_available(): Check if the provider is configured and reachable
    """

    @abstractmethod
    def complete_json(
        self,
        system_prompt: str,
        user_message: str,
        max_tokens: int = 8192,
    ) -> LLMResponse:
        """
        Send a prompt to the LLM and return a JSON-parsed response.

        Args:
            system_prompt: The system-level instruction prompt.
            user_message: The user/document content prompt.
            max_tokens: Maximum number of tokens in the response.

        Returns:
            LLMResponse with success flag, parsed JSON content, and metadata.
        """
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if the provider is configured and ready to use."""
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable name of this provider."""
        ...

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Model identifier being used."""
        ...

    def ping_alive(self) -> Dict[str, Any]:
        """
        Send a tiny test prompt to verify API connectivity and JSON parsing.
        Returns a diagnostic dict with reachable, response_received, parsed, candidate_name, latency_ms, error.
        """
        import time
        start_t = time.perf_counter()
        resp = self.complete_json(
            system_prompt="You are a precise data extraction assistant. Return valid JSON only.",
            user_message='Extract candidate name from: "Name: Test Candidate". Return JSON format: {"candidate_name": "Test Candidate"}',
            max_tokens=100,
        )
        latency = int((time.perf_counter() - start_t) * 1000)
        parsed_name = resp.content.get("candidate_name") if resp.content else None
        return {
            "reachable": resp.success,
            "response_received": bool(resp.raw_text or resp.content),
            "parsed": resp.success and bool(parsed_name),
            "candidate_name": parsed_name,
            "latency_ms": latency,
            "error": resp.error,
        }
