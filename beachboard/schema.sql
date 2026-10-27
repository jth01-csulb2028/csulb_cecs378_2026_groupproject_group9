DROP TABLE IF EXISTS audit_log;
DROP TABLE IF EXISTS documents;
DROP TABLE IF EXISTS memberships;
DROP TABLE IF EXISTS clubs;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('student', 'officer', 'admin')),
    display_name TEXT NOT NULL,
    email TEXT NOT NULL,
    date_of_birth TEXT,
    government_id TEXT
);

CREATE TABLE clubs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT NOT NULL
);

CREATE TABLE memberships (
    user_id INTEGER NOT NULL REFERENCES users(id),
    club_id INTEGER NOT NULL REFERENCES clubs(id),
    club_role TEXT NOT NULL DEFAULT 'member',
    PRIMARY KEY (user_id, club_id)
);

CREATE TABLE documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    club_id INTEGER NOT NULL REFERENCES clubs(id),
    stored_name TEXT NOT NULL,
    uploaded_by INTEGER NOT NULL REFERENCES users(id),
    uploaded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    actor_id INTEGER REFERENCES users(id),
    action TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
