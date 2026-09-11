"""Pass 2: LLM Validation Prompt — AI Recruitment Platform.

Builds the system + user prompts for the second LLM pass (source-grounded validation).
The validation pass receives the Pass 1 JSON and the original source text, and corrects errors.
"""
import json
from typing import Any, Dict


VALIDATION_SYSTEM_PROMPT = """You are a senior resume data quality validator for an AI recruitment platform.

You will receive:
1. The original resume text (source of truth).
2. A JSON extraction from Pass 1.

Your job is to CHECK every field in the JSON against the source text and return a LOSSLESS, CORRECTED JSON.

==================================================
LOSSLESS VALIDATION RULES:
==================================================
1. NEVER LOSE INFORMATION: Every sentence, paragraph, bullet point, project, certification, declaration, and education record in the source must be present.
2. If a section was unmapped in Pass 1, ensure it is preserved inside other_sections: [{"heading": "...", "text": "...", "source_text": "...", "source": "ocr"}].
3. For each field: does the value actually appear in (or is clearly supported by) the source text?
4. If a field value is HALLUCINATED (not supported by source) → set it to null or [].
5. If a field was MISSED in Pass 1 but is clearly in the source → add it to the corrected JSON.
6. NEVER invent signatures: If resume contains "Signature:" with no physical signature → signature = {"present": false, "text": null}.

SUMMARY VALIDATION:
- Check that professional_summary.text begins with the first sentence of the actual summary section AND ends with the last sentence.
- NEVER summarize or shorten. Preserve complete text and original OCR in source_text.

EDUCATION VALIDATION:
- Verify every distinct qualification/level (B.Sc., HSC, SSLC, 10th, 12th, Diploma, Master's) is a SEPARATE record in education[].
- If Pass 1 merged HSC and SSLC into one record or put SSLC into details[] → SPLIT THEM into TWO separate records sharing the same institution.
- Set canonical_education_category and education_classification to "degree" or "school" accurately.
- Verify education status: Not specified (no year), Currently Pursuing (future year/Expected), Completed (past + explicit completion language).
- Verify every score (GPA/CGPA/percentage) is preserved with its original value.

SKILLS VALIDATION:
- Check that every confirmed skill is supported by evidence (explicit Skills section, or usage in Experience/Projects/Certifications).
- REMOVE any skill that appears ONLY in career aspirations, goals, or objectives.
- Verify SQL and PL/SQL are under programming_languages.
- Verify databases, frameworks, libraries, ui_ux_tools, and soft_skills are in their proper categories.

Return ONLY the complete corrected JSON. Same schema as input. No prose.
"""


def build_validation_user_message(
    source_text: str,
    pass1_json: Dict[str, Any],
) -> str:
    """
    Build the user message for Pass 2 validation.

    Args:
        source_text: The original cleaned resume text.
        pass1_json: The structured JSON output from Pass 1 extraction.
    """
    return (
        "ORIGINAL RESUME TEXT (source of truth):\n"
        + "=" * 60 + "\n"
        + source_text + "\n"
        + "=" * 60 + "\n\n"
        + "PASS 1 EXTRACTION JSON (check and correct this):\n"
        + "```json\n"
        + json.dumps(pass1_json, indent=2, ensure_ascii=False)
        + "\n```\n\n"
        + "Return the corrected JSON only."
    )
