"""
Pydantic models for request/response validation
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import date


class DocumentData(BaseModel):
    """Base model for extracted document data"""
    document_type: str  # "KTP", "PASSPORT", or "VISA"
    
    # Common fields
    name: Optional[str] = None
    
    # KTP specific fields
    nik: Optional[str] = None
    address: Optional[str] = None
    rt: Optional[str] = None
    rw: Optional[str] = None
    kelurahan: Optional[str] = None
    kecamatan: Optional[str] = None
    kabupaten: Optional[str] = None
    provinsi: Optional[str] = None
    
    # Passport specific fields
    passport_number: Optional[str] = None
    place_of_birth: Optional[str] = None
    date_of_birth: Optional[str] = None
    date_of_issue: Optional[str] = None
    city_of_issue: Optional[str] = None
    date_of_expiry: Optional[str] = None
    
    # Visa specific fields
    visa_number: Optional[str] = None


class ExcelRow(BaseModel):
    """Model representing a single row in the Excel output"""
    no_identitas: Optional[str] = Field(None, alias="No Identitas")
    nama: Optional[str] = Field(None, alias="Nama (Sesuai Dengan nama Pada Kartu Vaksin)")
    tempat_lahir: Optional[str] = Field(None, alias="Tempat Lahir")
    tanggal_lahir: Optional[str] = Field(None, alias="Tanggal Lahir(yyyy-mm-dd)")
    alamat: Optional[str] = Field(None, alias="Alamat")
    provinsi: Optional[str] = Field(None, alias="Provinsi")
    kabupaten: Optional[str] = Field(None, alias="Kabupaten")
    kecamatan: Optional[str] = Field(None, alias="Kecamatan")
    kelurahan: Optional[str] = Field(None, alias="Kelurahan")
    no_paspor: Optional[str] = Field(None, alias="No Paspor")
    tanggal_dikeluarkan_paspor: Optional[str] = Field(None, alias="Tanggal Dikeluarkan Paspor(yyyy-mm-dd)")
    kota_paspor: Optional[str] = Field(None, alias="Kota Paspor")
    no_visa: Optional[str] = Field(None, alias="No Visa")
    jenis_identitas: Optional[str] = Field(None, alias="Jenis Identitas")
    kewarganegaraan: Optional[str] = Field(None, alias="KewargaNegaraan")

    class Config:
        populate_by_name = True


class ProcessingResult(BaseModel):
    """Result of processing a single document"""
    filename: str
    success: bool
    document_type: Optional[str] = None
    data: Optional[DocumentData] = None
    error: Optional[str] = None


class ExtractedDataItem(BaseModel):
    """Single row of extracted data for preview - matches 32 Excel columns"""
    title: str = ""                    # Col 1: Title (Mr/Mrs/Ms)
    nama: str = ""                     # Col 2: Nama (Sesuai Dengan nama Pada Kartu Vaksin)
    nama_ayah: str = ""                # Col 3: Nama Ayah
    jenis_identitas: str = ""          # Col 4: Jenis Identitas (KTP/PASPOR)
    no_identitas: str = ""             # Col 5: No Identitas
    nama_paspor: str = ""              # Col 6: Nama Paspor
    no_paspor: str = ""                # Col 7: No Paspor
    tanggal_paspor: str = ""           # Col 8: Tanggal Dikeluarkan Paspor (yyyy-mm-dd)
    kota_paspor: str = ""              # Col 9: Kota Paspor
    tempat_lahir: str = ""             # Col 10: Tempat Lahir
    tanggal_lahir: str = ""            # Col 11: Tanggal Lahir (yyyy-mm-dd)
    alamat: str = ""                   # Col 12: Alamat
    provinsi: str = ""                 # Col 13: Provinsi
    kabupaten: str = ""                # Col 14: Kabupaten
    kecamatan: str = ""                # Col 15: Kecamatan
    kelurahan: str = ""                # Col 16: Kelurahan
    no_telepon: str = ""               # Col 17: No. Telepon
    no_hp: str = ""                    # Col 18: No Hp
    kewarganegaraan: str = "WNI"       # Col 19: KewargaNegaraan
    status_pernikahan: str = ""        # Col 20: Status Pernikahan
    pendidikan: str = ""               # Col 21: Pendidikan
    pekerjaan: str = ""                # Col 22: Pekerjaan
    provider_visa: str = ""            # Col 23: Provider Visa
    no_visa: str = ""                  # Col 24: No Visa
    tanggal_visa: str = ""             # Col 25: Tanggal Berlaku Visa (yyyy-mm-dd)
    tanggal_visa_akhir: str = ""       # Col 26: Tanggal Akhir Visa (yyyy-mm-dd)
    asuransi: str = ""                 # Col 27: Asuransi
    no_polis: str = ""                 # Col 28: No Polis
    tanggal_input_polis: str = ""      # Col 29: Tanggal Input Polis (yyyy-mm-dd)
    tanggal_awal_polis: str = ""       # Col 30: Tanggal Awal Polis (yyyy-mm-dd)
    tanggal_akhir_polis: str = ""      # Col 31: Tanggal Akhir Polis (yyyy-mm-dd)
    no_bpjs: str = ""                  # Col 32: No BPJS


class ValidationWarning(BaseModel):
    """A single validation warning for a field"""
    field: str
    message: str


class FileResult(BaseModel):
    """Per-file processing status"""
    filename: str
    status: str  # "success", "partial", "failed"
    document_type: str = ""
    error: str = ""
    cached: bool = False


class ProcessingPreviewResponse(BaseModel):
    """Response for /process-documents/ endpoint"""
    status: str
    message: str
    total_files: int
    successful: int
    failed: int
    data: List[ExtractedDataItem]
    validation_warnings: List[List[ValidationWarning]] = []  # warnings per row
    file_results: List[FileResult] = []  # per-file status
    cache_stats: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None  # for SSE progress connection


class GenerateExcelRequest(BaseModel):
    """Request body for /generate-excel/ endpoint"""
    data: List[ExtractedDataItem]
