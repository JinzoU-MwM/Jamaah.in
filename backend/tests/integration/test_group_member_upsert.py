from app.auth import create_access_token
from app.models.group import GroupMember


def _auth_headers(user):
    token = create_access_token({"sub": str(user.id), "email": user.email})
    return {"Authorization": f"Bearer {token}"}


def test_add_members_merges_existing_member_by_passport(client, db_session, test_user, test_group):
    headers = _auth_headers(test_user)

    passport_payload = {
        "members": [
            {
                "nama": "BUDI SANTOSO",
                "tanggal_lahir": "1990-01-01",
                "no_paspor": "A1234567",
                "jenis_identitas": "",
                "no_identitas": "",
            }
        ]
    }
    resp_1 = client.post(f"/groups/{test_group.id}/members", headers=headers, json=passport_payload)
    assert resp_1.status_code == 200
    assert resp_1.json()["added_count"] == 1
    assert resp_1.json()["updated_count"] == 0

    ktp_visa_payload = {
        "members": [
            {
                "nama": "BUDI SANTOSO",
                "tanggal_lahir": "1990-01-01",
                "nama_ayah": "SUTRISNO",
                "alamat": "JL MAWAR NO 10",
                "no_identitas": "3276010101900001",
                "no_visa": "V-998877",
            }
        ]
    }
    resp_2 = client.post(f"/groups/{test_group.id}/members", headers=headers, json=ktp_visa_payload)
    assert resp_2.status_code == 200
    assert resp_2.json()["added_count"] == 0
    assert resp_2.json()["updated_count"] == 1

    members = db_session.query(GroupMember).filter(GroupMember.group_id == test_group.id).all()
    assert len(members) == 1
    row = members[0]
    assert row.nama == "BUDI SANTOSO"
    assert row.nama_ayah == "SUTRISNO"
    assert row.alamat == "JL MAWAR NO 10"
    assert row.no_visa == "V-998877"
    assert row.no_paspor == "A1234567"
    assert row.jenis_identitas == "PASPOR"
    assert row.no_identitas == "A1234567"


def test_add_members_keeps_new_row_when_identity_does_not_match(client, db_session, test_user, test_group):
    headers = _auth_headers(test_user)

    first = {
        "members": [
            {
                "nama": "ALI AKBAR",
                "tanggal_lahir": "1988-03-10",
                "no_paspor": "C1234567",
            }
        ]
    }
    second = {
        "members": [
            {
                "nama": "ALI AKBAR",
                "tanggal_lahir": "1999-04-11",
                "no_paspor": "D7654321",
            }
        ]
    }
    client.post(f"/groups/{test_group.id}/members", headers=headers, json=first)
    resp = client.post(f"/groups/{test_group.id}/members", headers=headers, json=second)

    assert resp.status_code == 200
    assert resp.json()["added_count"] == 1
    assert resp.json()["updated_count"] == 0

    total = db_session.query(GroupMember).filter(GroupMember.group_id == test_group.id).count()
    assert total == 2


def test_add_members_passport_priority_over_identity_fields(client, db_session, test_user, test_group):
    headers = _auth_headers(test_user)
    payload = {
        "members": [
            {
                "nama": "SITI AMINAH",
                "no_paspor": "X9988776",
                "jenis_identitas": "KTP",
                "no_identitas": "3276123412341234",
            }
        ]
    }

    resp = client.post(f"/groups/{test_group.id}/members", headers=headers, json=payload)
    assert resp.status_code == 200
    assert resp.json()["added_count"] == 1

    row = db_session.query(GroupMember).filter(GroupMember.group_id == test_group.id).first()
    assert row is not None
    assert row.no_paspor == "X9988776"
    assert row.jenis_identitas == "PASPOR"
    assert row.no_identitas == "X9988776"
