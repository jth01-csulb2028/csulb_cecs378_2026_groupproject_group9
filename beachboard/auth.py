"""Sign-in helpers."""

from functools import wraps

from flask import abort, g, redirect, session, url_for

from .db import get_db


def load_user():
    user_id = session.get("user_id")
    g.user = (
        get_db().execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if user_id is not None
        else None
    )


def login_required(view):
    @wraps(view)
    def wrapped(**kwargs):
        if g.user is None:
            return redirect(url_for("login"))
        return view(**kwargs)

    return wrapped


def require_role(*roles):
    def decorate(view):
        @wraps(view)
        def wrapped(**kwargs):
            if g.user is None:
                return redirect(url_for("login"))
            if g.user["role"] not in roles:
                abort(403)
            return view(**kwargs)

        return wrapped

    return decorate
