"""Functional checks. These must keep passing after your security fixes."""

import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from conftest import login, post  # noqa: E402


def test_login_and_browse(client):
    response = login(client)
    assert b"Campus clubs" in response.data
    assert client.get("/clubs/1").status_code == 200


def test_wrong_password_rejected(client):
    response = post(client, "/login", "/login", {"username": "student1", "password": "wrong"})
    assert b"Invalid username or password" in response.data


def test_search_finds_club(client):
    response = client.get("/clubs/search", query_string={"q": "Robot"})
    assert b"Robotics Club" in response.data
    assert b"Cybersecurity Club" not in response.data


def test_join_club(client, db):
    login(client, "student2")
    post(client, "/clubs/1", "/clubs/1/join")
    row = db.execute(
        """SELECT 1 FROM memberships m JOIN users u ON u.id = m.user_id
           WHERE u.username = 'student2' AND m.club_id = 1"""
    ).fetchone()
    assert row is not None


def test_officer_edits_description(client, db):
    login(client, "officer1")
    post(client, "/clubs/1", "/clubs/1/description", {"description": "Meetings on Thursdays."})
    row = db.execute("SELECT description FROM clubs WHERE id = 1").fetchone()
    assert row["description"] == "Meetings on Thursdays."
    assert b"Meetings on Thursdays." in client.get("/clubs/1").data


def test_officer_upload_and_download(client):
    login(client, "officer1")
    post(
        client,
        "/clubs/1",
        "/clubs/1/upload",
        {"document": (io.BytesIO(b"synthetic agenda"), "agenda.txt")},
        content_type="multipart/form-data",
    )
    page = client.get("/clubs/1").data.decode()
    link = page.split('href="/documents')[1].split('"')[0]
    assert client.get("/documents" + link.replace("&amp;", "&")).data == b"synthetic agenda"


def test_student_cannot_upload(client):
    login(client)
    response = post(
        client,
        "/clubs/1",
        "/clubs/1/upload",
        {"document": (io.BytesIO(b"no"), "no.txt")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 403


def test_member_sees_roster(client):
    login(client)
    names = [row["display_name"] for row in client.get("/api/members/1").get_json()]
    assert "Avery Nguyen" in names


def test_profile_edit(client, db):
    login(client)
    post(client, "/profile", "/profile", {"display_name": "Updated Student", "email": "updated@example.test"})
    row = db.execute("SELECT display_name FROM users WHERE username = 'student1'").fetchone()
    assert row["display_name"] == "Updated Student"


def test_admin_pages(client):
    login(client, "admin1")
    assert client.get("/admin/users").status_code == 200
    assert client.get("/admin/audit").status_code == 200
    assert client.get("/admin/export").status_code == 200


def test_student_blocked_from_admin(client):
    login(client)
    assert client.get("/admin/users").status_code == 403
