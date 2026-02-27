"""
Data validation and formatting utilities
"""
import re
from datetime import datetime
from typing import Optional


def validate_nik(nik: str) -> bool:
    """Validate NIK (must be exactly 16 digits)"""
    if not nik:
        return False
    return bool(re.match(r'^\d{16}$', nik))


def validate_date(date_str: str, format: str = "%Y-%m-%d") -> bool:
    """Validate date string with specific format"""
    if not date_str:
        return False
    try:
        datetime.strptime(date_str, format)
        return True
    except ValueError:
        return False


def convert_date_format(date_str: str, from_format: str, to_format: str = "%Y-%m-%d") -> Optional[str]:
    """
    Convert date from one format to another
    Example: "25-06-1992", "%d-%m-%Y" -> "1992-06-25"
    """
    if not date_str:
        return None
    try:
        date_obj = datetime.strptime(date_str, from_format)
        return date_obj.strftime(to_format)
    except ValueError:
        return None


def normalize_text(text: str) -> str:
    """Normalize text by removing extra whitespace and converting to uppercase"""
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    return text.upper()


def clean_field(value: Optional[str]) -> Optional[str]:
    """Clean a field value by normalizing and validating"""
    if not value:
        return None
    cleaned = normalize_text(value)
    return cleaned if cleaned else None
