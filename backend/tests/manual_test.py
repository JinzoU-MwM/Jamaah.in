import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent))

from app.services.cleaner import validate_and_clean_name, standardize_date, clean_entry, fuzzy_merge_data
from app.services.parser import extract_nik, fix_ocr_digits, clean_mrz_line
from app.schemas import ExtractedDataItem

def run_tests():
    failures = []
    
    # test_validate_and_clean_name
    try:
        assert validate_and_clean_name("JOHN DOE") == "JOHN DOE"
        assert validate_and_clean_name("JOHN-DOE") == "JOHN-DOE"
        assert validate_and_clean_name("JOHN. DOE") == "JOHN DOE"
        assert validate_and_clean_name("PROVINSI JAWA") is None
        assert validate_and_clean_name("AB") is None
        assert validate_and_clean_name("12345") is None
        print("test_validate_and_clean_name: PASS")
    except AssertionError as e:
        failures.append("test_validate_and_clean_name failed")
        print("test_validate_and_clean_name: FAIL")

    # test_standardize_date
    try:
        assert standardize_date("16 MEI 1990") == "1990-05-16"
        assert standardize_date("17 AGU 1995") == "1995-08-17"
        assert standardize_date("16-05-1990") == "1990-05-16"
        assert standardize_date("1990-05-16") == "1990-05-16"
        assert standardize_date("16 MEI l990") == "1990-05-16"
        assert standardize_date("I6 MEI 1990") == "1990-05-16"
        assert standardize_date("1990-13-12") == "1990-12-13"
        print("test_standardize_date: PASS")
    except AssertionError:
        failures.append("test_standardize_date failed")
        print("test_standardize_date: FAIL")

    # test_extract_nik
    try:
        assert extract_nik("NIK : 3515082506920002") == "3515082506920002"
        assert extract_nik("NIK : 35I5O8250692OOO2") == "3515082506920002"
        print("test_extract_nik: PASS")
    except AssertionError:
        failures.append("test_extract_nik failed")
        print("test_extract_nik: FAIL")

    # test_fix_ocr_digits
    try:
        assert fix_ocr_digits("O123") == "0123"
        assert fix_ocr_digits("S678") == "5678"
        assert fix_ocr_digits("B000") == "8000"
        print("test_fix_ocr_digits: PASS")
    except AssertionError:
        failures.append("test_fix_ocr_digits failed")
        print("test_fix_ocr_digits: FAIL")

    # test_clean_mrz_line
    try:
        assert clean_mrz_line("P<IDN<K<C<E<<<") == "P<IDN<<<<<<<<<"
        print("test_clean_mrz_line: PASS")
    except AssertionError:
        failures.append("test_clean_mrz_line failed")
        print(f"test_clean_mrz_line: FAIL. Got {clean_mrz_line('P<IDN<K<C<E<<<')}")

    # test_clean_entry_logic
    try:
        item = ExtractedDataItem(
            nama="John. Doe!",
            tanggal_lahir="16 MEI 1990",
            tempat_lahir="jakarta",
            no_identitas="123"
        )
        cleaned = clean_entry(item)
        if cleaned.nama != "JOHN DOE": return print(f"clean_entry FAIL: nama is {cleaned.nama}")
        if cleaned.tanggal_lahir != "1990-05-16": return print(f"clean_entry FAIL: user date is {cleaned.tanggal_lahir}")
        if cleaned.tempat_lahir != "JAKARTA": return print(f"clean_entry FAIL: tempat_lahir is {cleaned.tempat_lahir}")
        print("test_clean_entry_logic: PASS")
    except Exception as e:
        failures.append(f"test_clean_entry_logic failed: {e}")
        print(f"test_clean_entry_logic: FAIL {e}")

    # test_fuzzy_merge
    try:
        item1 = ExtractedDataItem(nama="AHMAD DAHLAN", no_identitas="123")
        item2 = ExtractedDataItem(nama="AHMAD DAHLANN", alamat="Jl. Sudirman")
        merged = fuzzy_merge_data([item1, item2])
        assert len(merged) == 1
        assert merged[0].nama == "AHMAD DAHLANN"
        assert merged[0].no_identitas == "123"
        assert merged[0].alamat == "Jl. Sudirman"
        print("test_fuzzy_merge: PASS")
    except AssertionError:
        failures.append("test_fuzzy_merge failed")
        print("test_fuzzy_merge: FAIL")

    if failures:
        sys.exit(1)
    else:
        print("ALL TESTS PASSED")

if __name__ == "__main__":
    run_tests()
