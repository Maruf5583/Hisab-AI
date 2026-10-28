import re
from decimal import Decimal, InvalidOperation
from datetime import date, datetime
from typing import Optional

# Bengali to English digit mapping
BENGALI_DIGITS = "০১২৩৪৫৬৭৮৯"
ENGLISH_DIGITS = "0123456789"
BENGALI_TO_ENGLISH_TABLE = str.maketrans(BENGALI_DIGITS, ENGLISH_DIGITS)
ENGLISH_TO_BENGALI_TABLE = str.maketrans(ENGLISH_DIGITS, BENGALI_DIGITS)


def normalize_bengali_digits(text: str) -> str:
    """Translate Bengali numerals (০-৯) into standard English numerals (0-9)."""
    if not text:
        return ""
    return text.translate(BENGALI_TO_ENGLISH_TABLE)


def to_bengali_digits(text: str) -> str:
    """Translate English numerals (0-9) into Bengali numerals (০-৯)."""
    if not text:
        return ""
    return text.translate(ENGLISH_TO_BENGALI_TABLE)


def parse_monetary_amount(text: str) -> Optional[Decimal]:
    """Extract and parse monetary amounts from Bengali/English text into Decimal.
    
    Handles:
    - '১৫,৫০০.০০' -> Decimal('15500.00')
    - '৳ ১,২০,০০০/-' -> Decimal('120000.00')
    - '12,500.50 Tk' -> Decimal('12500.50')
    - '5000' -> Decimal('5000.00')
    """
    if not text:
        return None

    # Normalize Bengali digits first
    normalized = normalize_bengali_digits(text)

    # Strip currency symbols and common suffixes
    cleaned = re.sub(r"[৳$£€₹]|(?:tk|taka|bdt|\/-|\/=)", "", normalized, flags=re.IGNORECASE).strip()

    # Match numeric patterns: e.g. 15,500.00 or 15500 or 15,500
    match = re.search(r"[-+]?\d+(?:,\d+)*(?:\.\d+)?", cleaned)
    if not match:
        return None

    num_str = match.group(0).replace(",", "")
    try:
        val = Decimal(num_str).quantize(Decimal("0.01"))
        return val
    except (InvalidOperation, TypeError):
        return None


def parse_flexible_date(text: str) -> Optional[date]:
    """Parse dates from Bengali and English representations.
    
    Supports:
    - '২৮/১০/২০২৬' or '28/10/2026'
    - '২৮-১০-২০২৬' or '28-10-2026'
    - '২৮.১০.২০২৬' or '28.10.2026'
    - '2026-10-28'
    """
    if not text:
        return None

    normalized = normalize_bengali_digits(text).strip()

    # Common date formats in Bangladesh business documents
    formats = [
        r"(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{4})",  # DD/MM/YYYY
        r"(\d{4})[/\-.](\d{1,2})[/\-.](\d{1,2})",  # YYYY-MM-DD
    ]

    for pattern in formats:
        match = re.search(pattern, normalized)
        if match:
            groups = match.groups()
            try:
                if len(groups[0]) == 4:  # YYYY-MM-DD
                    year, month, day = int(groups[0]), int(groups[1]), int(groups[2])
                else:  # DD-MM-YYYY
                    day, month, year = int(groups[0]), int(groups[1]), int(groups[2])
                return date(year, month, day)
            except ValueError:
                continue

    return None
