"""
Field-level validation rules for extracted document data.
Returns warnings (non-blocking) so users can fix in preview.
"""
import re
from typing import List, Dict, Optional
from datetime import datetime


def validate_nik(nik: str) -> Optional[str]:
    """Validate Indonesian NIK (16 digits)"""
    if not nik:
        return None
    cleaned = re.sub(r'\D', '', nik)
    if len(cleaned) != 16:
        return f"NIK harus 16 digit (ditemukan {len(cleaned)} digit)"
    return None


def validate_date(value: str, field_label: str) -> Optional[str]:
    """Validate date format (YYYY-MM-DD or DD-MM-YYYY)"""
    if not value:
        return None
    # Try multiple formats
    for fmt in ('%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%Y/%m/%d'):
        try:
            datetime.strptime(value.strip(), fmt)
            return None
        except ValueError:
            continue
    return f"{field_label}: format tanggal tidak valid (gunakan YYYY-MM-DD)"


def validate_passport_number(passport: str) -> Optional[str]:
    """Validate Indonesian passport number (1 letter + 6-7 digits)"""
    if not passport:
        return None
    cleaned = passport.strip().upper()
    if not re.match(r'^[A-Z]\d{6,7}$', cleaned):
        return f"No Paspor format tidak valid: '{passport}'"
    return None


def validate_visa_number(visa: str) -> Optional[str]:
    """Validate visa number (alphanumeric, 8+ chars)"""
    if not visa:
        return None
    cleaned = visa.strip()
    if len(cleaned) < 8:
        return f"No Visa terlalu pendek: '{visa}'"
    return None


def validate_kewarganegaraan(value: str) -> Optional[str]:
    """Validate citizenship"""
    if not value:
        return None
    if value.upper() not in ('WNI', 'WNA'):
        return f"Kewarganegaraan harus WNI atau WNA"
    return None


def validate_row(row_data: dict) -> List[Dict[str, str]]:
    """
    Validate a single row of extracted data.
    Returns list of warnings: [{"field": "no_identitas", "message": "..."}]
    """
    warnings = []

    # NIK validation (only if jenis_identitas is KTP)
    if row_data.get('jenis_identitas', '').upper() in ('KTP', 'MERGED'):
        w = validate_nik(row_data.get('no_identitas', ''))
        if w:
            warnings.append({"field": "no_identitas", "message": w})

    # Passport number
    w = validate_passport_number(row_data.get('no_paspor', ''))
    if w:
        warnings.append({"field": "no_paspor", "message": w})

    # Visa number
    w = validate_visa_number(row_data.get('no_visa', ''))
    if w:
        warnings.append({"field": "no_visa", "message": w})

    # Date fields
    date_fields = [
        ('tanggal_lahir', 'Tanggal Lahir'),
        ('tanggal_paspor', 'Tanggal Paspor'),
        ('tanggal_visa', 'Tanggal Visa'),
        ('tanggal_visa_akhir', 'Tanggal Visa Akhir'),
        ('tanggal_input_polis', 'Tanggal Input Polis'),
        ('tanggal_awal_polis', 'Tanggal Awal Polis'),
        ('tanggal_akhir_polis', 'Tanggal Akhir Polis'),
    ]
    for field_key, field_label in date_fields:
        w = validate_date(row_data.get(field_key, ''), field_label)
        if w:
            warnings.append({"field": field_key, "message": w})

    # Kewarganegaraan
    w = validate_kewarganegaraan(row_data.get('kewarganegaraan', ''))
    if w:
        warnings.append({"field": "kewarganegaraan", "message": w})

    # Required field: nama
    if not row_data.get('nama', '').strip():
        warnings.append({"field": "nama", "message": "Nama tidak boleh kosong"})

    return warnings
