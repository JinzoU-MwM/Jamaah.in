"""
KTP Parser - Indonesian ID Card (Kartu Tanda Penduduk)

Extracts: NIK, Nama, Tempat/Tanggal Lahir, Alamat,
          Provinsi, Kabupaten, Kecamatan, Kelurahan

Handles noisy OCR from phone photos of ID cards.
"""
import re
import logging
from typing import Dict, Optional

from ..cleaner import validate_and_clean_name
from .common import fix_ocr_digits, extract_date, empty_result

logger = logging.getLogger(__name__)


# =============================================================================
# KTP FIELD EXTRACTORS
# =============================================================================

def extract_nik(text: str) -> Optional[str]:
    """Extract NIK (16 digits) with fuzzy matching"""
    clean_text = re.sub(r'\s+', ' ', text)
    
    # Strategy 1: Direct 16-digit match
    nik_match = re.search(r'\b(\d{16})\b', clean_text)
    if nik_match:
        return nik_match.group(1)
    
    # Strategy 2: After "NIK" keyword
    nik_pattern = re.search(r'NIK[:\s=]*([0-9OoIlLDSBZz?|\-\)\(]{14,22})', clean_text, re.IGNORECASE)
    if nik_pattern:
        fixed = fix_ocr_digits(nik_pattern.group(1))
        digits = re.sub(r'\D', '', fixed)
        if len(digits) >= 16:
            return digits[:16]
            
    # Strategy 3: Any 16+ character number-like sequence
    sequences = re.findall(r'[0-9OoIlLDSBZz?|\-\)\(]{14,22}', clean_text)
    for seq in sequences:
        fixed = fix_ocr_digits(seq)
        digits = re.sub(r'\D', '', fixed)
        if len(digits) >= 16:
            return digits[:16]
    
    return None


def extract_name_ktp(text: str) -> Optional[str]:
    """Extract name from KTP using multiple strategies"""
    lines = text.split('\n')
    
    # Strategy 1: Line after "Nama:" label
    for i, line in enumerate(lines):
        if re.match(r'^Nama\s*[:\.]?', line, re.IGNORECASE):
            # Attempt 1: Content on the same line
            raw = re.sub(r'^Nama\s*[:\.]?\s*', '', line, flags=re.IGNORECASE)
            valid = validate_and_clean_name(raw)
            if valid:
                return valid
            
            # Attempt 2: "Try Next Line" logic
            if i + 1 < len(lines):
                valid_next = validate_and_clean_name(lines[i+1])
                if valid_next:
                    return valid_next
    
    # Strategy 2: Longest uppercase sequence in top half
    top_half = lines[:len(lines)//2 + 5]
    best_name = None
    best_len = 0
    
    skip_words = ['PROVINSI', 'KABUPATEN', 'KOTA', 'NIK', 'LAKI', 'PEREMPUAN', 
                  'AGAMA', 'ALAMAT', 'TEMPAT', 'LAHIR', 'KELAMIN', 'KAWIN',
                  'PEKERJAAN', 'KEWARGANEGARAAN', 'BERLAKU']
    
    for line in top_half:
        line = line.strip()
        if any(w in line.upper() for w in skip_words):
            continue
            
        if len(line) < 4:
            continue
        
        matches = re.findall(r"[A-Z][A-Z\s\.']{3,}", line)
        for m in matches:
            valid = validate_and_clean_name(m)
            if valid:
                if len(valid) > best_len:
                    best_name = valid
                    best_len = len(valid)
    
    return best_name


def extract_place_of_birth(text: str) -> Optional[str]:
    """Extract place of birth from KTP"""
    lines = text.split('\n')
    
    for line in lines:
        lower = line.lower()
        # Match variations: "Tempat/Tgl Lahir", "Tempat Lahir", etc
        if 'lahir' in lower or 'late' in lower or 'lahr' in lower:
            # Pattern: "LABEL: PLACE, DATE" or "LABEL: PLACE DD-MM-YYYY"
            m = re.search(r'(?:Tempat|Place|Tempa)[/\s]*(?:Tgl|Tanggal|Tg)?[/\s]*(?:Lahir|Late|Lahr)[:\s]*([A-Za-z\s]+?)\s*[,\s]+\d',
                         line, re.IGNORECASE)
            if m:
                place = m.group(1).strip().upper()
                if len(place) >= 2:
                    return place
            
            # Simpler pattern: after colon, take alphabetic part before comma/number
            m = re.search(r'[:\s]+([A-Za-z\s]+?)\s*[,\s]+\d', line)
            if m:
                place = m.group(1).strip().upper()
                if len(place) >= 2:
                    return place
    
    return None


def extract_address(text: str) -> Optional[str]:
    """
    Extract address from KTP.
    Handles noisy OCR where 'Alamat' may be partially read.
    """
    lines = text.split('\n')
    
    for i, line in enumerate(lines):
        lower = line.lower()
        
        # Strategy 1: Exact "Alamat" label match
        m = re.match(r'^Alamat\s*[:\.]?\s*(.*)', line, re.IGNORECASE)
        if m and m.group(1).strip():
            return m.group(1).strip()
        
        # Strategy 2: Fuzzy match - "lamat", "lama", "Alam" at start of line (OCR noise)
        if re.match(r'^(?:a?lamat|alam|lama)', lower):
            # Try to extract value after the label
            value = re.sub(r'^(?:a?lamat|alam|lama)\w*\s*[:\.]?\s*', '', line, flags=re.IGNORECASE).strip()
            if value and len(value) >= 3:
                return value
        
        # Strategy 3: Look for "DUKUH", "DESA", "JL", "JALAN", "DSN" as address indicators
        if re.match(r'^(?:DUKUH|DESA|JL|JALAN|DSN|DUSUN)', line.strip(), re.IGNORECASE):
            return line.strip()
        
        # Strategy 4: Line contains address-like keywords anywhere
        if re.search(r'(?:DUKUH|KOPEK|JL\.|JALAN|DSN)', line, re.IGNORECASE):
            # Remove any label prefix
            cleaned = re.sub(r'^[A-Za-z]+\s+', '', line, count=1).strip()
            if cleaned:
                return cleaned
    
    # Strategy 5: Check for "Rama" or similar OCR misreading of "Alamat"
    for line in lines:
        m = re.match(r'^(?:Rama|Rame|Ramat|lama)\s+(.+)', line, re.IGNORECASE)
        if m:
            value = m.group(1).strip()
            # Filter out label-only artifacts
            if len(value) >= 3 and not re.match(r'^[:\.\s]+$', value):
                return value
    
    return None


# =============================================================================
# REGIONAL INFO EXTRACTORS
# =============================================================================

def extract_regional_info(text: str) -> Dict[str, Optional[str]]:
    """
    Extract provinsi, kabupaten, kecamatan, kelurahan from KTP.
    Handles both header format (PROVINSI JAWA TENGAH) and label format (Provinsi: JAWA TENGAH).
    """
    result = {
        'provinsi': None,
        'kabupaten': None,
        'kecamatan': None,
        'kelurahan': None,
    }
    
    lines = text.split('\n')
    
    for line in lines:
        stripped = line.strip()
        upper = stripped.upper()
        
        # Header format: "PROVINSI JAWA TENGAH" (the word PROVINSI followed by the name)
        m = re.match(r'PROVINSI\s+(.+)', upper)
        if m and not result['provinsi']:
            prov = re.sub(r'[^A-Z\s]', '', m.group(1)).strip()
            if len(prov) >= 3:
                result['provinsi'] = prov
                continue
        
        # Header format: "KABUPATEN PATI" or "KOTA SURABAYA"
        m = re.match(r'(?:KABUPATEN|KOTA)\s+(.+)', upper)
        if m and not result['kabupaten']:
            kab = re.sub(r'[^A-Z\s]', '', m.group(1)).strip()
            if len(kab) >= 2:
                result['kabupaten'] = kab
                continue
        
        # Label format: "Kecamatan: PUCAKWANGI" or "Kecamatan PUCAKWANGI"
        m = re.search(r'Kecamatan\w*\s*[:\s]+([A-Za-z\s]+)', stripped, re.IGNORECASE)
        if m and not result['kecamatan']:
            kec = m.group(1).strip().upper()
            kec = re.sub(r'[^A-Z\s]', '', kec).strip()
            if len(kec) >= 2:
                result['kecamatan'] = kec
                continue
        
        # Label format: "Kel/Desa: KARANGWOTAN" or "KelDess KAANGHOTAN" (noisy OCR)
        m = re.search(r'(?:Kel|Kal|Col)[/\s]*(?:Desa|Des|Dess|Dese|de)\w*\s*[:\s=]+([A-Za-z\s]+)', stripped, re.IGNORECASE)
        if m and not result['kelurahan']:
            kel = m.group(1).strip().upper()
            kel = re.sub(r'[^A-Z\s]', '', kel).strip()
            if len(kel) >= 2:
                result['kelurahan'] = kel
                continue
    
    return result


# =============================================================================
# MAIN KTP EXTRACTION
# =============================================================================

def extract_ktp_data(text: str) -> Dict[str, Optional[str]]:
    """
    Extract all fields from KTP document.
    Returns a dict with all standard fields.
    """
    result = empty_result()
    result['document_type'] = 'KTP'
    
    result['no_identitas'] = extract_nik(text)
    result['nama'] = extract_name_ktp(text)
    result['tempat_lahir'] = extract_place_of_birth(text)
    result['tanggal_lahir'] = extract_date(text, "Lahir")
    result['alamat'] = extract_address(text)
    
    # Regional info
    regional = extract_regional_info(text)
    result['provinsi'] = regional['provinsi']
    result['kabupaten'] = regional['kabupaten']
    result['kecamatan'] = regional['kecamatan']
    result['kelurahan'] = regional['kelurahan']
    
    return result
