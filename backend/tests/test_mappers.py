from app.mappers import doc_data_to_item
from app.services.parser import detect_document_type


def test_doc_data_to_item_normalizes_kk_to_ktp():
    item = doc_data_to_item(
        {
            "document_type": "KK",
            "nama": "BUDI",
            "no_identitas": "1234567890123456",
            "alamat": "JL. MELATI 1",
        }
    )
    assert item.jenis_identitas == "KTP"
    assert item.no_identitas == "1234567890123456"
    assert item.alamat == "JL. MELATI 1"


def test_detect_document_type_for_kk_text():
    text = "KARTU KELUARGA\nNO. KK 3175091200000001\nKEPALA KELUARGA"
    assert detect_document_type(text) == "KTP"
