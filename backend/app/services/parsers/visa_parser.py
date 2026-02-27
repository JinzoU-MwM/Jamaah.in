"""
Visa Parser - Saudi Arabia Visa / Travel Visa

Extracts: Name, Passport Number, Visa Number
Uses MRZ (shared with passport_parser) and Visa-specific patterns.
"""
import re
import logging
from typing import Dict, Optional

from ..cleaner import validate_and_clean_name
from .common import empty_result
from .passport_parser import parse_mrz, extract_passport_number, extract_name_passport

logger = logging.getLogger(__name__)


# =============================================================================
# VISA-SPECIFIC FIELD EXTRACTORS
# =============================================================================

def extract_visa_number(text: str) -> Optional[str]:
    """Extract visa number"""
    m = re.search(r'(?:Visa\s*(?:No\.?|Number)?)[:\s]*([A-Z0-9]{8,20})', text, re.IGNORECASE)
    if m:
        return m.group(1).upper()
    m = re.search(r'\b([A-Z]{2}\d{4}[A-Z]+\d+)\b', text)
    if m:
        return m.group(1)
    return None


# =============================================================================
# MAIN VISA EXTRACTION
# =============================================================================

def extract_visa_data(text: str) -> Dict[str, Optional[str]]:
    """
    Extract all fields from Visa document.
    Uses MRZ for name/passport number, and Visa-specific patterns for visa number.
    """
    result = empty_result()
    result['document_type'] = 'VISA'
    
    mrz_data = parse_mrz(text)
    
    # --- NAME: Prefer MRZ name (usually more accurate for Visa) ---
    if mrz_data['name']:
        result['nama'] = mrz_data['name']
    else:
        result['nama'] = extract_name_passport(text)
        
    # --- PASSPORT NUMBER: MRZ first, then Visual ---
    if mrz_data['passport_number']:
        result['no_paspor'] = mrz_data['passport_number']
    else:
        result['no_paspor'] = extract_passport_number(text)
        
    # --- VISA NUMBER ---
    result['no_visa'] = extract_visa_number(text)
    result['no_identitas'] = result['no_visa']
    
    return result
