"""Resume processing subpackage for AI Recruitment Platform."""


def __getattr__(name: str):
    """Lazy module attribute loading to prevent circular import reentrancy."""
    if name in ("ResumeExtractionPipeline", "extract_candidate_profile"):
        from src.resume.pipeline import ResumeExtractionPipeline, extract_candidate_profile
        return locals()[name]
    if name in (
        "CandidateProfile", "PersonalInfo", "Experience", "ExperienceDetail",
        "InternshipDetail", "Education", "Skills", "Certification", "Project",
        "ExtractionMetadata", "ExtractionConfidence", "ParsingStatus",
        "EmploymentStatus", "EducationStatus", "QualificationType",
    ):
        import src.resume.profile_schema as ps
        return getattr(ps, name)
    if name in ("FileHandler", "process_resume_file"):
        import src.resume.file_handler as fh
        return getattr(fh, name)
    if name in ("PDFParser", "extract_text_from_pdf"):
        import src.resume.pdf_parser as pp
        return getattr(pp, name)
    if name in ("DOCXParser", "extract_text_from_docx"):
        import src.resume.docx_parser as dp
        return getattr(dp, name)
    if name in ("TXTParser", "extract_text_from_txt"):
        import src.resume.txt_parser as tp
        return getattr(tp, name)
    if name in ("TextCleaner", "clean_text"):
        import src.resume.text_cleaner as tc
        return getattr(tc, name)
    if name in ("SectionDetector", "detect_resume_sections"):
        import src.resume.section_detector as sd
        return getattr(sd, name)
    if name in ("SKILLS_TAXONOMY", "get_all_skills", "get_skills_by_category"):
        import src.resume.skills_taxonomy as stx
        return getattr(stx, name)
    if name in ("InformationExtractor",):
        from src.resume.information_extractor import InformationExtractor
        return InformationExtractor
    if name in ("ProfileValidator",):
        from src.resume.validator import ProfileValidator
        return ProfileValidator
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "CandidateProfile",
    "PersonalInfo",
    "Experience",
    "ExperienceDetail",
    "InternshipDetail",
    "Education",
    "Skills",
    "Certification",
    "Project",
    "ExtractionMetadata",
    "ExtractionConfidence",
    "ParsingStatus",
    "EmploymentStatus",
    "EducationStatus",
    "QualificationType",
    "FileHandler",
    "process_resume_file",
    "PDFParser",
    "extract_text_from_pdf",
    "DOCXParser",
    "extract_text_from_docx",
    "TXTParser",
    "extract_text_from_txt",
    "TextCleaner",
    "clean_text",
    "SectionDetector",
    "detect_resume_sections",
    "SKILLS_TAXONOMY",
    "get_all_skills",
    "get_skills_by_category",
    "InformationExtractor",
    "ProfileValidator",
    "ResumeExtractionPipeline",
    "extract_candidate_profile",
]
