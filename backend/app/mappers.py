"""
Data Mappers — Convert raw OCR output dicts to Pydantic models.
"""
from .schemas import ExtractedDataItem


def _normalize_identity_type(doc_type: str) -> str:
    """Normalize OCR document type for downstream compatibility."""
    normalized = (doc_type or "UNKNOWN").strip().upper()
    if normalized in {"KK", "KARTU KELUARGA", "FAMILY_CARD"}:
        return "KTP"
    return normalized


def _normalize_source_document_type(doc_type: str, kk_member_names: str = "") -> str:
    """Track original source type for special enrichment logic."""
    normalized = (doc_type or "").strip().upper()
    if normalized:
        return normalized
    if kk_member_names:
        return "KK"
    return "UNKNOWN"


def doc_data_to_item(doc_data: dict) -> ExtractedDataItem:
    """Convert a raw OCR dict (from Gemini) to an ExtractedDataItem (32 columns).
    
    Maps Gemini's JSON field names to the internal ExtractedDataItem fields
    that match the Siskopatuh Excel column structure.
    """
    nama = doc_data.get('nama') or ""
    kk_member_names = (doc_data.get('kk_member_names') or "").strip()
    kk_member_fathers = (doc_data.get('kk_member_fathers') or "").strip()
    raw_doc_type = doc_data.get('document_type', 'UNKNOWN')
    identity_type = _normalize_identity_type(raw_doc_type)
    source_document_type = _normalize_source_document_type(raw_doc_type, kk_member_names)
    return ExtractedDataItem(
        title=doc_data.get('title') or "",
        nama=nama,
        nama_ayah=doc_data.get('nama_ayah') or "",
        jenis_identitas=identity_type,
        no_identitas=doc_data.get('no_identitas') or "",
        nama_paspor=nama,  # Same as nama by default
        no_paspor=doc_data.get('no_paspor') or "",
        tanggal_paspor=doc_data.get('tanggal_paspor') or "",
        kota_paspor=doc_data.get('kota_paspor') or "",
        tempat_lahir=doc_data.get('tempat_lahir') or "",
        tanggal_lahir=doc_data.get('tanggal_lahir') or "",
        alamat=doc_data.get('alamat') or "",
        provinsi=doc_data.get('provinsi') or "",
        kabupaten=doc_data.get('kabupaten') or "",
        kecamatan=doc_data.get('kecamatan') or "",
        kelurahan=doc_data.get('kelurahan') or "",
        no_telepon=doc_data.get('no_telepon') or "",
        no_hp=doc_data.get('no_hp') or "",
        kewarganegaraan="WNI",
        status_pernikahan=doc_data.get('status_pernikahan') or "",
        pendidikan=doc_data.get('pendidikan') or "",
        pekerjaan=doc_data.get('pekerjaan') or "",
        provider_visa=doc_data.get('provider_visa') or "",
        no_visa=doc_data.get('no_visa') or "",
        tanggal_visa=doc_data.get('tanggal_visa') or "",
        tanggal_visa_akhir=doc_data.get('tanggal_visa_akhir') or "",
        asuransi=doc_data.get('asuransi') or "",
        no_polis=doc_data.get('no_polis') or "",
        tanggal_input_polis=doc_data.get('tanggal_input_polis') or "",
        tanggal_awal_polis=doc_data.get('tanggal_awal_polis') or "",
        tanggal_akhir_polis=doc_data.get('tanggal_akhir_polis') or "",
        no_bpjs=doc_data.get('no_bpjs') or "",
        source_document_type=source_document_type,
        kk_member_names=kk_member_names,
        kk_member_fathers=kk_member_fathers,
        jenis_kelamin=doc_data.get('jenis_kelamin') or "",
    )
