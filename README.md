# Access Control System (Flask)

Full-stack web system that manages who enters and leaves a training center: digital ID cards with barcodes, gate control with a scanner, visitor / vehicle / equipment passes, class attendance, messaging and role-based administration. Built with Flask, PostgreSQL and Docker, ready to deploy on Coolify.

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.1-000000?logo=flask&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white)
![Tests](https://img.shields.io/badge/tests-800%2B-1a7f37)

The same system also exists as a Spring Boot API plus a React front end: see [`spring`](https://github.com/cristianyesidmquiroga-tech/spring) and [`react`](https://github.com/cristianyesidmquiroga-tech/react).

## Features

- **Digital ID card** per profile (apprentice, instructor, contractor, official, subdirector...) with a Code128 barcode generated as SVG, and a profile photo validated with face detection.
- **Gate control:** scanner view, entries and exits for people, visitors, vehicles and personal equipment, with duplicate-entry and exit-without-entry protection. Everything still inside is closed automatically at midnight.
- **Passes and reports:** visitor, vehicle and object passes; dashboard, per-person history and exportable reports.
- **Training module:** training groups, class attendance and announcements sent by email.
- **Accounts:** registration with email verification, password recovery, self-hosted anti-bot challenge (proof of work, no third-party service) and a first-login password change.
- **Roles and views:** 11 profiles, each with its own permissions. Every view is tested against every profile.
- **Operations:** monthly Excel backup of the previous month, scheduled jobs with APScheduler, audit log, and user manuals in Markdown with scripts to export them to PDF.

## Stack

| Layer | Tools |
|---|---|
| Backend | Python, Flask 3.1, SQLAlchemy, Flask-Login, Flask-WTF, Flask-Limiter, Flask-Migrate (Alembic), APScheduler |
| Data | PostgreSQL 16 |
| Frontend | Jinja2 templates, CSS and JavaScript split by view |
| Files and images | Pillow, OpenCV, pandas + openpyxl (Excel) |
| Infra | Docker, gunicorn, Coolify, GitHub Actions |
| Tests | pytest |

## Security

- Passwords validated server-side; one active session per user.
- CSRF protection on every form and rate limits per route and per user.
- Required `SECRET_KEY` and `DATABASE_URL`: the app refuses to start without them.
- Profile photos are re-encoded, stored outside public folders and served only with permission.
- Input length limits, HTML stripped from free text, secure cookies behind a proxy.
- Personal-data handling follows Colombian Law 1581 of 2012 (privacy policy page included).

## Project layout

```
app/
├── models/      SQLAlchemy models (users, access, entities, attendance, messages)
├── routes/      blueprints: auth, main, usuarios, porteria, equipos
├── templates/   Jinja2 views
├── static/      css/ and js/ split by view
└── utils/       barcode, captcha, email queue, photos, rate limits, backups, jobs
config/          Config class and .env.example
docker/          Dockerfile, docker-compose.yml, entrypoint
docs/            structure, deployment and operations, migrations runbook, manuals
scripts/         create_admin, email test, card and manual generators
tests/           modulos/ (by module), roles/ (by profile), vistas/ (by view)
```

More detail in [`docs/ESTRUCTURA_PROYECTO.md`](docs/ESTRUCTURA_PROYECTO.md) and [`docs/DESPLIEGUE_Y_OPERACION.md`](docs/DESPLIEGUE_Y_OPERACION.md).

## Run it locally

You need Python 3.12 and a PostgreSQL database.

```bash
# database for development
docker run -d --name porteria-db -e POSTGRES_USER=porteria -e POSTGRES_PASSWORD=dev -e POSTGRES_DB=porteria -p 5432:5432 postgres:16

python -m venv .venv
.venv\Scripts\activate            # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt

copy config\.env.example config\.env   # Linux/macOS: cp config/.env.example config/.env
```

Fill in `config/.env`: `SECRET_KEY`, `DATABASE_URL` (`postgresql://porteria:dev@localhost:5432/porteria`), `ADMIN_EMAIL`, `ADMIN_PASSWORD` (12+ characters) and `COOKIES_SEGURAS=false` for plain HTTP. Then:

```bash
python scripts/create_admin.py
python run.py
```

## Docker and Coolify

`docker/docker-compose.yml` builds the web service (python:3.12-slim, non-root user, Bogotá time zone); the database is external and connected through `DATABASE_URL`. In Coolify, set the variables listed in `config/.env.example` as environment variables and expose port 5000.

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

800+ tests run on every push with GitHub Actions against PostgreSQL 16. They are organized three ways: by module, by role (what each profile can and cannot do) and by view (each view with every profile).

## Author

Cristian Muñoz · [GitHub](https://github.com/cristianyesidmquiroga-tech)
