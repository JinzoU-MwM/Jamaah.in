from app.mappers import doc_data_to_item
from app.services.parser import detect_document_type


def test_doc_data_to_item_normalizes_kk_to_ktp():
    item = doc_data_to_item(
        {
            "document_type": "KK",
            "nama": "BUDI",
            "no_identitas": "1234567890123456",
            "alamat": "JL. MELATI 1",
            "kk_member_names": "BUDI; SITI",
            "kk_member_fathers": "BUDI:SUPARMAN;SITI:DARWIS",
            "jenis_kelamin": "LAKI-LAKI",
        }
    )
    assert item.jenis_identitas == "KTP"
    assert item.source_document_type == "KK"
    assert item.kk_member_names == "BUDI; SITI"
    assert item.kk_member_fathers == "BUDI:SUPARMAN;SITI:DARWIS"
    assert item.jenis_kelamin == "LAKI-LAKI"
    assert item.field_source_json == ""
    assert item.field_confidence_json == ""
    assert item.no_identitas == "1234567890123456"
    assert item.alamat == "JL. MELATI 1"


def test_detect_document_type_for_kk_text():
    text = "KARTU KELUARGA\nNO. KK 3175091200000001\nKEPALA KELUARGA"
    assert detect_document_type(text) == "KTP"
