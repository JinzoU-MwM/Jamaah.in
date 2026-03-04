from app.auth import create_access_token
from app.models.group import GroupMember


def _auth_headers(user):
    token = create_access_token({"sub": str(user.id), "email": user.email})
    return {"Authorization": f"Bearer {token}"}


def test_group_duplicate_detection_by_passport_and_name_birth(client, db_session, test_user, test_group):
    headers = _auth_headers(test_user)

    # Seed duplicates directly (bypass upsert merge behavior).
    db_session.add_all([
        GroupMember(
            group_id=test_group.id,
            nama="BUDI SANTOSO",
            tanggal_lahir="1990-01-01",
            no_paspor="A1234567",
            no_identitas="3276010101900001",
        ),
        GroupMember(
            group_id=test_group.id,
            nama="BUDI SANTOSO",
            tanggal_lahir="1990-01-01",
            no_paspor="A1234567",
            no_identitas="3276010101909999",
        ),
        GroupMember(
            group_id=test_group.id,
            nama="SITI AMINAH",
            tanggal_lahir="1991-02-02",
            no_paspor="X1112223",
        ),
    ])
    db_session.commit()

    dup_resp = client.get(f"/groups/{test_group.id}/duplicates", headers=headers)
    assert dup_resp.status_code == 200
    data = dup_resp.json()

    assert data["group_id"] == test_group.id
    assert data["total_duplicate_groups"] >= 1

    duplicate_types = {row["key_type"] for row in data["duplicate_groups"]}
    assert "passport" in duplicate_types or "name_birth" in duplicate_types


def test_group_duplicate_detection_empty(client, test_user, test_group):
    headers = _auth_headers(test_user)
    dup_resp = client.get(f"/groups/{test_group.id}/duplicates", headers=headers)
    assert dup_resp.status_code == 200
    data = dup_resp.json()
    assert data["total_duplicate_groups"] == 0
