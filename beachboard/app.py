"""BeachBoard Lite Flask application."""

import csv
import io
import os
from pathlib import Path

from flask import (
    Flask,
    abort,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)

from . import config
from .auth import load_user, login_required, require_role
from .crypto_util import encrypt_export
from .db import check_password, close_db, ensure_database, get_db


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=config.SECRET_KEY,
        DATABASE=os.getenv(
            "BEACHBOARD_DATABASE", str(Path(app.instance_path) / "beachboard.sqlite")
        ),
        UPLOAD_FOLDER=os.getenv(
            "BEACHBOARD_UPLOAD_DIR", str(Path(app.instance_path) / "uploads")
        ),
        SESSION_COOKIE_HTTPONLY=False,
    )
    if test_config:
        app.config.update(test_config)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)
    app.teardown_appcontext(close_db)
    app.before_request(load_user)

    def club_role(club_id):
        if g.user is None:
            return None
        row = get_db().execute(
            "SELECT club_role FROM memberships WHERE user_id = ? AND club_id = ?",
            (g.user["id"], club_id),
        ).fetchone()
        return row["club_role"] if row else None

    @app.get("/")
    def index():
        return redirect(url_for("clubs"))

    @app.route("/login", methods=("GET", "POST"))
    def login():
        if request.method == "POST":
            user = get_db().execute(
                "SELECT * FROM users WHERE username = ?", (request.form["username"],)
            ).fetchone()
            if user is None or not check_password(user["password_hash"], request.form["password"]):
                flash("Invalid username or password.")
            else:
                session["user_id"] = user["id"]
                return redirect(url_for("clubs"))
        return render_template("login.html")

    @app.post("/logout")
    def logout():
        session.clear()
        return redirect(url_for("login"))

    @app.get("/clubs")
    def clubs():
        rows = get_db().execute("SELECT * FROM clubs ORDER BY name").fetchall()
        return render_template("clubs.html", clubs=rows)

    @app.get("/clubs/search")
    def search_clubs():
        q = request.args.get("q", "")
        rows = get_db().execute(
            f"SELECT * FROM clubs WHERE name LIKE '%{q}%' ORDER BY name"
        ).fetchall()
        return render_template("clubs.html", clubs=rows, query=q)

    @app.get("/clubs/<int:club_id>")
    def club_detail(club_id):
        club = get_db().execute("SELECT * FROM clubs WHERE id = ?", (club_id,)).fetchone()
        if club is None:
            abort(404)
        documents = get_db().execute(
            "SELECT * FROM documents WHERE club_id = ? ORDER BY uploaded_at DESC", (club_id,)
        ).fetchall()
        return render_template(
            "club_detail.html", club=club, role=club_role(club_id), documents=documents
        )

    @app.post("/clubs/<int:club_id>/join")
    @login_required
    def join_club(club_id):
        get_db().execute(
            "INSERT OR IGNORE INTO memberships (user_id, club_id) VALUES (?, ?)",
            (g.user["id"], club_id),
        )
        get_db().commit()
        flash("Club joined.")
        return redirect(url_for("club_detail", club_id=club_id))

    @app.post("/clubs/<int:club_id>/description")
    @login_required
    def edit_description(club_id):
        if g.user["role"] != "admin" and club_role(club_id) != "officer":
            abort(403)
        get_db().execute(
            "UPDATE clubs SET description = ? WHERE id = ?",
            (request.form["description"], club_id),
        )
        get_db().commit()
        flash("Description updated.")
        return redirect(url_for("club_detail", club_id=club_id))

    @app.get("/api/members/<int:club_id>")
    @login_required
    def members_api(club_id):
        rows = get_db().execute(
            """SELECT u.id, u.display_name, u.email, u.date_of_birth, m.club_role
               FROM memberships m JOIN users u ON u.id = m.user_id
               WHERE m.club_id = ? ORDER BY u.display_name""",
            (club_id,),
        ).fetchall()
        return jsonify([dict(row) for row in rows])

    @app.post("/clubs/<int:club_id>/upload")
    @login_required
    def upload(club_id):
        if g.user["role"] != "admin" and club_role(club_id) != "officer":
            abort(403)
        uploaded = request.files.get("document")
        if uploaded is None or not uploaded.filename:
            abort(400)
        uploaded.save(os.path.join(app.config["UPLOAD_FOLDER"], uploaded.filename))
        get_db().execute(
            "INSERT INTO documents (club_id, stored_name, uploaded_by) VALUES (?, ?, ?)",
            (club_id, uploaded.filename, g.user["id"]),
        )
        get_db().commit()
        flash("Document uploaded.")
        return redirect(url_for("club_detail", club_id=club_id))

    @app.get("/documents")
    @login_required
    def document():
        name = request.args.get("name", "")
        return send_file(os.path.join(app.config["UPLOAD_FOLDER"], name))

    @app.route("/profile", methods=("GET", "POST"))
    @login_required
    def profile():
        if request.method == "POST":
            get_db().execute(
                """UPDATE users SET display_name = ?, email = ?, date_of_birth = ?,
                   government_id = ? WHERE id = ?""",
                (
                    request.form["display_name"],
                    request.form["email"],
                    request.form.get("date_of_birth", ""),
                    request.form.get("government_id", ""),
                    g.user["id"],
                ),
            )
            get_db().commit()
            flash("Profile updated.")
            return redirect(url_for("profile"))
        return render_template("profile.html")

    @app.get("/admin/users")
    @require_role("admin")
    def admin_users():
        rows = get_db().execute("SELECT id, username, role, display_name FROM users").fetchall()
        return render_template("admin_users.html", rows=rows)

    @app.get("/admin/users/<int:user_id>/role")
    @require_role("admin")
    def admin_change_role(user_id):
        new_role = request.args.get("role", "")
        if new_role not in {"student", "officer", "admin"}:
            abort(400)
        get_db().execute("UPDATE users SET role = ? WHERE id = ?", (new_role, user_id))
        get_db().commit()
        flash(f"User {user_id} is now {new_role}.")
        return redirect(url_for("admin_users"))

    @app.get("/admin/export")
    @require_role("admin")
    def admin_export():
        rows = get_db().execute(
            "SELECT username, role, display_name, email, date_of_birth, government_id FROM users"
        ).fetchall()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(rows[0].keys())
        writer.writerows([tuple(row) for row in rows])
        return send_file(
            io.BytesIO(encrypt_export(output.getvalue().encode())),
            mimetype="application/octet-stream",
            as_attachment=True,
            download_name="members.csv.enc",
        )

    @app.get("/admin/audit")
    @require_role("admin")
    def admin_audit():
        rows = get_db().execute("SELECT * FROM audit_log ORDER BY created_at DESC").fetchall()
        return render_template("audit.html", rows=rows)

    with app.app_context():
        ensure_database()
    return app


if __name__ == "__main__":
    create_app().run(host=os.getenv("BEACHBOARD_HOST", "127.0.0.1"), port=8080)
