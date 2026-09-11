"""Two-pass LLM Extraction Orchestrator — AI Recruitment Platform.

Coordinates Pass 1 (extraction) and Pass 2 (validation) LLM calls.
Provides deterministic fallback if either pass fails.
"""
import hashlib
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from services.llm.base import LLMProvider, LLMResponse
from services.llm.prompts.extraction_prompt import (
    EXTRACTION_SYSTEM_PROMPT,
    build_extraction_user_message,
)
from services.llm.prompts.validation_prompt import (
    VALIDATION_SYSTEM_PROMPT,
    build_validation_user_message,
)

logger = logging.getLogger(__name__)

PROMPT_VERSION = "v2"
_EXTRACTION_CACHE: Dict[str, Dict[str, Any]] = {}


@dataclass
class LLMExtractionResult:
    """Result of the 2-pass LLM extraction process."""
    success: bool
    llm_json: Optional[Dict[str, Any]] = None
    pass1_json: Optional[Dict[str, Any]] = None
    pass2_json: Optional[Dict[str, Any]] = None
    pass1_status: str = "NOT_RUN"  # "NOT_RUN", "SUCCESS", "FAILED"
    pass2_status: str = "NOT_RUN"  # "NOT_RUN", "SUCCESS", "FAILED", "SKIPPED"
    pass1_used: bool = False
    pass2_used: bool = False
    output_received: bool = False
    output_parsed: bool = False
    provider_name: Optional[str] = None
    model_name: Optional[str] = None
    validation_model_name: Optional[str] = None
    call_id: Optional[str] = None
    error: Optional[str] = None
    cache_hit: bool = False
    warnings: list = field(default_factory=list)


class LLMExtractor:
    """Orchestrates the 2-pass LLM extraction pipeline."""

    def __init__(
        self,
        extraction_provider: Optional[LLMProvider],
        validation_provider: Optional[LLMProvider] = None,
        enable_cache: bool = True,
    ):
        self.extraction_provider = extraction_provider
        self.validation_provider = validation_provider
        self.enable_cache = enable_cache

    @classmethod
    def clear_cache(cls):
        """Clear the in-memory extraction cache."""
        _EXTRACTION_CACHE.clear()

    def extract(
        self,
        resume_text: str,
        section_hints: Optional[Dict[str, str]] = None,
        deterministic_hints: Optional[Dict[str, str]] = None,
        call_id: Optional[str] = None,
    ) -> LLMExtractionResult:
        """
        Run 2-pass LLM extraction on resume text.

        Pass 1: Extract structured JSON from resume text.
        Pass 2: Validate and correct Pass 1 JSON against source text.

        Args:
            resume_text: Cleaned resume text from the document parser.
            section_hints: Section boundaries detected by SectionDetector.
            deterministic_hints: High-confidence values already extracted by the deterministic pipeline.
            call_id: Unique trace identifier for this extraction request.

        Returns:
            LLMExtractionResult with structured JSON if successful, or error details.
        """
        cid = call_id or "LLM-DIRECT"

        if not self.extraction_provider or not self.extraction_provider.is_available():
            logger.warning(f"[LLM][{cid}] No LLM extraction provider available.")
            return LLMExtractionResult(
                success=False,
                call_id=cid,
                error="No LLM extraction provider available.",
            )

        provider_name = self.extraction_provider.provider_name
        model_name = self.extraction_provider.model_name
        val_model_name = self.validation_provider.model_name if self.validation_provider else model_name

        # Cache check
        cache_key = hashlib.sha256(
            f"{resume_text}:{model_name}:{PROMPT_VERSION}".encode("utf-8")
        ).hexdigest()

        if self.enable_cache and cache_key in _EXTRACTION_CACHE:
            cached_data = _EXTRACTION_CACHE[cache_key]
            logger.info(f"[LLM][{cid}] cache_hit=true key={cache_key[:8]}")
            return LLMExtractionResult(
                success=True,
                llm_json=cached_data.get("llm_json"),
                pass1_json=cached_data.get("pass1_json"),
                pass2_json=cached_data.get("pass2_json"),
                pass1_status=cached_data.get("pass1_status", "SUCCESS"),
                pass2_status=cached_data.get("pass2_status", "SKIPPED"),
                pass1_used=cached_data.get("pass1_used", True),
                pass2_used=cached_data.get("pass2_used", False),
                output_received=True,
                output_parsed=True,
                provider_name=provider_name,
                model_name=model_name,
                validation_model_name=val_model_name,
                call_id=cid,
                cache_hit=True,
            )

        logger.info(f"[LLM][{cid}] enabled=true provider={provider_name} model={model_name} val_model={val_model_name}")

        # === PASS 1: EXTRACTION ===
        logger.info(f"[LLM][{cid}] extraction_call_started provider={provider_name} model={model_name}")

        user_message = build_extraction_user_message(
            resume_text=resume_text,
            section_hints=section_hints,
            deterministic_hints=deterministic_hints,
        )

        pass1_response: LLMResponse = self.extraction_provider.complete_json(
            system_prompt=EXTRACTION_SYSTEM_PROMPT,
            user_message=user_message,
        )

        if not pass1_response.success or not pass1_response.content:
            safe_err = pass1_response.error or "Unknown extraction failure"
            logger.warning(f"[LLM][{cid}] extraction_call_failed error_type={type(safe_err).__name__} msg={safe_err}")
            return LLMExtractionResult(
                success=False,
                call_id=cid,
                pass1_status="FAILED",
                output_received=bool(pass1_response.raw_text),
                output_parsed=False,
                error=f"Pass 1 extraction failed: {safe_err}",
                provider_name=provider_name,
                model_name=model_name,
                validation_model_name=val_model_name,
            )

        pass1_json = pass1_response.content
        num_fields = len(pass1_json) if isinstance(pass1_json, dict) else 0
        logger.info(f"[LLM][{cid}] extraction_call_success output_received=true output_parsed=true fields={num_fields}")

        # === PASS 2: VALIDATION ===
        if not self.validation_provider or not self.validation_provider.is_available():
            logger.info(f"[LLM][{cid}] validation_skipped provider_unavailable=true")
            res = LLMExtractionResult(
                success=True,
                call_id=cid,
                llm_json=pass1_json,
                pass1_json=pass1_json,
                pass2_json=None,
                pass1_status="SUCCESS",
                pass2_status="SKIPPED",
                pass1_used=True,
                pass2_used=False,
                output_received=True,
                output_parsed=True,
                provider_name=provider_name,
                model_name=model_name,
                validation_model_name=val_model_name,
            )
            if self.enable_cache:
                _EXTRACTION_CACHE[cache_key] = {
                    "llm_json": pass1_json,
                    "pass1_json": pass1_json,
                    "pass2_json": None,
                    "pass1_status": "SUCCESS",
                    "pass2_status": "SKIPPED",
                    "pass1_used": True,
                    "pass2_used": False,
                }
            return res

        logger.info(f"[LLM][{cid}] validation_call_started provider={self.validation_provider.provider_name} model={val_model_name}")

        validation_user_message = build_validation_user_message(
            source_text=resume_text,
            pass1_json=pass1_json,
        )

        pass2_response: LLMResponse = self.validation_provider.complete_json(
            system_prompt=VALIDATION_SYSTEM_PROMPT,
            user_message=validation_user_message,
        )

        if not pass2_response.success or not pass2_response.content:
            safe_val_err = pass2_response.error or "Unknown validation failure"
            logger.warning(f"[LLM][{cid}] validation_call_failed error={safe_val_err} using_pass1_result=true")
            res = LLMExtractionResult(
                success=True,
                call_id=cid,
                llm_json=pass1_json,
                pass1_json=pass1_json,
                pass2_json=None,
                pass1_status="SUCCESS",
                pass2_status="FAILED",
                pass1_used=True,
                pass2_used=False,
                output_received=True,
                output_parsed=True,
                provider_name=provider_name,
                model_name=model_name,
                validation_model_name=val_model_name,
                warnings=[f"Pass 2 validation skipped: {safe_val_err}"],
            )
            if self.enable_cache:
                _EXTRACTION_CACHE[cache_key] = {
                    "llm_json": pass1_json,
                    "pass1_json": pass1_json,
                    "pass2_json": None,
                    "pass1_status": "SUCCESS",
                    "pass2_status": "FAILED",
                    "pass1_used": True,
                    "pass2_used": False,
                }
            return res

        logger.info(f"[LLM][{cid}] validation_call_success output_received=true")
        res = LLMExtractionResult(
            success=True,
            call_id=cid,
            llm_json=pass2_response.content,
            pass1_json=pass1_json,
            pass2_json=pass2_response.content,
            pass1_status="SUCCESS",
            pass2_status="SUCCESS",
            pass1_used=True,
            pass2_used=True,
            output_received=True,
            output_parsed=True,
            provider_name=provider_name,
            model_name=model_name,
            validation_model_name=val_model_name,
        )
        if self.enable_cache:
            _EXTRACTION_CACHE[cache_key] = {
                "llm_json": pass2_response.content,
                "pass1_json": pass1_json,
                "pass2_json": pass2_response.content,
                "pass1_status": "SUCCESS",
                "pass2_status": "SUCCESS",
                "pass1_used": True,
                "pass2_used": True,
            }
        return res
