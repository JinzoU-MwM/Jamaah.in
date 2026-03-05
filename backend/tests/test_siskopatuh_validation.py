from app.schemas import ExtractedDataItem
from app.services.siskopatuh_validation import (
    SiskopatuhDropdownRules,
    normalize_items_to_siskopatuh_dropdowns,
    validate_items_against_siskopatuh_dropdowns,
)


def _mock_rules() -> SiskopatuhDropdownRules:
    return SiskopatuhDropdownRules(
        titles=frozenset({"TUAN", "NONA", "NYONYA"}),
        jenis_identitas=frozenset({"NIK", "KITAS", "KITAP", "PASPOR"}),
        kewarganegaraan=frozenset({"WNI", "WNA"}),
        status_pernikahan=frozenset({"BELUM MENIKAH", "MENIKAH", "JANDA / DUDA"}),
        pendidikan=frozenset({"SMA/MA", "D4/S1"}),
        pekerjaan=frozenset({"PEG. SWASTA", "WIRAUSAHA"}),
        provider_visa=frozenset({"PT. A", "PT. B"}),
        asuransi=frozenset({"ASURANSI A", "ASURANSI B"}),
        provinsi=frozenset({"JAWA TENGAH", "DKI JAKARTA"}),
        kabupaten_by_named_range={
            "JAWA_TENGAH": frozenset({"KAB. PATI", "KOTA SEMARANG"}),
            "DKI_JAKARTA": frozenset({"KOTA JAKARTA SELATAN"}),
        },
    )


def test_validate_items_against_siskopatuh_dropdowns_valid(monkeypatch):
    monkeypatch.setattr(
        "app.services.siskopatuh_validation.get_siskopatuh_dropdown_rules",
        _mock_rules,
    )
    item = ExtractedDataItem(
        title="NYONYA",
        jenis_identitas="PASPOR",
        kewarganegaraan="WNI",
        status_pernikahan="MENIKAH",
        pendidikan="SMA/MA",
        pekerjaan="PEG. SWASTA",
        provider_visa="PT. A",
        asuransi="ASURANSI A",
        provinsi="JAWA TENGAH",
        kabupaten="KAB. PATI",
    )

    errors = validate_items_against_siskopatuh_dropdowns([item])
    assert errors == []


def test_validate_items_against_siskopatuh_dropdowns_invalid(monkeypatch):
    monkeypatch.setattr(
        "app.services.siskopatuh_validation.get_siskopatuh_dropdown_rules",
        _mock_rules,
    )
    item = ExtractedDataItem(
        title="BAPAK",
        jenis_identitas="KTP",
        kewarganegaraan="INDONESIA",
        status_pernikahan="CERAI",
        pendidikan="S1",
        pekerjaan="KARYAWAN",
        provider_visa="PT. X",
        asuransi="ASURANSI X",
        provinsi="JAWA TENGAH",
        kabupaten="KOTA JAKARTA SELATAN",
    )

    errors = validate_items_against_siskopatuh_dropdowns([item])
    assert len(errors) >= 9
    assert any("Title" in err for err in errors)
    assert any("Jenis Identitas" in err for err in errors)
    assert any("Kabupaten" in err for err in errors)


def test_normalize_items_to_siskopatuh_dropdowns_maps_common_values(monkeypatch):
    monkeypatch.setattr(
        "app.services.siskopatuh_validation.get_siskopatuh_dropdown_rules",
        _mock_rules,
    )
    item = ExtractedDataItem(
        title="bapak",
        jenis_identitas="ktp",
        kewarganegaraan="indonesia",
        status_pernikahan="kawin",
        pendidikan="s1",
        pekerjaan="karyawan swasta",
        provider_visa="pt. a",
        asuransi="asuransi a",
        provinsi="jawa tengah",
        kabupaten="kab pati",
    )

    normalize_items_to_siskopatuh_dropdowns([item])

    assert item.title == "TUAN"
    assert item.jenis_identitas == "NIK"
    assert item.kewarganegaraan == "WNI"
    assert item.status_pernikahan == "MENIKAH"
    assert item.pendidikan == "D4/S1"
    assert item.pekerjaan == "PEG. SWASTA"
    assert item.provider_visa == "PT. A"
    assert item.asuransi == "ASURANSI A"
    assert item.provinsi == "JAWA TENGAH"
    assert item.kabupaten == "KAB. PATI"
