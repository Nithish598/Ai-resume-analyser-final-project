"""End-to-End Resume Extraction Pipeline for AI Recruitment Platform.

Connects:
1. FileHandler (PDF / DOCX / TXT text extraction)
2. TextCleaner (Normalization, un-hyphenation, unicode cleanup)
3. SectionDetector (Fuzzy section boundary mapping)
4. InformationExtractor (Layered regex + NLP candidate entity extraction)
5. [OPTIONAL] LLMExtractor (2-pass LLM enhancement: extraction + validation)
6. [OPTIONAL] ResultMerger (Merges deterministic + LLM results)
7. ProfileValidator (Post-extraction integrity, student/fresher classification, sanity checks)
8. InformationLossDetector (Detects fields present in source but absent from extraction)
"""
import logging
import uuid
from typing import Optional, Union, BinaryIO, Dict, Any
from dotenv import load_dotenv

load_dotenv(override=False)

from src.resume.file_handler import FileHandler, RawExtractionResult
from src.resume.text_cleaner import TextCleaner
from src.resume.section_detector import SectionDetector
from src.resume.information_extractor import InformationExtractor
from src.resume.validator import ProfileValidator
from src.resume.profile_schema import (
    CandidateProfile,
    ExtractionMetadata,
    ParsingStatus,
    ExtractionConfidence,
)

logger = logging.getLogger(__name__)


def _build_deterministic_hints(profile: CandidateProfile) -> Dict[str, str]:
    """
    Extract high-confidence deterministic values to anchor the LLM extraction.
    These values will be provided to the LLM as already-verified ground truth.
    """
    p = profile.personal_info
    hints = {}
    if p.name:
        hints["full_name"] = p.name
    if p.email:
        hints["email"] = p.email
    if p.phone:
        hints["phone"] = p.phone
    if p.linkedin:
        hints["linkedin_url"] = p.linkedin
    if p.github:
        hints["github_url"] = p.github
    if p.leetcode:
        hints["leetcode_url"] = p.leetcode
    if p.kaggle:
        hints["kaggle_url"] = p.kaggle
    if p.portfolio:
        hints["portfolio_url"] = p.portfolio
    return hints


class ResumeExtractionPipeline:
    """Orchestrates document loading, text cleaning, section detection, information extraction, and validation."""

    def __init__(self):
        self.extractor = InformationExtractor()
        self._llm_extraction_provider = None
        self._llm_validation_provider = None
        self._llm_initialized = False

    def reset_llm(self):
        """Force re-initialization of LLM providers (e.g. when API key or model changes in UI)."""
        self._llm_extraction_provider = None
        self._llm_validation_provider = None
        self._llm_initialized = False
        self._init_llm(force=True)

    def _init_llm(self, force: bool = False):
        """Lazily initialize LLM providers on first use or after reset."""
        try:
            from services.llm.llm_factory import get_llm_provider, get_validation_provider, llm_config
            if force:
                self._llm_extraction_provider = None
                self._llm_validation_provider = None

            if llm_config.enabled:
                if self._llm_extraction_provider is None or not self._llm_extraction_provider.is_available():
                    self._llm_extraction_provider = get_llm_provider()
                if self._llm_validation_provider is None or not self._llm_validation_provider.is_available():
                    self._llm_validation_provider = get_validation_provider()
                self._llm_initialized = bool(self._llm_extraction_provider and self._llm_extraction_provider.is_available())
                if self._llm_extraction_provider and self._llm_extraction_provider.is_available():
                    logger.info(
                        f"LLM initialized: {self._llm_extraction_provider.provider_name}/"
                        f"{self._llm_extraction_provider.model_name}"
                    )
                else:
                    logger.info("LLM enabled but provider unavailable. Using deterministic extraction only.")
            else:
                self._llm_initialized = True
                logger.info("LLM disabled (LLM_ENABLED=false). Using deterministic extraction only.")
        except ImportError:
            self._llm_initialized = True
            logger.warning("services.llm not available. Using deterministic extraction only.")
        except Exception as e:
            self._llm_initialized = True
            logger.warning(f"LLM initialization failed: {e}. Using deterministic extraction only.")

    def process(
        self,
        file_source: Union[str, bytes, BinaryIO],
        file_name: str = "resume.pdf",
    ) -> CandidateProfile:
        """
        Execute full extraction pipeline on a resume file.

        Args:
            file_source: File path string, raw bytes, or file-like buffer (e.g., Streamlit UploadedFile).
            file_name: Name of the file including extension.

        Returns:
            CandidateProfile dataclass containing all validated structured fields and metadata.
        """
        # Step 1: Extract raw text via FileHandler
        raw_result: RawExtractionResult = FileHandler.process_file(file_source, file_name)

        # Handle Corrupted / Unsupported / Empty Errors
        if raw_result.status != ParsingStatus.SUCCESS.value:
            metadata = ExtractionMetadata(
                file_name=file_name,
                file_type=raw_result.file_type,
                character_count=raw_result.character_count,
                status=raw_result.status,
                status_message=raw_result.error_message or "Extraction failed.",
                extraction_method=raw_result.extraction_method,
                ocr_confidence=raw_result.ocr_confidence,
                ocr_pages_count=raw_result.ocr_pages_count,
                is_scanned=raw_result.is_scanned,
            )
            return CandidateProfile(metadata=metadata)

        # Step 2: Clean and normalize text
        cleaned_text = TextCleaner.clean(raw_result.text)

        # Handle edge case where text cleaning reduces text to empty
        if not cleaned_text.strip():
            metadata = ExtractionMetadata(
                file_name=file_name,
                file_type=raw_result.file_type,
                character_count=0,
                status=ParsingStatus.ERROR_EMPTY.value,
                status_message="Extracted text was empty after normalization.",
                extraction_method=raw_result.extraction_method,
                ocr_confidence=raw_result.ocr_confidence,
                ocr_pages_count=raw_result.ocr_pages_count,
                is_scanned=raw_result.is_scanned,
            )
        # Step 2.5: Direct JSON File Processing (if uploading a pre-structured/exported JSON)
        if raw_result.file_type == "json":
            try:
                import json
                json_data = json.loads(raw_result.text)
                if isinstance(json_data, dict) and ("education" in json_data or "personal_info" in json_data or "skills" in json_data):
                    profile = CandidateProfile.from_dict(json_data)
                    profile.metadata.file_name = file_name
                    profile.metadata.file_type = "json"
                    profile.metadata.status = ParsingStatus.SUCCESS.value
                    profile.metadata.extraction_engine = "json_direct"
                    profile.metadata.llm_enabled = True
                    profile.metadata.llm_enhanced = True
                    profile.metadata.final_result_source = "JSON"
                    profile.metadata.stage_snapshots["stage_a_raw_llm"] = json_data
                    profile.metadata.stage_snapshots["stage_b_post_llm"] = profile.to_dict()
                    profile.metadata.stage_snapshots["stage_c_final_json"] = profile.to_dict()
                    profile.metadata.stage_snapshots["final_llm"] = profile.to_dict()
                    return profile
            except Exception as e:
                logger.warning(f"Failed to parse direct JSON input: {e}")

        # Step 3: Detect section boundaries (used for hints and fallback)
        section_result = SectionDetector.detect_sections(cleaned_text)

        # Step 4: LLM EXTRACTION — PRIMARY
        call_id = f"LLM-{uuid.uuid4().hex[:6].upper()}"
        llm_used = False
        profile: Optional[CandidateProfile] = None
        fallback_reason: Optional[str] = None
        llm_prov_name: Optional[str] = None
        llm_mod_name: Optional[str] = None
        llm_val_mod_name: Optional[str] = None

        try:
            self._init_llm()
            from services.llm.llm_factory import llm_config
            llm_prov_name = llm_config.provider.title()
            llm_mod_name = llm_config.model
            llm_val_mod_name = llm_config.validation_model

            if not llm_config.enabled:
                fallback_reason = "LLM disabled in configuration (LLM_ENABLED=false)"
            elif not llm_config.api_key:
                fallback_reason = "LLM API key not configured (add to Streamlit Secrets, .env, or sidebar settings)"
            elif not self._llm_extraction_provider or not self._llm_extraction_provider.is_available():
                init_err = getattr(self._llm_extraction_provider, "_init_error", None) if self._llm_extraction_provider else None
                fallback_reason = init_err or f"LLM provider initialization failed for {llm_config.provider}"
            else:
                from services.llm.llm_extractor import LLMExtractor
                from services.llm.schema_normalizer import normalize_llm_json_to_profile

                llm_extractor = LLMExtractor(
                    extraction_provider=self._llm_extraction_provider,
                    validation_provider=self._llm_validation_provider,
                )

                llm_result = llm_extractor.extract(
                    resume_text=cleaned_text,
                    section_hints=section_result.sections,
                    call_id=call_id,
                )

                llm_prov_name = llm_result.provider_name or llm_prov_name
                llm_mod_name = llm_result.model_name or llm_mod_name
                llm_val_mod_name = llm_result.validation_model_name or llm_val_mod_name

                if llm_result.success and llm_result.llm_json:
                    logger.info(f"[LLM][{call_id}] LLM primary extraction successful")
                    raw_llm_json = llm_result.llm_json
                    
                    profile = normalize_llm_json_to_profile(
                        llm_json=raw_llm_json,
                        raw_text=raw_result.text,
                        cleaned_text=cleaned_text,
                        file_name=file_name,
                        file_type=raw_result.file_type,
                        hyperlinks=raw_result.hyperlinks,
                    )

                    # Populate LLM Primary Metadata
                    profile.metadata.file_name = file_name
                    profile.metadata.file_type = raw_result.file_type
                    profile.metadata.extraction_engine = "llm"
                    profile.metadata.llm_enabled = True
                    profile.metadata.llm_enhanced = True
                    profile.metadata.llm_call_id = call_id
                    profile.metadata.llm_provider = llm_prov_name or "Gemini"
                    profile.metadata.llm_model = llm_mod_name
                    profile.metadata.llm_validation_model = llm_val_mod_name
                    profile.metadata.llm_pass1_used = llm_result.pass1_used
                    profile.metadata.llm_pass2_used = llm_result.pass2_used
                    profile.metadata.fallback_used = False
                    profile.metadata.fallback_reason = None
                    profile.metadata.final_result_source = "LLM"
                    profile.metadata.prompt_version = "v2"
                    profile.metadata.cache_hit = llm_result.cache_hit
                    
                    # 3-Stage Snapshots (Stage A, Stage B, Stage C)
                    profile.metadata.stage_snapshots["stage_a_raw_llm"] = raw_llm_json
                    profile.metadata.stage_snapshots["stage_b_post_llm"] = profile.to_dict()
                    profile.metadata.stage_snapshots["stage_c_final_json"] = profile.to_dict()
                    profile.metadata.stage_snapshots["llm_pass1"] = llm_result.pass1_json
                    profile.metadata.stage_snapshots["llm_pass2"] = llm_result.pass2_json
                    profile.metadata.stage_snapshots["final_llm"] = profile.to_dict()

                    # Automated LLM vs Final JSON Diff Safety Check
                    from services.llm.schema_normalizer import compare_llm_and_final
                    diff_issues = compare_llm_and_final(raw_llm_json, profile.to_dict())
                    if diff_issues:
                        logger.warning(f"[Pipeline][{call_id}] LLM to Final JSON mismatches detected: {diff_issues}")
                        for issue in diff_issues:
                            profile.metadata.information_loss_warnings.append(
                                f"Fidelity mismatch in {issue['field']}: LLM={issue['llm_value']} != Final={issue['final_value']}"
                            )
                    else:
                        logger.info(f"[Pipeline][{call_id}] LLM to Final JSON 100% fidelity check passed.")

                    llm_used = True
                else:
                    safe_err = llm_result.error or "Unknown LLM extraction failure"
                    fallback_reason = safe_err
                    logger.warning(f"[LLM][{call_id}] fallback_used=true reason={safe_err}")

        except Exception as e:
            safe_ex = f"{type(e).__name__}: {e}"
            fallback_reason = safe_ex
            logger.error(f"[LLM][{call_id}] extraction_failed exception={safe_ex} fallback_used=true", exc_info=True)

        # Step 5: DETERMINISTIC FALLBACK (only executed if LLM was unavailable or failed)
        if not llm_used or profile is None:
            logger.info(f"[Pipeline] Running deterministic extraction fallback for {file_name} (Reason: {fallback_reason})")
            profile = self.extractor.extract(
                cleaned_text=cleaned_text,
                sections=section_result.sections,
                file_name=file_name,
                file_type=raw_result.file_type,
                hyperlinks=raw_result.hyperlinks,
            )
            profile.metadata.stage_snapshots["deterministic"] = profile.to_dict()

            try:
                from services.llm.llm_factory import llm_config
                is_llm_cfg_enabled = bool(llm_config.enabled)
                cfg_prov = llm_config.provider.title()
                cfg_model = llm_config.model
            except Exception:
                is_llm_cfg_enabled = False
                cfg_prov = "Gemini"
                cfg_model = "gemini-3.5-flash-lite"

            profile.metadata.llm_call_id = call_id
            profile.metadata.llm_provider = llm_prov_name or cfg_prov
            profile.metadata.llm_model = llm_mod_name or cfg_model
            profile.metadata.llm_validation_model = llm_val_mod_name
            profile.metadata.prompt_version = "v2"

            if is_llm_cfg_enabled:
                profile.metadata.extraction_engine = "deterministic_fallback"
                profile.metadata.llm_enabled = True
                profile.metadata.llm_enhanced = False
                profile.metadata.fallback_used = True
                profile.metadata.fallback_reason = fallback_reason or "LLM extraction unavailable"
                profile.metadata.last_error = fallback_reason or "LLM extraction unavailable"
                profile.metadata.final_result_source = "DETERMINISTIC"
                profile.metadata.information_loss_warnings.append(
                    f"LLM primary extraction unavailable ({profile.metadata.fallback_reason}): used deterministic fallback."
                )
            else:
                profile.metadata.extraction_engine = "deterministic"
                profile.metadata.llm_enabled = False
                profile.metadata.llm_enhanced = False
                profile.metadata.fallback_used = False
                profile.metadata.fallback_reason = None
                profile.metadata.final_result_source = "DETERMINISTIC"

            # Step 6: Run deterministic validator only for deterministic fallback
            profile = ProfileValidator.validate(profile, cleaned_text)

        validated_profile = profile

        # Step 7: Information loss detection
        try:
            from services.llm.information_loss import InformationLossDetector
            loss_report = InformationLossDetector.check(validated_profile, cleaned_text)
            if loss_report.has_issues():
                validated_profile.metadata.information_loss_warnings.extend(loss_report.as_strings())
                logger.info(f"Information loss check: {len(loss_report.all_messages())} warning(s) detected.")
        except Exception as e:
            logger.warning(f"Information loss detection failed: {e}")

        # Step 8: Populate OCR and runtime metadata
        validated_profile.metadata.extraction_method = raw_result.extraction_method
        validated_profile.metadata.ocr_confidence = raw_result.ocr_confidence
        validated_profile.metadata.ocr_pages_count = raw_result.ocr_pages_count
        validated_profile.metadata.ocr_blocks = raw_result.ocr_blocks
        validated_profile.metadata.is_scanned = raw_result.is_scanned
        validated_profile.metadata.character_count = raw_result.character_count
        validated_profile.metadata.raw_text = raw_result.text

        if raw_result.is_scanned:
            conf_pct = f"{int(raw_result.ocr_confidence * 100)}%" if raw_result.ocr_confidence is not None else "N/A"
            validated_profile.metadata.status_message = (
                f"Resume text extracted using OCR fallback ({raw_result.ocr_pages_count} pages processed, confidence: {conf_pct})."
            )

        return validated_profile



def extract_candidate_profile(
    file_source: Union[str, bytes, BinaryIO],
    file_name: str = "resume.pdf",
) -> CandidateProfile:
    """Convenience function to run the full extraction pipeline."""
    pipeline = ResumeExtractionPipeline()
    return pipeline.process(file_source, file_name)
