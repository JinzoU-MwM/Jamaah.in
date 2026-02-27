"""
Data Mappers — Convert raw OCR output dicts to Pydantic models.
"""
from .schemas import ExtractedDataItem


def doc_data_to_item(doc_data: dict) -> ExtractedDataItem:
    """Convert a raw OCR dict (from Gemini) to an ExtractedDataItem (32 columns).
    
    Maps Gemini's JSON field names to the internal ExtractedDataItem fields
    that match the Siskopatuh Excel column structure.
    """
    nama = doc_data.get('nama') or ""
    return ExtractedDataItem(
        title=doc_data.get('title') or "",
        nama=nama,
        nama_ayah=doc_data.get('nama_ayah') or "",
        jenis_identitas=doc_data.get('document_type', 'UNKNOWN'),
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
    )
