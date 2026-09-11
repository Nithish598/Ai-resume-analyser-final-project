"""Plain Text Resume Extraction Module.

Handles UTF-8 and legacy encodings (latin-1, cp1252, iso-8859-1) robustly.
"""
from dataclasses import dataclass
from typing import Optional, Union, BinaryIO
import io


class TXTExtractionError(Exception):
    """Base exception for TXT parsing failures."""
    pass


@dataclass
class TXTParseResult:
    """Result of TXT text extraction."""
    text: str
    character_count: int
    encoding_used: str
    error_message: Optional[str] = None


class TXTParser:
    """Robust plain-text resume parser with multi-encoding fallback."""

    SUPPORTED_ENCODINGS = ["utf-8", "utf-8-sig", "latin-1", "cp1252", "iso-8859-1"]

    @classmethod
    def parse(cls, file_source: Union[str, bytes, BinaryIO]) -> TXTParseResult:
        """
        Extract text from a TXT file path, raw bytes, or BytesIO stream.
        
        Args:
            file_source: File path string, raw bytes, or file-like buffer.
            
        Returns:
            TXTParseResult containing decoded text and metadata.
            
        Raises:
            TXTExtractionError: If the file cannot be decoded with supported encodings.
        """
        raw_bytes: bytes = b""

        try:
            if isinstance(file_source, str):
                with open(file_source, "rb") as f:
                    raw_bytes = f.read()
            elif isinstance(file_source, bytes):
                raw_bytes = file_source
            elif hasattr(file_source, "read"):
                raw_bytes = file_source.read()
                if isinstance(raw_bytes, str):
                    raw_bytes = raw_bytes.encode("utf-8")
            else:
                raise TXTExtractionError("Invalid file source type provided for TXT parsing.")

            if not raw_bytes:
                return TXTParseResult(
                    text="",
                    character_count=0,
                    encoding_used="none",
                    error_message="The TXT file is empty.",
                )

            # Try sequential encodings
            decoded_text = None
            used_encoding = None

            for enc in cls.SUPPORTED_ENCODINGS:
                try:
                    decoded_text = raw_bytes.decode(enc)
                    used_encoding = enc
                    break
                except UnicodeDecodeError:
                    continue

            if decoded_text is None:
                # Ultimate fallback with replace
                decoded_text = raw_bytes.decode("utf-8", errors="replace")
                used_encoding = "utf-8 (lossy fallback)"

            clean_text = decoded_text.strip()
            char_count = len(clean_text.replace(" ", "").replace("\n", ""))

            return TXTParseResult(
                text=clean_text,
                character_count=char_count,
                encoding_used=used_encoding or "unknown",
                error_message=None if clean_text else "The TXT file contains only whitespace.",
            )

        except Exception as e:
            if isinstance(e, TXTExtractionError):
                raise
            raise TXTExtractionError(f"Error reading TXT file: {str(e)}") from e


def extract_text_from_txt(file_source: Union[str, bytes, BinaryIO]) -> TXTParseResult:
    """Convenience wrapper for TXTParser.parse()."""
    return TXTParser.parse(file_source)
