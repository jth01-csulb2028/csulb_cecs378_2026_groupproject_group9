import os
import sys
from html.parser import HTMLParser
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("BEACHBOARD_SECRET_KEY", "test-only-secret")
os.environ.setdefault("BEACHBOARD_EXPORT_KEY", "dGVzdC1vbmx5LWV4cG9ydC1rZXktMzItYnl0ZXMhISE=")

from beachboard.app import create_app  # noqa: E402
from beachboard.db import get_db  # noqa: E402


@pytest.fixture()
def app(tmp_path):
    return create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-only-secret",
            "DATABASE": str(tmp_path / "test.sqlite"),
            "UPLOAD_FOLDER": str(tmp_path / "uploads"),
        }
    )


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def db(app):
    with app.app_context():
        yield get_db()


class HiddenInputs(HTMLParser):
    def __init__(self):
        super().__init__()
        self.fields = {}

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "input" and attrs.get("type") == "hidden" and attrs.get("name"):
            self.fields[attrs["name"]] = attrs.get("value") or ""


def hidden_fields(client, page):
    """Return the hidden input fields of the forms on page."""
    parser = HiddenInputs()
    parser.feed(client.get(page).data.decode())
    return parser.fields


def post(client, page, url, data=None, **kwargs):
    """Submit a form found on page to url, including the form's hidden fields."""
    fields = hidden_fields(client, page)
    fields.update(data or {})
    return client.post(url, data=fields, **kwargs)


def login(client, username="student1"):
    if username == "admin1":
        # The admin password is not provided, so the test signs in by setting the session.
        with client.application.app_context():
            user_id = get_db().execute(
                "SELECT id FROM users WHERE username = ?", (username,)
            ).fetchone()["id"]
        with client.session_transaction() as sess:
            sess["user_id"] = user_id
        return client.get("/clubs", follow_redirects=True)
    return post(
        client,
        "/login",
        "/login",
        {"username": username, "password": "learn-security"},
        follow_redirects=True,
    )
