"""File Handling and Format Routing Module for AI Recruitment Platform.

Validates file extensions, inspects file size limits, and delegates to the appropriate
format-specific parser (PDF, DOCX, TXT).
"""
import os
from dataclasses import dataclass, field
from typing import Optional, Union, BinaryIO, List, Dict, Any
from src.resume.pdf_parser import PDFParser, PDFExtractionError
from src.resume.docx_parser import DOCXParser, DOCXExtractionError
from src.resume.txt_parser import TXTParser, TXTExtractionError
from src.resume.profile_schema import ParsingStatus


class UnsupportedFormatError(Exception):
    """Raised when an uploaded file format is not supported."""
    pass


class FileSizeExceededError(Exception):
    """Raised when file size exceeds system limit."""
    pass


@dataclass
class RawExtractionResult:
    """Unified result after parsing a file."""
    text: str
    file_name: str
    file_type: str
    character_count: int
    is_scanned: bool = False
    extraction_method: str = "native"
    ocr_confidence: Optional[float] = None
    ocr_pages_count: int = 0
    ocr_blocks: List[Dict[str, Any]] = field(default_factory=list)
    status: str = ParsingStatus.SUCCESS.value
    error_message: Optional[str] = None
    hyperlinks: List[str] = field(default_factory=list)


class FileHandler:
    """Orchestrates format inspection and document text extraction."""

    SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".json"}
    MAX_FILE_SIZE_BYTES = 15 * 1024 * 1024  # 15 MB limit

    @classmethod
    def get_extension(cls, file_name: str) -> str:
        """Extract lowercase file extension with leading dot."""
        _, ext = os.path.splitext(file_name)
        return ext.lower()

    @classmethod
    def process_file(
        cls,
        file_source: Union[str, bytes, BinaryIO],
        file_name: str = "uploaded_resume.txt",
    ) -> RawExtractionResult:
        """
        Validate and extract text from an uploaded file or file path.
        
        Args:
            file_source: File path, bytes, or file-like buffer (e.g. Streamlit UploadedFile).
            file_name: Name of the file for extension inference.
            
        Returns:
            RawExtractionResult with extracted text and status metadata.
        """
        ext = cls.get_extension(file_name)

        if hasattr(file_source, "seek"):
            try:
                file_source.seek(0)
            except Exception:
                pass

        if ext not in cls.SUPPORTED_EXTENSIONS:
            return RawExtractionResult(
                text="",
                file_name=file_name,
                file_type=ext or "unknown",
                character_count=0,
                status=ParsingStatus.ERROR_UNSUPPORTED.value,
                error_message=(
                    f"Unsupported file format '{ext}'. "
                    f"Supported formats are: {', '.join(sorted(cls.SUPPORTED_EXTENSIONS))}"
                ),
                hyperlinks=[],
            )

        try:
            if ext == ".pdf":
                res = PDFParser.parse(file_source)
                status = ParsingStatus.SUCCESS.value if res.character_count > 0 else ParsingStatus.ERROR_EMPTY.value
                return RawExtractionResult(
                    text=res.text,
                    file_name=file_name,
                    file_type="pdf",
                    character_count=res.character_count,
                    is_scanned=res.is_scanned,
                    extraction_method=res.extraction_method,
                    ocr_confidence=res.ocr_confidence,
                    ocr_pages_count=res.ocr_pages_count,
                    ocr_blocks=res.ocr_blocks,
                    status=status,
                    error_message=res.error_message,
                    hyperlinks=res.hyperlinks,
                )

            elif ext == ".docx":
                res = DOCXParser.parse(file_source)
                status = ParsingStatus.SUCCESS.value if res.text else ParsingStatus.ERROR_EMPTY.value
                return RawExtractionResult(
                    text=res.text,
                    file_name=file_name,
                    file_type="docx",
                    character_count=res.character_count,
                    status=status,
                    error_message=res.error_message,
                    hyperlinks=res.hyperlinks,
                )

            elif ext in {".txt", ".json"}:
                res = TXTParser.parse(file_source)
                status = ParsingStatus.SUCCESS.value if res.text else ParsingStatus.ERROR_EMPTY.value
                return RawExtractionResult(
                    text=res.text,
                    file_name=file_name,
                    file_type="json" if ext == ".json" else "txt",
                    character_count=res.character_count,
                    status=status,
                    error_message=res.error_message,
                    hyperlinks=[],
                )

        except (PDFExtractionError, DOCXExtractionError, TXTExtractionError) as e:
            return RawExtractionResult(
                text="",
                file_name=file_name,
                file_type=ext.replace(".", ""),
                character_count=0,
                status=ParsingStatus.ERROR_CORRUPTED.value,
                error_message=f"Failed to extract text: {str(e)}",
            )
        except Exception as e:
            return RawExtractionResult(
                text="",
                file_name=file_name,
                file_type=ext.replace(".", ""),
                character_count=0,
                status=ParsingStatus.ERROR_CORRUPTED.value,
                error_message=f"Unexpected extraction error: {str(e)}",
            )

        return RawExtractionResult(
            text="",
            file_name=file_name,
            file_type=ext,
            character_count=0,
            status=ParsingStatus.ERROR_UNSUPPORTED.value,
            error_message="Unhandled file processing condition.",
        )


def process_resume_file(
    file_source: Union[str, bytes, BinaryIO],
    file_name: str = "resume.pdf",
) -> RawExtractionResult:
    """Convenience functional wrapper for FileHandler.process_file()."""
    return FileHandler.process_file(file_source, file_name)
