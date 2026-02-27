"""
Common utilities shared across all document parsers.
- Date extraction
- OCR digit fixing
"""
import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def fix_ocr_digits(text: str) -> str:
    """Fix common OCR misreadings for digits"""
    replacements = {
        'O': '0', 'o': '0', 'D': '0', 'Q': '0',
        'I': '1', 'l': '1', 'L': '1', '|': '1', 'i': '1',
        '?': '7', 'T': '7',
        'S': '5', 's': '5',
        'B': '8',
        'G': '6', 'g': '9',
        'A': '4',
        'Z': '2', 'z': '2',
    }
    result = text
    for old, new in replacements.items():
        result = result.replace(old, new)
    return result


def extract_date(text: str, keyword: str = "Lahir") -> Optional[str]:
    """Extract date near a keyword"""
    for line in text.split('\n'):
        if keyword.lower() in line.lower():
            # DD-MM-YYYY or DD/MM/YYYY
            m = re.search(r'(\d{1,2})[-/](\d{1,2})[-/](\d{4})', line)
            if m:
                return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
            # DD MMM YYYY
            m = re.search(r'(\d{1,2})\s+(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\s+(\d{4})', line, re.IGNORECASE)
            if m:
                return f"{m.group(1)} {m.group(2)} {m.group(3)}"
    return None


def empty_result() -> dict:
    """Return a blank extraction result template"""
    return {
        'document_type': 'UNKNOWN',
        'no_identitas': None,
        'nama': None,
        'tempat_lahir': None,
        'tanggal_lahir': None,
        'alamat': None,
        'no_paspor': None,
        'tanggal_paspor': None,
        'kota_paspor': None,
        'no_visa': None,
        'provinsi': None,
        'kabupaten': None,
        'kecamatan': None,
        'kelurahan': None
    }
