# BeachBoard Lite

BeachBoard Lite is a small club portal used for the CECS 378 course project. Students browse clubs, join them, and read club documents. Club officers edit their club's description and upload documents. Administrators manage user roles, download an encrypted member export, and review the audit log.

All accounts and records are synthetic. Run the application only on your own computer.

## Accounts

| Username | Password | Role |
| --- | --- | --- |
| `student1` | `learn-security` | Member of the Cybersecurity Club |
| `student2` | `learn-security` | Member of the Robotics Club |
| `officer1` | `learn-security` | Officer of the Cybersecurity Club |
| `admin1` | not provided | Administrator |

## Run with Docker

```bash
docker compose up --build
```

Open http://127.0.0.1:8080. Stop with Ctrl+C. To reset the database, run `docker compose down -v`.

## Run without Docker

Python 3.11 or newer is required. Run these commands from the project folder.

On macOS or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m beachboard.app
```

On Windows PowerShell:

```powershell
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m beachboard.app
```

Open http://127.0.0.1:8080. The database is created in `beachboard/instance/beachboard.sqlite`. Delete that file and `beachboard/instance/uploads` to reset the data.

## Tests

```bash
python -m pytest
```

The tests in `tests/functional` check normal behavior. They must still pass after your fixes. Add your security regression tests in `tests/security`.

## Layout

| Path | Contents |
| --- | --- |
| `beachboard/app.py` | Routes |
| `beachboard/auth.py` | Sign-in and role checks |
| `beachboard/db.py` | Database connection, password hashing, and seed data |
| `beachboard/crypto_util.py` | Encryption for the member export |
| `beachboard/config.py` | Application settings |
| `beachboard/debug_server.py` | Diagnostics service |
| `beachboard/templates/` | HTML templates |
| `Dockerfile`, `docker-compose.yml` | Container configuration |
