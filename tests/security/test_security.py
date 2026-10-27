"""Security checks for the announced BeachBoard Lite flaws.

These ship with the project. Each check fails on the original code and passes once the
matching flaw is fixed. Run them with: python -m pytest tests/security -v
Do not edit these files. Add your own checks in new files in this folder.
"""

import io
import re
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from conftest import login, post  # noqa: E402

APP_DIR = Path(__file__).resolve().parents[2] / "beachboard"


def read_users(app, columns):
    with sqlite3.connect(app.config["DATABASE"]) as con:
        con.row_factory = sqlite3.Row
        return con.execute(f"SELECT {columns} FROM users").fetchall()


def table_columns(app, table):
    with sqlite3.connect(app.config["DATABASE"]) as con:
        return {row[1] for row in con.execute(f"PRAGMA table_info({table})")}


def document_links(client, club_id=1):
    page = client.get(f"/clubs/{club_id}").data.decode()
    return [href.replace("&amp;", "&") for href in re.findall(r'href="(/documents[^"]*)"', page)]


# G1: club search must not let input change the query (Lecture 09)
def test_g01_search_injection(client):
    baseline = client.get("/clubs/search", query_string={"q": "zzznotaclub"}).data
    assert b"Robotics Club" not in baseline
    # A name that does not match any club must not return every club.
    tampered = client.get("/clubs/search", query_string={"q": "zzznotaclub%' OR '1'='1' -- "}).data
    assert b"Robotics Club" not in tampered
    assert b"Cybersecurity Club" not in tampered


# G2: passwords must be stored with a salted key-derivation function (Lecture 06)
def test_g02_password_hash_strength(client):
    rows = {r["username"]: r["password_hash"] for r in read_users(client.application, "username, password_hash")}
    stored = rows["student1"]
    assert not re.fullmatch(r"[0-9a-f]{32}", stored), "hash looks like unsalted MD5"
    # student1 and student2 share a password; a salted KDF makes their hashes differ.
    assert rows["student1"] != rows["student2"], "equal passwords produced equal hashes"


# G3: the roster endpoint must check club membership (Lecture 12)
def test_g03_roster_requires_membership(client):
    login(client, "student2")  # student2 is not a member of club 1
    assert client.get("/api/members/1").status_code == 403


# G4: application keys must come from the environment, not the source (Lecture 14)
def test_g04_secrets_from_environment():
    source = (APP_DIR / "config.py").read_text()
    assert "beachboard-dev-2026" not in source
    assert "getenv" in source or "environ" in source
    assert not re.search(r"EXPORT_KEY\s*=\s*b?['\"]", source), "export key is hard-coded"


# G5: uploads and downloads must be safe (Lectures 11 and 13)
def test_g05_upload_stays_in_folder(client):
    login(client, "officer1")
    upload_dir = Path(client.application.config["UPLOAD_FOLDER"])
    escaped = upload_dir.parent / "beachboard_escape.txt"
    if escaped.exists():
        escaped.unlink()
    post(client, "/clubs/1", "/clubs/1/upload",
         {"document": (io.BytesIO(b"synthetic"), "../beachboard_escape.txt")},
         content_type="multipart/form-data")
    assert not escaped.exists(), "upload escaped the storage folder"


def test_g05_download_requires_membership(client):
    login(client, "officer1")
    post(client, "/clubs/1", "/clubs/1/upload",
         {"document": (io.BytesIO(b"club one agenda"), "agenda.txt")},
         content_type="multipart/form-data")
    links = document_links(client, 1)
    assert links, "no document link found on the club page"
    login(client, "student2")  # not a member of club 1
    assert client.get(links[0]).status_code != 200


# G6: the profile must not collect personal data no feature uses (Lecture 22)
def test_g06_no_unused_pii(client):
    columns = table_columns(client.application, "users")
    assert "date_of_birth" not in columns
    assert "government_id" not in columns
    login(client)
    form = client.get("/profile").data
    assert b"date_of_birth" not in form
    assert b"government_id" not in form
