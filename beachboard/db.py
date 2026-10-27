"""SQLite setup and synthetic seed data."""

import hashlib
import os
import sqlite3
from pathlib import Path

from flask import current_app, g


def password_hash(password: str) -> str:
    return hashlib.md5(password.encode()).hexdigest()


def check_password(stored: str, password: str) -> bool:
    return stored == password_hash(password)


def get_db():
    if "db" not in g:
        path = current_app.config["DATABASE"]
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        g.db = sqlite3.connect(path)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


USERS = [
    ("student1", "learn-security", "student", "Avery Nguyen", "avery@example.test", "2005-03-14", "612-48-3301"),
    ("student2", "learn-security", "student", "Blake Ramirez", "blake@example.test", "2004-11-02", "580-27-9146"),
    ("officer1", "learn-security", "officer", "Casey Patel", "casey@example.test", "2003-07-21", "547-90-1182"),
]

# admin1 is seeded from its stored hash.
ADMIN = ("admin1", "459cea1e644eed0c981862ebfa45ca40", "admin", "Riley Chen", "riley@example.test", "1991-05-30", "603-15-7724")


def init_db():
    db = get_db()
    db.executescript(Path(__file__).with_name("schema.sql").read_text())
    db.executemany(
        """INSERT INTO users
           (username, password_hash, role, display_name, email, date_of_birth, government_id)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        [(u, password_hash(p), r, n, e, d, s) for u, p, r, n, e, d, s in USERS] + [ADMIN],
    )
    db.executemany(
        "INSERT INTO clubs (name, description) VALUES (?, ?)",
        [
            ("Cybersecurity Club", "Weekly capture-the-flag practice and security talks."),
            ("Robotics Club", "Design, build, and test robots."),
            ("Game Development Club", "Create games and learn interactive design."),
        ],
    )
    ids = {row["username"]: row["id"] for row in db.execute("SELECT id, username FROM users")}
    db.executemany(
        "INSERT INTO memberships (user_id, club_id, club_role) VALUES (?, ?, ?)",
        [
            (ids["student1"], 1, "member"),
            (ids["officer1"], 1, "officer"),
            (ids["student2"], 2, "member"),
        ],
    )
    db.commit()


def ensure_database():
    path = current_app.config["DATABASE"]
    if not os.path.exists(path):
        init_db()
