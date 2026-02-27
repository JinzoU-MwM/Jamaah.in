"""
Document Parser - Thin Orchestrator

Detects document type and delegates extraction to the appropriate parser:
- parsers/ktp_parser.py       → KTP (Indonesian ID)
- parsers/passport_parser.py  → Passport
- parsers/visa_parser.py      → Visa

Each parser is self-contained so a bug in one doesn't affect others.
"""
import re
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# Import sub-parsers
from .parsers.ktp_parser import extract_ktp_data
from .parsers.passport_parser import extract_passport_data
from .parsers.visa_parser import extract_visa_data
from .parsers.common import empty_result

# Re-export for backward compatibility (used by tests)
from .parsers.ktp_parser import extract_nik
from .parsers.passport_parser import clean_mrz_line, parse_mrz
from .parsers.common import fix_ocr_digits, extract_date


# =============================================================================
# DOCUMENT TYPE DETECTION
# =============================================================================

def detect_document_type(text: str) -> str:
    """
    Smart document type detection based on text patterns
    
    Priority:
    1. VISA keywords (Specific > Generic)
    2. KTP keywords
    3. PASSPORT keywords
    4. KTP/Passport Patterns
    """
    text_upper = text.upper()
    
    # 1. Check for VISA keywords (Priority over MRZ because Visas also have MRZ)
    visa_keywords = ['VISA', 'KINGDOM OF SAUDI', 'KSA', 'MOFA', 'KEDUTAAN', 'EMBASSY', 'R.S.A']
    if 'VISA' in text_upper and ('SAUDI' in text_upper or 'NUMBER' in text_upper or 'NO' in text_upper):
        return "VISA"
    if sum(1 for kw in visa_keywords if kw in text_upper) >= 2:
        return "VISA"

    # 2. Check for KTP keywords
    ktp_keywords = ['PROVINSI', 'KABUPATEN', 'KECAMATAN', 'KELURAHAN', 
                    'NIK', 'RT/RW', 'BERLAKU HINGGA', 'KARTU TANDA PENDUDUK']
    if sum(1 for kw in ktp_keywords if kw in text_upper) >= 2:
        return "KTP"

    # 3. Check for PASSPORT keywords
    passport_keywords = ['PASSPORT', 'PASPOR', 'DATE OF ISSUE', 'DATE OF EXPIRY', 
                         'REPUBLIC OF INDONESIA', 'TANGGAL HABIS BERLAKU', 'IMIGRASI']
    if sum(1 for kw in passport_keywords if kw in text_upper) >= 2:
        return "PASSPORT"

    # 4. Check for MRZ (Machine Readable Zone)
    if 'P<' in text_upper or 'P<IDN' in text_upper:
        return "PASSPORT"
    if 'V<' in text_upper or 'V<IDN' in text_upper:
        return "VISA"
        
    # Generic MRZ fallback (<<<)
    if '<<<' in text or re.search(r'[A-Z]{2}<[A-Z]+<<', text_upper):
        if 'SAUDI' in text_upper or 'ARABIA' in text_upper:
            return "VISA"
        return "PASSPORT"
    
    # 5. Default fallback - try to identify by patterns
    if re.search(r'\d{16}', text):
        return "KTP"
    if re.search(r'[A-Z]\d{7}', text):
        return "PASSPORT"
    
    return "UNKNOWN"


# =============================================================================
# MAIN EXTRACTION FUNCTION
# =============================================================================

def extract_document_data(text: str) -> Dict[str, Optional[str]]:
    """
    Smart extraction based on document type.
    Detects the type first, then delegates to the appropriate sub-parser.
    """
    doc_type = detect_document_type(text)
    logger.info(f"Detected document type: {doc_type}")
    
    if doc_type == "PASSPORT":
        return extract_passport_data(text)
    elif doc_type == "VISA":
        return extract_visa_data(text)
    elif doc_type == "KTP":
        return extract_ktp_data(text)
    else:
        result = empty_result()
        result['document_type'] = doc_type
        return result
