"""
Passport Parser - Indonesian Passport (Paspor)

Extracts: Name, Passport Number, Tempat Lahir, Tanggal Lahir,
          Tanggal Paspor (Expiry), Kota Paspor (Issuing Office)

Uses both MRZ (Machine Readable Zone) and Visual text extraction.
"""
import re
import logging
from typing import Dict, Optional

from ..cleaner import validate_and_clean_name
from .common import extract_date, empty_result

logger = logging.getLogger(__name__)


# =============================================================================
# MRZ (MACHINE READABLE ZONE) PARSER - ICAO STANDARD
# =============================================================================

def clean_mrz_line(line: str) -> str:
    """
    AGGRESSIVE MRZ line cleaner - handles OCR misreadings of < character
    """
    if not line:
        return ""
    
    result = line.upper()
    
    # === PASS 1: Replace obvious bracket-like characters ===
    bracket_replacements = {
        '(': '<', ')': '<', 
        '[': '<', ']': '<',
        '{': '<', '}': '<',
        '«': '<', '»': '<',
        '£': '<', '¢': '<',
        '|': '<',
    }
    for old, new in bracket_replacements.items():
        result = result.replace(old, new)
    
    # === PASS 2: Replace letters commonly misread as < ===
    chevron_lookalikes = ['K', 'C', 'E', 'R', 'X', 'V', 'Y']
    
    for _ in range(5):  # Multiple passes to catch nested patterns
        for char in chevron_lookalikes:
            result = result.replace(f'<{char}<', '<<<')
            result = result.replace(f'<{char}{char}<', '<<<<')
        
        result = result.replace('K<', '<<')
        result = result.replace('<K', '<<')
        result = result.replace('C<', '<<')
        result = result.replace('<C', '<<')
        
    # === PASS 3: Clean trailing garbage ===
    trailing_match = re.search(r'(<{3,})([KCERXVY]+)$', result)
    if trailing_match:
        result = result[:trailing_match.start()] + '<' * (len(trailing_match.group(1)) + len(trailing_match.group(2)))
    
    # === PASS 4: Remove any remaining non-MRZ characters ===
    result = re.sub(r'[^A-Z0-9<]', '', result)
    
    # === PASS 5: Normalize multiple < to clean sequence ===
    result = re.sub(r'<{3,}', lambda m: '<' * len(m.group()), result)
    
    return result


def clean_mrz_name_section(text: str) -> str:
    """Extra-aggressive cleaning specifically for the name section of MRZ Line 1"""
    if not text:
        return ""
    
    result = text.upper()
    
    # Replace all chevron-lookalikes
    for char in ['K', 'C', 'E', 'R', 'X', 'V']:
        result = re.sub(f'<{char}+<', lambda m: '<' * len(m.group()), result)
        result = re.sub(f'<{char}+$', lambda m: '<' * len(m.group()), result)
    
    # Clean up: remove any character that's not A-Z or <
    result = re.sub(r'[^A-Z<]', '', result)
    
    # Remove trailing single letters followed by nothing (garbage)
    result = re.sub(r'<[A-Z]$', '<', result)
    
    return result


def fix_mrz_number(text: str) -> str:
    """Fix OCR errors specifically for numeric fields in MRZ"""
    replacements = {
        'O': '0', 'Q': '0', 'D': '0',
        'I': '1', 'L': '1', 'l': '1', '|': '1',
        'S': '5', 's': '5',
        'B': '8',
        'G': '6', 'g': '9',
        'Z': '2', 'z': '2',
        'T': '7',
        'A': '4',
    }
    result = text
    for old, new in replacements.items():
        result = result.replace(old, new)
    return result


def parse_mrz(text: str) -> Dict[str, Optional[str]]:
    """Parse Machine Readable Zone (MRZ) from passport - ICAO 9303 Standard"""
    result = {
        'passport_number': None,
        'surname': None,
        'given_names': None,
        'name': None,
        'date_of_birth': None,
        'date_of_expiry': None,
        'sex': None,
        'nationality': None
    }
    
    lines = text.split('\n')
    mrz_line1 = None
    mrz_line2 = None
    
    # Strategy 1: Find lines starting with P< or V<
    for i, line in enumerate(lines):
        cleaned = clean_mrz_line(line)
        
        # Check for Passport (P<) or Visa (V<) or generic IDN marker
        if cleaned.startswith('P<') or cleaned.startswith('V<') or 'P<IDN' in cleaned or 'V<IDN' in cleaned:
            if len(cleaned) >= 30:
                mrz_line1 = cleaned
                if i + 1 < len(lines):
                    next_cleaned = clean_mrz_line(lines[i + 1])
                    if len(next_cleaned) >= 30 and next_cleaned[0].isalnum():
                        mrz_line2 = next_cleaned
                break
    
    # Strategy 2: Find lines with many < characters (MRZ signature)
    if mrz_line1 is None:
        for i, line in enumerate(lines):
            cleaned = clean_mrz_line(line)
            lt_count = cleaned.count('<')
            if lt_count >= 5 and len(cleaned) >= 30:
                if mrz_line1 is None:
                    mrz_line1 = cleaned
                elif mrz_line2 is None:
                    mrz_line2 = cleaned
                    break
    
    if not mrz_line1:
        logger.warning("MRZ Line 1 not found!")
        return result
    
    # === PARSE LINE 1: Names ===
    start_index = 5
    if mrz_line1.startswith('P<') or mrz_line1.startswith('V<'):
        if len(mrz_line1) > 5:
            start_index = 5
    
    raw_name_section = mrz_line1[start_index:]
    
    # Clean the section first
    clean_section = raw_name_section.replace('<<<', '<<').replace('<<<<', '<<')
    parts = clean_section.split('<<')
    
    surname = parts[0].replace('<', ' ').strip()
    given_name = ""
    
    if len(parts) > 1:
        given_name = parts[1].replace('<', ' ').strip()
        final_name = f"{given_name} {surname}".strip()
    else:
        # Fallback if double chevron lost
        final_name = clean_section.replace('<', ' ').strip()
        # Remove trailing single letters often misread
        final_name = re.sub(r'\s[A-Z]$', '', final_name)
        surname = final_name

    result['name'] = final_name
    result['surname'] = surname
    result['given_names'] = given_name
    
    # === PARSE LINE 2: Passport Number, DOB, Expiry ===
    if mrz_line2 and len(mrz_line2) >= 20:
        # Passport Number
        passport_raw = mrz_line2[0:9]
        passport_clean = passport_raw.replace('<', '')
        passport_clean = fix_mrz_number(passport_clean)
        if passport_clean:
            result['passport_number'] = passport_clean
        
        # Nationality (Chars 10-12)
        if len(mrz_line2) >= 13:
            result['nationality'] = mrz_line2[10:13].replace('<', '')
        
        # Date of Birth (Chars 13-18) YYMMDD
        if len(mrz_line2) >= 19:
            dob_raw = mrz_line2[13:19]
            dob_fixed = fix_mrz_number(dob_raw)
            if len(dob_fixed) == 6 and dob_fixed.isdigit():
                yy = int(dob_fixed[0:2])
                mm = dob_fixed[2:4]
                dd = dob_fixed[4:6]
                year = 2000 + yy if yy <= 30 else 1900 + yy
                result['date_of_birth'] = f"{year}-{mm}-{dd}"
        
        # Sex (Char 20)
        if len(mrz_line2) >= 21:
            sex_char = mrz_line2[20]
            if sex_char in ['M', 'F']:
                result['sex'] = sex_char
        
        # Expiry Date (Chars 21-26) YYMMDD
        if len(mrz_line2) >= 27:
            exp_raw = mrz_line2[21:27]
            exp_fixed = fix_mrz_number(exp_raw)
            if len(exp_fixed) == 6 and exp_fixed.isdigit():
                yy = int(exp_fixed[0:2])
                mm = exp_fixed[2:4]
                dd = exp_fixed[4:6]
                year = 2000 + yy
                result['date_of_expiry'] = f"{year}-{mm}-{dd}"
    
    return result


# =============================================================================
# PASSPORT VISUAL FIELD EXTRACTORS
# =============================================================================

def extract_passport_number(text: str) -> Optional[str]:
    """Extract passport number from visual text"""
    m = re.search(r'(?:Passport|Paspor)\s*(?:No\.?|Number)?[:\s]*([A-Z]\d{6,8})', text, re.IGNORECASE)
    if m:
        return m.group(1).upper()
    m = re.search(r'\b([A-Z]\d{7})\b', text)
    if m:
        return m.group(1)
    return None


def extract_name_passport(text: str) -> Optional[str]:
    """Extract name from passport visual text"""
    lines = text.split('\n')
    
    # Strategy 1: Look for "Nama Lengkap" or "Full Name"
    for i, line in enumerate(lines):
        if re.search(r'(?:Given\s*Names?|Nama\s*Lengkap|Full\s*Name)', line, re.IGNORECASE):
            # Attempt 1: Same line content
            same_line = re.sub(r'.*(?:Given\s*Names?|Nama\s*Lengkap|Full\s*Name)[:\s]*', '', line, flags=re.IGNORECASE).strip()
            if validate_and_clean_name(same_line):
                return validate_and_clean_name(same_line)
            
            # Attempt 2: Next line content (Common in IDN passports)
            if i + 1 < len(lines):
                next_line = lines[i+1].strip()
                if validate_and_clean_name(next_line):
                    return validate_and_clean_name(next_line)
                    
    # Strategy 2: Fallback to old regex
    given = re.search(r'(?:Given\s*Names?|Nama\s*Lengkap)[:\s]+([A-Z\s]+)', text, re.IGNORECASE)
    surname = re.search(r'(?:Surname|Nama\s*Keluarga)[:\s]+([A-Z\s]+)', text, re.IGNORECASE)
    
    name_parts = []
    if given:
        name_parts.append(given.group(1).strip())
    if surname:
        name_parts.append(surname.group(1).strip())
    
    if name_parts:
        return ' '.join(name_parts)
        
    return None


def extract_passport_place_of_birth(text: str) -> Optional[str]:
    """
    Extract Place of Birth from Indonesian passport visual text.
    Labels: 'TEMPAT LAHIR', 'PLACE OF BIRTH'
    """
    lines = text.split('\n')
    
    # Blacklist: words that are NOT places but appear near 'LAHIR' / 'BIRTH'
    place_blacklist = ['KELAMIN', 'SEX', 'PASPOR', 'PASSPORT', 'TYPE', 'CODE',
                       'PENGELUARAN', 'ISSUE', 'NATIONALITY', 'KEWARGANEGARAAN',
                       'HABIS', 'BERLAKU', 'EXPIRY', 'NAMA', 'NAME', 'FULL',
                       'TGL', 'DATE', 'KANTOR', 'OFFICE', 'REG']
    
    for i, line in enumerate(lines):
        line_upper = line.upper()
        
        # Strategy 1: Look for "TEMPAT LAHIR" or "PLACE OF BIRTH"
        if 'TEMPAT LAHIR' in line_upper or 'PLACE OF BIRTH' in line_upper:
            # Same line: after the label
            m = re.search(r'(?:TEMPAT\s*LAHIR|PLACE\s*OF\s*BIRTH)[:\s/|]*([A-Za-z\s]{2,})', line, re.IGNORECASE)
            if m:
                place = m.group(1).strip().upper()
                place = re.sub(r'[^A-Z\s]', '', place).strip()
                # Filter blacklist
                if len(place) >= 2 and not any(bl in place for bl in place_blacklist):
                    return place
            
            # Next line
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                place = re.sub(r'[^A-Za-z\s]', '', next_line).strip().upper()
                if len(place) >= 2 and not any(bl in place for bl in place_blacklist):
                    return place
    
    return None


def extract_passport_date_of_birth(text: str) -> Optional[str]:
    """
    Extract Date of Birth from Indonesian passport visual text.
    Labels: 'TGL. LAHIR', 'TGL LAHIR', 'DATE OF BIRTH'
    Common formats: '04 MAR 1972', '04-03-1972'
    """
    lines = text.split('\n')
    
    for line in lines:
        line_upper = line.upper()
        
        # Look for DOB label
        if any(kw in line_upper for kw in ['TGL. LAHIR', 'TGL LAHIR', 'DATE OF BIRTH', 'TGL.LAHIR']):
            # Extract date pattern: DD MMM YYYY or DD-MM-YYYY
            m = re.search(r'(\d{1,2})\s*(JAN|FEB|MAR|APR|MAY|MEI|JUN|JUL|AUG|AGU|SEP|OCT|OKT|NOV|DEC|DES)\s*(\d{4})', line, re.IGNORECASE)
            if m:
                return f"{m.group(1)} {m.group(2).upper()} {m.group(3)}"
            
            m = re.search(r'(\d{1,2})[-/](\d{1,2})[-/](\d{4})', line)
            if m:
                return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    
    # Fallback: look for any date near "lahir" or "birth"
    for line in lines:
        if 'lahir' in line.lower() or 'birth' in line.lower():
            m = re.search(r'(\d{1,2})\s*(JAN|FEB|MAR|APR|MAY|MEI|JUN|JUL|AUG|AGU|SEP|OCT|OKT|NOV|DEC|DES)\s*(\d{4})', line, re.IGNORECASE)
            if m:
                return f"{m.group(1)} {m.group(2).upper()} {m.group(3)}"
    
    return None


def extract_passport_date_of_issue(text: str) -> Optional[str]:
    """
    Extract Date of Issue from Indonesian passport visual text.
    Labels: 'TGL. PENGELUARAN', 'DATE OF ISSUE'
    """
    lines = text.split('\n')
    
    for line in lines:
        line_upper = line.upper()
        
        if any(kw in line_upper for kw in ['TGL. PENGELUARAN', 'TGL PENGELUARAN', 'DATE OF ISSUE']):
            m = re.search(r'(\d{1,2})\s*(JAN|FEB|MAR|APR|MAY|MEI|JUN|JUL|AUG|AGU|SEP|OCT|OKT|NOV|DEC|DES)\s*(\d{4})', line, re.IGNORECASE)
            if m:
                return f"{m.group(1)} {m.group(2).upper()} {m.group(3)}"
            m = re.search(r'(\d{1,2})[-/](\d{1,2})[-/](\d{4})', line)
            if m:
                return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    
    return None


def extract_passport_date_of_expiry(text: str) -> Optional[str]:
    """
    Extract Date of Expiry from Indonesian passport visual text.
    Labels: 'TGL. HABIS BERLAKU', 'DATE OF EXPIRY'
    """
    lines = text.split('\n')
    
    for line in lines:
        line_upper = line.upper()
        
        if any(kw in line_upper for kw in ['TGL. HABIS BERLAKU', 'TGL HABIS', 'DATE OF EXPIRY']):
            m = re.search(r'(\d{1,2})\s*(JAN|FEB|MAR|APR|MAY|MEI|JUN|JUL|AUG|AGU|SEP|OCT|OKT|NOV|DEC|DES)\s*(\d{4})', line, re.IGNORECASE)
            if m:
                return f"{m.group(1)} {m.group(2).upper()} {m.group(3)}"
            m = re.search(r'(\d{1,2})[-/](\d{1,2})[-/](\d{4})', line)
            if m:
                return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    
    # Broader fallback: "BERLAKU" without "HABIS" prefix
    for line in lines:
        line_upper = line.upper()
        if 'BERLAKU' in line_upper and 'HINGGA' not in line_upper:  # exclude KTP "berlaku hingga"
            m = re.search(r'(\d{1,2})\s*(JAN|FEB|MAR|APR|MAY|MEI|JUN|JUL|AUG|AGU|SEP|OCT|OKT|NOV|DEC|DES)\s*(\d{4})', line, re.IGNORECASE)
            if m:
                return f"{m.group(1)} {m.group(2).upper()} {m.group(3)}"
    
    return None


def extract_passport_issuing_office(text: str) -> Optional[str]:
    """
    Extract Issuing Office (Kota Paspor) from Indonesian passport visual text.
    Labels: 'KANTOR YANG MENGELUARKAN', 'ISSUING OFFICE'
    """
    lines = text.split('\n')
    
    # Blacklist: label fragments that aren't actual city names
    office_blacklist = ['YANG', 'MENGELUARKAN', 'ISSUING', 'OFFICE', 'KANTOR',
                        'PASSPORT', 'PASPOR', 'TYPE', 'CODE', 'DATE', 'TGL']
    
    for i, line in enumerate(lines):
        line_upper = line.upper()
        
        if 'KANTOR' in line_upper or 'ISSUING OFFICE' in line_upper or 'MENGELUARKAN' in line_upper:
            # Try next line first (value is usually on a separate line)
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                office = re.sub(r'[^A-Za-z\s]', '', next_line).strip().upper()
                if len(office) >= 2 and not any(bl in office for bl in office_blacklist):
                    return office
            
            # Same line: try to extract after the full label
            m = re.search(r'(?:MENGELUARKAN|ISSUING\s*OFFICE)\s*[:\s/|]+\s*([A-Za-z\s]{2,})', line, re.IGNORECASE)
            if m:
                office = m.group(1).strip().upper()
                office = re.sub(r'[^A-Z\s]', '', office).strip()
                if len(office) >= 2 and not any(bl in office for bl in office_blacklist):
                    return office
    
    return None


# =============================================================================
# MAIN PASSPORT EXTRACTION
# =============================================================================

def extract_passport_data(text: str) -> Dict[str, Optional[str]]:
    """
    Extract all fields from Passport document.
    Uses both MRZ and visual text, with smart fallback strategy.
    """
    result = empty_result()
    result['document_type'] = 'PASSPORT'
    
    mrz_data = parse_mrz(text)
    
    # --- NAME: Smart MRZ vs Visual selection ---
    mrz_name = mrz_data.get('name')
    visual_name = extract_name_passport(text)
    
    final_name = mrz_name
    
    if not mrz_name:
        final_name = visual_name
    elif visual_name:
        # If MRZ name is suspicious, prefer visual
        if ' ' not in mrz_name and ' ' in visual_name:
            final_name = visual_name
        elif '<' in mrz_name or re.search(r'(.)\1\1', mrz_name):
            final_name = visual_name
        elif len(visual_name) > len(mrz_name) + 3:
            final_name = visual_name
    
    result['nama'] = final_name
    
    # --- PASSPORT NUMBER: MRZ first, then Visual ---
    if mrz_data['passport_number']:
        result['no_paspor'] = mrz_data['passport_number']
    else:
        result['no_paspor'] = extract_passport_number(text)
    
    # --- DATE OF BIRTH: Visual first (more readable), MRZ fallback ---
    visual_dob = extract_passport_date_of_birth(text)
    result['tanggal_lahir'] = visual_dob or mrz_data.get('date_of_birth') or extract_date(text, "Birth")
    
    # --- PLACE OF BIRTH: Visual only (MRZ does not contain this) ---
    result['tempat_lahir'] = extract_passport_place_of_birth(text)
    
    # --- DATE OF EXPIRY: Visual first, MRZ fallback ---
    visual_expiry = extract_passport_date_of_expiry(text)
    result['tanggal_paspor'] = visual_expiry or mrz_data.get('date_of_expiry') or extract_date(text, "Issue")
    
    # --- ISSUING OFFICE (Kota Paspor) ---
    result['kota_paspor'] = extract_passport_issuing_office(text)
    
    result['no_identitas'] = result['no_paspor']
    
    return result
