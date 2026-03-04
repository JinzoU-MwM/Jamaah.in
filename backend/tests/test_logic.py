import sys
from pathlib import Path
import pytest

# Add backend directory to path so we can import app
sys.path.append(str(Path(__file__).parent.parent))

from app.services.cleaner import validate_and_clean_name, standardize_date, clean_entry, fuzzy_merge_data
from app.services.parser import extract_nik, fix_ocr_digits, clean_mrz_line
from app.schemas import ExtractedDataItem


def test_validate_and_clean_name():
    assert validate_and_clean_name("JOHN DOE") == "JOHN DOE"
    assert validate_and_clean_name("JOHN-DOE") == "JOHN-DOE"
    assert validate_and_clean_name("JOHN. DOE") == "JOHN DOE"
    assert validate_and_clean_name("PROVINSI JAWA") is None  # Blacklist
    assert validate_and_clean_name("AB") is None  # Too short
    assert validate_and_clean_name("12345") is None  # No letters


def test_standardize_date():
    # Indonesian Month
    assert standardize_date("16 MEI 1990") == "1990-05-16"
    assert standardize_date("17 AGU 1995") == "1995-08-17"
    
    # Numeric with separators
    assert standardize_date("16-05-1990") == "1990-05-16"
    assert standardize_date("1990-05-16") == "1990-05-16"
    
    # Typos
    assert standardize_date("16 MEI l990") == "1990-05-16"  # l -> 1
    assert standardize_date("I6 MEI 1990") == "1990-05-16"  # I -> 1
    
    # Day/Month Swap Logic
    assert standardize_date("1990-13-12") == "1990-12-13"  # 13 is month? No, swap to day


def test_extract_nik():
    # Clear NIK
    text = "NIK : 3515082506920002"
    assert extract_nik(text) == "3515082506920002"
    
    # OCR Noise
    text = "NIK : 35I5O8250692OOO2"  # I, O replaced
    assert extract_nik(text) == "3515082506920002"


def test_fix_ocr_digits():
    assert fix_ocr_digits("O123") == "0123"
    assert fix_ocr_digits("S678") == "5678"
    assert fix_ocr_digits("B000") == "8000"


def test_clean_mrz_line():
    # Should replace K,C,E within chevrons
    line = "P<IDN<K<C<E<<<"
    assert clean_mrz_line(line) == "P<IDN<<<<<<<<<"


def test_clean_entry_logic():
    item = ExtractedDataItem(
        nama="John. Doe!",
        tanggal_lahir="16 MEI 1990",
        tempat_lahir="jakarta",
        no_identitas="123"
    )
    cleaned = clean_entry(item)
    assert cleaned.nama == "JOHN DOE"
    assert cleaned.tanggal_lahir == "1990-05-16"
    assert cleaned.tempat_lahir == "JAKARTA"


def test_fuzzy_merge():
    item1 = ExtractedDataItem(nama="AHMAD DAHLAN", no_identitas="123")
    item2 = ExtractedDataItem(nama="AHMAD DAHLANN", alamat="Jl. Sudirman") # Typo but similar
    
    merged = fuzzy_merge_data([item1, item2])
    
    assert len(merged) == 1
    result = merged[0]
    # Should take longer name
    assert result.nama == "AHMAD DAHLANN"
    # Should merge fields
    assert result.no_identitas == "123"
    assert result.alamat == "Jl. Sudirman"


def test_passport_prioritized_for_identity_fields():
    item = ExtractedDataItem(
        nama="BUDI SANTOSO",
        jenis_identitas="KTP",
        no_identitas="3175090101010001",
        no_paspor="C1234567",
    )
    merged = fuzzy_merge_data([item])
    assert len(merged) == 1
    assert merged[0].jenis_identitas == "PASPOR"
    assert merged[0].no_identitas == "C1234567"


def test_kk_enrichment_fills_father_and_address():
    kk_item = ExtractedDataItem(
        nama="SUTRISNO",
        nama_ayah="SUTRISNO",
        alamat="JL. MELATI NO. 10",
        source_document_type="KK",
        kk_member_names="BUDI SANTOSO; SITI AMINAH",
    )
    passport_item = ExtractedDataItem(
        nama="BUDI SANTOSO",
        jenis_identitas="PASPOR",
        no_paspor="A1234567",
    )

    merged = fuzzy_merge_data([kk_item, passport_item])
    target = next(x for x in merged if x.nama == "BUDI SANTOSO")
    assert target.nama_ayah == "SUTRISNO"
    assert target.alamat == "JL. MELATI NO. 10"


def test_title_assignment_tuan_for_male():
    item = ExtractedDataItem(
        nama="AHMAD",
        tanggal_lahir="1990-01-01",
        jenis_kelamin="LAKI-LAKI",
        status_pernikahan="KAWIN",
    )
    merged = fuzzy_merge_data([item])
    assert merged[0].title == "TUAN"


def test_title_assignment_nona_for_underage_female():
    item = ExtractedDataItem(
        nama="SITI",
        tanggal_lahir="2012-01-01",
        jenis_kelamin="PEREMPUAN",
        status_pernikahan="BELUM KAWIN",
    )
    merged = fuzzy_merge_data([item])
    assert merged[0].title == "NONA"


def test_title_assignment_nyonya_for_married_adult_female():
    item = ExtractedDataItem(
        nama="RINA",
        tanggal_lahir="1992-05-10",
        jenis_kelamin="PEREMPUAN",
        status_pernikahan="KAWIN",
    )
    merged = fuzzy_merge_data([item])
    assert merged[0].title == "NYONYA"
