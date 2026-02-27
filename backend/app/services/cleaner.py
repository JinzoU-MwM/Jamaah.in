"""
Data Cleaning and Validation Services
"""
import re
from typing import Optional, List
from difflib import SequenceMatcher
from ..schemas import ExtractedDataItem
# Actually parser uses validate_and_clean_name.
# cleaner uses standardize_date on ExtractedDataItem.

# Let's put validate_and_clean_name here.
# parser will import it.

def validate_and_clean_name(raw_name: Optional[str]) -> Optional[str]:
    """
    Validates and cleans extracted name.
    1. Blacklist check (PROVINSI, KABUPATEN, etc.)
    2. Sanitize (remove non-letters)
    3. Minimum length check
    """
    if not raw_name:
        return None
        
    # 1. Sanitize: Keep only A-Z and space
    # Remove dots, commas, digits, symbols
    # We allow - and ' for names like 'D'ARCY' or 'ANNA-MARIE'
    cleaned = re.sub(r'[^A-Z\s\-\']', '', raw_name.upper())
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    # 2. Minimum Length
    if len(cleaned) < 3:
        return None
        
    # 3. Blacklist Strategy
    # Discard if it contains technical keywords
    blacklist = ["PROVINSI", "KABUPATEN", "KOTA", "NIK", "LAKI-LAKI", "PEREMPUAN", 
                 "AGAMA", "KAWIN", "GOL. DARAH", "GOL DARAH", "PARTAI", 
                 "PEMILIHAN", "UMUM", "KARTU", "PENDUDUK", "NEGARA"]
    
    for word in blacklist:
        if word in cleaned:
            return None
            
    return cleaned


def standardize_date(raw_text: str | None) -> str | None:
    """
    Robust date parser for OCR output.
    Handles:
    - Indonesian textual months (16 MEI 1990)
    - Numeric formats (DD-MM-YYYY, YYYY-MM-DD)
    - Common OCR typos (l->1, O->0, etc.)
    - Logical validation (1900-2030)
    - Day/Month swaps
    """
    if not raw_text:
        return None
        
    # 1. CLEAN UP TYPOS
    text = raw_text.upper().strip()
    replacements = {
        'l': '1', 'I': '1', 'O': '0', 'o': '0', 
        '?': '7', ':': '-', '.': '-', ',': '-',
        '|': '1', '_': '-'
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
        
    # 2. INDONESIAN MONTH MAPPING
    month_map = {
        'JAN': '01', 'FEB': '02', 'PEB': '02', 'MAR': '03', 
        'APR': '04', 'MEI': '05', 'MAY': '05', 'JUN': '06', 
        'JUL': '07', 'AGU': '08', 'AUG': '08', 'SEP': '09', 
        'OKT': '10', 'OCT': '10', 'NOV': '11', 'DES': '12', 'DEC': '12'
    }
    
    # 3. REGEX STRATEGIES (Priority Order)
    
    # Strategy A: Text Month (16 MEI 1977 or 16-MEI-1977)
    # Pattern: Digit(1-2) + Separator + Alpha(3+) + Separator + Digit(4)
    match_text = re.search(r'(\d{1,2})[\s\-]+([A-Z]{3,})[\s\-]+(\d{4})', text)
    if match_text:
        d, m_str, y = match_text.groups()
        # Find month number
        for k, v in month_map.items():
            if k in m_str:
                return f"{y}-{v}-{d.zfill(2)}"
    
    # Strategy B: Numeric (DD-MM-YYYY or YYYY-MM-DD or MM-DD-YYYY)
    # Extract all numbers from string
    nums = re.findall(r'\d+', text)
    
    if len(nums) >= 3:
        # We need at least 3 numbers for date
        # Sort them by length to guess Year (4 digits)
        year = next((n for n in nums if len(n) == 4), None)
        
        if year:
            # Remove year from list to process day/month
            others = [n for n in nums if n != year]
            if len(others) >= 2:
                n1, n2 = int(others[0]), int(others[1])
                y_val = int(year)
                
                # VALIDATION: Year Range
                if not (1900 <= y_val <= 2040):
                    return None
                    
                # DETERMINE DAY & MONTH
                # Assumption: If one > 12, it must be Day. If both <= 12, assume DD-MM (standard for ID)
                month, day = 0, 0
                
                if n2 > 12 >= n1:
                     # MM-DD format (rare in ID but possible typo)
                    month, day = n1, n2
                elif n1 > 12 >= n2:
                    # DD-MM format (standard)
                    day, month = n1, n2
                else:
                     # Both <= 12. Assume DD-MM-YYYY preferred
                    day, month = n1, n2
                    
                # Final Sanity Check
                if 1 <= month <= 12 and 1 <= day <= 31:
                     return f"{year}-{str(month).zfill(2)}-{str(day).zfill(2)}"

    return None


def clean_entry(entry: ExtractedDataItem) -> Optional[ExtractedDataItem]:
    """
    Sanitizes extraction data before merging.
    1. Clean Name (remove punctuation, blacklist check)
    2. Standardize Dates (YYYY-MM-DD)
    3. Uppercase Name/Place
    
    IMPORTANT: Visa documents may not have a 'nama' field but still contain
    valuable data (no_visa, tanggal_visa, etc.). We must NOT discard them.
    """
    # Check if this entry has ANY useful data (not just nama)
    has_visa_data = bool(entry.no_visa or entry.tanggal_visa or entry.provider_visa)
    has_passport_data = bool(entry.no_paspor or entry.tanggal_paspor)
    has_id_data = bool(entry.no_identitas)
    has_name = bool(entry.nama and entry.nama.strip())
    
    # Drop only if there's no useful data at all
    if not has_name and not has_visa_data and not has_passport_data and not has_id_data:
        return None
        
    # --- NAME CLEANING ---
    if has_name:
        # Uppercase and remove basic punctuation
        name = entry.nama.upper()
        name = re.sub(r'[.,\-!@#$%\^&*()_+=|<>?{}[\]~`]', ' ', name)
        name = re.sub(r'\s+', ' ', name).strip()
        
        # Remove common OCR artifacts
        name = re.sub(r'^DN\s+', '', name)
        name = re.sub(r'^IDN\s+', '', name)
        name = re.sub(r'\s+SE$', '', name)
        
        # Minimum Length — only reject if name is too short AND no other data
        if len(name) < 3:
            if not has_visa_data and not has_passport_data and not has_id_data:
                return None
            name = ""  # Clear garbage name but keep the entry
            
        # Blacklist Check (Header garbage)
        blacklist = ["PROVINSI", "KABUPATEN", "JAWA", "NIK", "LAKI-LAKI", "PEREMPUAN", 
                     "AGAMA", "KAWIN", "GOL. DARAH", "GOL DARAH", "PARTAI"]
        is_blacklisted = False
        for word in blacklist:
            if word in name:
                is_blacklisted = True
                break
        
        if is_blacklisted:
            if not has_visa_data and not has_passport_data and not has_id_data:
                return None
            name = ""  # Clear garbage name but keep the entry
        
        entry.nama = name
    
    # --- DATE STANDARDIZATION ---
    if entry.tanggal_lahir:
        entry.tanggal_lahir = standardize_date(entry.tanggal_lahir) or entry.tanggal_lahir
    
    if entry.tanggal_paspor:
        entry.tanggal_paspor = standardize_date(entry.tanggal_paspor) or entry.tanggal_paspor
    
    if entry.tanggal_visa:
        entry.tanggal_visa = standardize_date(entry.tanggal_visa) or entry.tanggal_visa
    
    if entry.tanggal_visa_akhir:
        entry.tanggal_visa_akhir = standardize_date(entry.tanggal_visa_akhir) or entry.tanggal_visa_akhir
        
    # --- PLACE STANDARDIZATION ---
    if entry.tempat_lahir:
        entry.tempat_lahir = entry.tempat_lahir.upper().strip()
        
    return entry


def fuzzy_merge_data(data_list: List[ExtractedDataItem]) -> List[ExtractedDataItem]:
    """Merge similar records using fuzzy logic"""
    consolidated = []

    def is_similar(n1: str, n2: str, threshold: float = 0.80) -> bool:
        if not n1 or not n2: return False
        # Direct match
        if n1 == n2: return True
        # Prefix match (e.g. "REBI" inside "REBI SARIP")
        # Ensure length is sufficient to avoid "ALI" matching "ALICE" falsely (require 4+ chars)
        if len(n1) > 3 and len(n2) > 3:
            if n1.startswith(n2) or n2.startswith(n1):
                return True
        # Sequence Matcher
        return SequenceMatcher(None, n1, n2).ratio() > threshold

    for new_item in data_list:
        matched = False
        for existing in consolidated:
            if is_similar(new_item.nama, existing.nama):
                matched = True
                # MERGE STRATEGY

                # 1. Name Priority: Prefer names with spaces (Full Name) over single strings (likely garbage/incomplete)
                curr_space = ' ' in existing.nama
                new_space = ' ' in new_item.nama

                if new_space and not curr_space:
                     existing.nama = new_item.nama
                elif new_space == curr_space:
                     # If both have spaces or neither, take the longer one
                     # But check for garbage repetition (e.g. KKK)
                     if len(new_item.nama) > len(existing.nama) and "KKK" not in new_item.nama:
                         existing.nama = new_item.nama

                # 2. Fill missing fields
                # Use dict() for Pydantic v1 compatibility (v2 uses model_dump)
                new_dict = new_item.dict() if hasattr(new_item, 'dict') else new_item.model_dump()
                for field, value in new_dict.items():
                    current_val = getattr(existing, field)
                    if not current_val and value:
                        setattr(existing, field, value)
                break

        if not matched:
            consolidated.append(new_item)

    # 3. Post-merge: Ensure consistency between jenis_identitas, no_identitas, and no_paspor
    for item in consolidated:
        # If jenis_identitas is Paspor, no_identitas should equal no_paspor
        if item.jenis_identitas and item.jenis_identitas.upper() in ('PASPOR', 'PASSPORT', 'VISA'):
            if item.no_paspor:
                item.no_identitas = item.no_paspor
        # If we have passport number but no_identitas is empty, use passport number
        elif item.no_paspor and not item.no_identitas:
            item.no_identitas = item.no_paspor
            item.jenis_identitas = "Paspor"

    return consolidated
