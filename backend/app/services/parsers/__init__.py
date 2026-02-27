"""
Parsers Package - Modular document parsing

Each document type has its own parser file:
- ktp_parser.py    → KTP (Indonesian ID Card)
- passport_parser.py → Passport
- visa_parser.py   → Visa

Shared utilities live in common.py.
The main parser.py orchestrates detection and delegates to the right parser.
"""

from .common import extract_date, fix_ocr_digits
from .ktp_parser import extract_ktp_data
from .passport_parser import extract_passport_data
from .visa_parser import extract_visa_data
