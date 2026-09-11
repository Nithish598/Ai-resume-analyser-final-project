"""Helper functions for string processing, date parsing, and experience calculations."""
import re
from datetime import datetime, date
from typing import Optional, Tuple, List, Dict, Any

# Month keywords mapping
MONTHS_MAP = {
    "jan": 1, "january": 1,
    "feb": 2, "february": 2,
    "mar": 3, "march": 3,
    "apr": 4, "april": 4,
    "may": 5,
    "jun": 6, "june": 6,
    "jul": 7, "july": 7,
    "aug": 8, "august": 8,
    "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10,
    "nov": 11, "november": 11,
    "dec": 12, "december": 12,
}

# Regex to parse date ranges supporting:
# "17 Apr 2026 – 18 May 2026", "Jan 2020 - Present", "06/2018 - 12/2021", "2019 to Present", "March 2021 – Aug 2023"
DATE_SINGLE_PATTERN = r"(?:(?:\d{1,2}[\s\/\.-]+)?(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?|\d{1,2})[\s\/\.-]+)?(?:19|20)\d{2}"

DATE_RANGE_REGEX = re.compile(
    rf"(?P<start>{DATE_SINGLE_PATTERN})\s*(?:-|–|—|to|until)\s*(?P<end>{DATE_SINGLE_PATTERN}|Present|Current|Now|Ongoing)",
    re.IGNORECASE,
)


def normalize_whitespace(text: str) -> str:
    """Replace multiple spaces, tabs, and non-breaking spaces with a single space."""
    if not text:
        return ""
    text = text.replace("\u00a0", " ").replace("\u200b", "")
    return re.sub(r"[ \t]+", " ", text).strip()


def parse_date_str(date_str: str) -> Optional[Tuple[int, int, int]]:
    """
    Parse a date string into (year, month, day).
    Supports:
    - '17 April 2026', '17 Apr 2026', '17-Apr-2026'
    - 'April 17, 2026', 'Apr 17 2026'
    - 'April 2026', 'Apr 2026'
    - '2026-04-17', '2026/04/17'
    - '17/04/2026', '17-04-2026'
    - '04/2026', '4/2026'
    - '2026'
    - 'Present', 'Current', 'Ongoing'
    Returns (year, month, day) or None if parsing fails.
    """
    if not date_str or not isinstance(date_str, str):
        return None
    clean = date_str.strip()
    if not clean or clean.lower() in ["none", "null", "not specified", "n/a"]:
        return None
    
    clean_lower = clean.lower()
    if clean_lower in ["present", "current", "now", "ongoing"]:
        now = datetime.now()
        return (now.year, now.month, now.day)
    
    # 1. ISO format YYYY-MM-DD or YYYY/MM/DD
    iso_match = re.match(r"^(\d{4})[-\/\.](\d{1,2})[-\/\.](\d{1,2})$", clean)
    if iso_match:
        y, m, d = int(iso_match.group(1)), int(iso_match.group(2)), int(iso_match.group(3))
        if 1 <= m <= 12 and 1 <= d <= 31:
            return (y, m, d)

    # 2. DD/MM/YYYY or DD-MM-YYYY
    dmy_match = re.match(r"^(\d{1,2})[-\/\.](\d{1,2})[-\/\.](\d{4})$", clean)
    if dmy_match:
        d, m, y = int(dmy_match.group(1)), int(dmy_match.group(2)), int(dmy_match.group(3))
        if 1 <= m <= 12 and 1 <= d <= 31:
            return (y, m, d)

    # 3. MM/YYYY
    my_match = re.match(r"^(\d{1,2})[-\/\.](\d{4})$", clean)
    if my_match:
        m, y = int(my_match.group(1)), int(my_match.group(2))
        if 1 <= m <= 12:
            return (y, m, 1)

    # 4. Extract 4-digit year
    year_match = re.search(r"\b(19\d{2}|20\d{2})\b", clean)
    if not year_match:
        return None
    year = int(year_match.group(1))
    
    # Check for month word (e.g. 'April', 'Apr', 'January', etc.)
    month = None
    for m_name, m_num in MONTHS_MAP.items():
        if re.search(rf"\b{m_name}\b", clean_lower):
            month = m_num
            break
            
    if month is None:
        # Check for numeric month before year: e.g. '04/2026' or '4-2026'
        num_m = re.search(r"\b(\d{1,2})[-\/\.]\d{4}\b", clean)
        if num_m:
            val = int(num_m.group(1))
            if 1 <= val <= 12:
                month = val
    if month is None:
        month = 1

    # Check for day of month (e.g. '17 Apr 2026' or 'April 17 2026')
    day = 1
    day_before_m = re.search(r"\b(\d{1,2})\s*(?:st|nd|rd|th)?[\s\/\.-]+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)", clean_lower)
    if day_before_m:
        day = int(day_before_m.group(1))
    else:
        day_after_m = re.search(r"\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[\s\/\.-]+(\d{1,2})\b", clean_lower)
        if day_after_m:
            day = int(day_after_m.group(1))
        else:
            day_match2 = re.search(r"\b(\d{1,2})[\/\.-]\d{1,2}[\/\.-](?:19|20)\d{2}\b", clean)
            if day_match2:
                day = int(day_match2.group(1))
            
    return (year, month, max(1, min(31, day)))


def calculate_internship_duration(
    start_date: Optional[str],
    end_date: Optional[str],
    explicit_duration: Optional[str] = None,
) -> str:
    """
    Calculate human-readable internship duration deterministically.
    
    Priority:
    1. Valid start_date and end_date -> programmatically calculated calendar-aware duration
    2. Explicit duration (when dates are missing, partial, or invalid)
    3. 'Duration not specified'
    """
    # If both dates are provided, attempt calculation
    if start_date and end_date:
        p1 = parse_date_str(start_date)
        p2 = parse_date_str(end_date)
        if p1 and p2:
            try:
                d1 = date(p1[0], p1[1], p1[2])
                d2 = date(p2[0], p2[1], p2[2])
                
                # Check for invalid date range (end before start)
                if d2 < d1:
                    if explicit_duration and explicit_duration.strip() and explicit_duration.strip().lower() not in ["none", "null", "duration not specified"]:
                        return explicit_duration.strip()
                    return "Duration not specified"
                
                if d2 == d1:
                    return "0 days"
                
                # Elapsed days
                diff_days = (d2 - d1).days
                
                # Short duration (< 25 days)
                if diff_days < 25:
                    return f"{diff_days} day" if diff_days == 1 else f"{diff_days} days"
                
                # Calculate calendar difference (years, months, days)
                y = d2.year - d1.year
                m = d2.month - d1.month
                d = d2.day - d1.day
                
                if d < 0:
                    prev_month = d2.month - 1 if d2.month > 1 else 12
                    prev_year = d2.year if d2.month > 1 else d2.year - 1
                    import calendar
                    days_in_prev = calendar.monthrange(prev_year, prev_month)[1]
                    d += days_in_prev
                    m -= 1
                    
                if m < 0:
                    m += 12
                    y -= 1
                
                # 1. Period of ~1 month (e.g. 1 Jan to 31 Jan = 30 days, or 17 Apr to 18 May = 31 days)
                if y == 0 and m == 0 and diff_days >= 25:
                    return "1 month"
                
                # 2. Whole years with negligible remaining days (<= 3 days)
                if y > 0 and m == 0 and d <= 3:
                    return f"{y} year" if y == 1 else f"{y} years"
                
                # 3. Years + months with negligible remaining days (<= 3 days)
                if y > 0 and m > 0 and d <= 3:
                    yr_str = f"{y} year" if y == 1 else f"{y} years"
                    mo_str = f"{m} month" if m == 1 else f"{m} months"
                    return f"{yr_str} {mo_str}"
                
                # 4. Months with negligible remaining days (<= 3 days)
                if y == 0 and m > 0 and d <= 3:
                    return f"{m} month" if m == 1 else f"{m} months"
                
                # 5. Mixed duration with days >= 25 -> round up to next month
                if y == 0 and m > 0:
                    if d >= 25:
                        tot_m = m + 1
                        return f"{tot_m} months"
                    return f"{m} month {d} days" if m == 1 else f"{m} months {d} days"
                
                if y > 0 and m > 0:
                    yr_str = f"{y} year" if y == 1 else f"{y} years"
                    mo_str = f"{m} month" if m == 1 else f"{m} months"
                    return f"{yr_str} {mo_str}"
                
                if y > 0:
                    return f"{y} year" if y == 1 else f"{y} years"
                
                tot_m = max(1, round(diff_days / 30.44))
                return f"{tot_m} month" if tot_m == 1 else f"{tot_m} months"
                
            except Exception:
                pass

    # If dates missing or invalid, fall back to explicit duration
    if explicit_duration and explicit_duration.strip() and explicit_duration.strip().lower() not in ["none", "null", "duration not specified"]:
        return explicit_duration.strip()

    return "Duration not specified"


def calculate_duration_detailed(start_str: str, end_str: str) -> Dict[str, Any]:
    """
    Calculate the detailed duration between two date strings.
    Returns dictionary with 'years', 'months', 'days', 'total_months', 'fractional_years', and 'display'.
    Example: '17 Apr 2026' to '18 May 2026' -> 1 month, 0.08 years.
    """
    start = parse_date_str(start_str)
    end = parse_date_str(end_str)
    
    if not start or not end:
        return {
            "years": 0,
            "months": 0,
            "days": 0,
            "total_months": 0,
            "fractional_years": 0.0,
            "display": "0 yrs",
        }
    
    try:
        d1 = date(start[0], start[1], start[2])
        d2 = date(end[0], end[1], end[2])
        if d2 < d1:
            return {
                "years": 0, "months": 0, "days": 0, "total_months": 0, "fractional_years": 0.0, "display": "0 yrs"
            }
        
        diff_days = (d2 - d1).days
        total_months = max(1, round(diff_days / 30.44))
    except Exception:
        # Fallback to month calculation
        total_months = max(1, (end[0] - start[0]) * 12 + (end[1] - start[1]))
        diff_days = total_months * 30

    years = total_months // 12
    remaining_months = total_months % 12
    fractional_years = round(total_months / 12.0, 2)
    
    if total_months < 12:
        display = f"{total_months} month" if total_months == 1 else f"{total_months} months"
    elif remaining_months == 0:
        display = f"{years} yr" if years == 1 else f"{years} yrs"
    else:
        display = f"{years} yr {remaining_months} mo" if years == 1 else f"{years} yrs {remaining_months} mos"

    return {
        "years": years,
        "months": remaining_months,
        "days": diff_days,
        "total_months": total_months,
        "fractional_years": fractional_years,
        "display": display,
    }


def calculate_duration_years(start_str: str, end_str: str) -> float:
    """Calculate fractional duration in years."""
    res = calculate_duration_detailed(start_str, end_str)
    return res["fractional_years"]


def extract_all_date_ranges(text: str) -> List[Tuple[str, str, float, str]]:
    """
    Find all date ranges in a text block and calculate their durations.
    Returns a list of (start_date, end_date, duration_in_years, display_string).
    """
    results = []
    for match in DATE_RANGE_REGEX.finditer(text):
        start = match.group("start").strip()
        end = match.group("end").strip()
        dur_info = calculate_duration_detailed(start, end)
        results.append((start, end, dur_info["fractional_years"], dur_info["display"]))
    return results


def clean_bullet_points(text: str) -> str:
    """Normalize bullet point characters to standard markdown dashes."""
    if not text:
        return ""
    bullets = ["•", "●", "○", "■", "▪", "▫", "◆", "◇", "➢", "", "–", "—", "►", "✓", "✔", "·", "・", "∙", "·", "•", "▪", "▫"]
    pattern = r"^\s*(?:" + "|".join(re.escape(b) for b in set(bullets)) + r")+\s*"
    lines = text.split("\n")
    cleaned_lines = []
    for line in lines:
        cleaned_line = re.sub(pattern, "- ", line)
        cleaned_lines.append(cleaned_line)
    return "\n".join(cleaned_lines)
