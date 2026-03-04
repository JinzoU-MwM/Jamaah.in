from app.auth import create_access_token


def _auth_headers(user):
    token = create_access_token({"sub": str(user.id), "email": user.email})
    return {"Authorization": f"Bearer {token}"}


def test_audit_log_records_group_member_actions(client, test_user, test_group):
    headers = _auth_headers(test_user)

    add_resp = client.post(
        f"/groups/{test_group.id}/members",
        headers=headers,
        json={
            "members": [
                {
                    "nama": "AUDIT TEST",
                    "tanggal_lahir": "1992-10-10",
                    "no_paspor": "AUD12345",
                }
            ]
        },
    )
    assert add_resp.status_code == 200
    member_id = add_resp.json()["members"][0]["id"]

    upd_resp = client.put(
        f"/groups/{test_group.id}/members/{member_id}",
        headers=headers,
        json={"nama": "AUDIT TEST UPDATED"},
    )
    assert upd_resp.status_code == 200

    del_resp = client.delete(f"/groups/{test_group.id}/members/{member_id}", headers=headers)
    assert del_resp.status_code == 200

    logs_resp = client.get("/auth/audit?limit=20", headers=headers)
    assert logs_resp.status_code == 200
    logs = logs_resp.json()["logs"]
    actions = {row["action"] for row in logs}

    assert "group_members_upsert" in actions
    assert "group_member_update" in actions
    assert "group_member_delete" in actions
