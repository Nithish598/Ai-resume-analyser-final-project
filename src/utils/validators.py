"""Validation utilities for contact details, URLs, and file types."""
import re
from typing import Optional

# Standard RFC-5322 compatible email pattern
EMAIL_REGEX = re.compile(
    r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
)

# International & National phone number regex
# Supports +1 (555) 019-2834, +91 98765 43210, (123) 456-7890, 123-456-7890, etc.
PHONE_REGEX = re.compile(
    r"^(\+?\d{1,3}[-.\s]?)?(\(?\d{2,4}\)?[-.\s]?)?\d{3,4}[-.\s]?\d{3,4}$"
)

# Standard Web URLs
URL_REGEX = re.compile(
    r"^(https?:\/\/)?(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$",
    re.IGNORECASE,
)

# Dedicated LinkedIn pattern (with OCR error tolerance like linkedln.com)
LINKEDIN_REGEX = re.compile(
    r"(?:https?:\/\/)?(?:www\.)?linke?d[il1]n\.com\/(?:in|profile)\/([a-zA-Z0-9\-_%]+)\/?",
    re.IGNORECASE,
)

# Dedicated GitHub pattern
GITHUB_REGEX = re.compile(
    r"(?:https?:\/\/)?(?:www\.)?github\.com\/([a-zA-Z0-9\-_]+)\/?",
    re.IGNORECASE,
)


def is_valid_email(email: Optional[str]) -> bool:
    """Validate whether an email string matches standard email formatting."""
    if not email or not isinstance(email, str):
        return False
    clean = email.strip()
    return bool(EMAIL_REGEX.match(clean)) and len(clean) <= 254


def is_valid_phone(phone: Optional[str]) -> bool:
    """Validate whether a string resembles a valid phone number."""
    if not phone or not isinstance(phone, str):
        return False
    digits = re.sub(r"\D", "", phone)
    # Most international telephone numbers contain between 7 and 15 digits
    if len(digits) < 7 or len(digits) > 15:
        return False
    return bool(PHONE_REGEX.match(phone.strip()))


def is_valid_url(url: Optional[str]) -> bool:
    """Validate whether a string is a valid web URL."""
    if not url or not isinstance(url, str):
        return False
    return bool(URL_REGEX.match(url.strip()))


def is_linkedin_url(url: Optional[str]) -> bool:
    """Check if the given string is a LinkedIn profile URL."""
    if not url or not isinstance(url, str):
        return False
    return bool(LINKEDIN_REGEX.search(url.strip()))


def is_github_url(url: Optional[str]) -> bool:
    """Check if the given string is a GitHub profile URL."""
    if not url or not isinstance(url, str):
        return False
    return bool(GITHUB_REGEX.search(url.strip()))
