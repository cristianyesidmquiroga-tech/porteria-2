# Sistema de control de acceso (Flask)

<details>
<summary><b>Read this in English</b></summary>

Full-stack web system that manages who enters and leaves a training center: digital ID cards with barcodes, gate control with a scanner, visitor / vehicle / equipment passes, class attendance, messaging and role-based administration. Built with Flask, PostgreSQL and Docker, ready to deploy on Coolify.


**Live system:** [esena.proyecto.sbs](https://esena.proyecto.sbs/auth/login)

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

</details>

Sistema web completo que gestiona quién entra y sale de un centro de formación: carnet digital con código de barras, control de portería con escáner, pases de visitantes, vehículos y equipos, asistencia a clase, mensajería y administración por roles. Hecho con Flask, PostgreSQL y Docker, listo para desplegar en Coolify.

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.1-000000?logo=flask&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-listo-2496ED?logo=docker&logoColor=white)
![Pruebas](https://img.shields.io/badge/pruebas-800%2B-1a7f37)

**Sistema en línea:** [esena.proyecto.sbs](https://esena.proyecto.sbs/auth/login)

El mismo sistema existe también como API en Spring Boot más frontend en React: ver [`spring`](https://github.com/cristianyesidmquiroga-tech/spring) y [`react`](https://github.com/cristianyesidmquiroga-tech/react).

## Qué incluye

- **Carnet digital** por perfil (aprendiz, instructor, contratista, funcionario, subdirector...) con código de barras Code128 generado en SVG y foto de perfil validada con detección de rostro.
- **Control de portería:** vista de escáner, entradas y salidas de personas, visitantes, vehículos y equipos personales, con protección contra doble entrada y salida sin entrada. Lo que queda adentro se cierra solo a medianoche.
- **Pases y reportes:** pases de visitantes, vehículos y objetos; panel, historial por persona y reportes exportables.
- **Formación:** fichas, asistencia a clase y comunicados por correo.
- **Cuentas:** registro con verificación de correo, recuperación de contraseña, desafío anti-bot propio (prueba de trabajo, sin servicios de terceros) y cambio obligatorio de contraseña temporal.
- **Roles y vistas:** 11 perfiles, cada uno con sus permisos. Cada vista se prueba con todos los perfiles.
- **Operación:** respaldo mensual en Excel del mes anterior, tareas programadas con APScheduler, registro de auditoría y manuales de usuario en Markdown con scripts para exportarlos a PDF.

## Stack

| Capa | Herramientas |
|---|---|
| Backend | Python, Flask 3.1, SQLAlchemy, Flask-Login, Flask-WTF, Flask-Limiter, Flask-Migrate (Alembic), APScheduler |
| Datos | PostgreSQL 16 |
| Frontend | Plantillas Jinja2, CSS y JavaScript divididos por vista |
| Archivos e imágenes | Pillow, OpenCV, pandas + openpyxl (Excel) |
| Infraestructura | Docker, gunicorn, Coolify, GitHub Actions |
| Pruebas | pytest |

## Seguridad

- Contraseñas validadas en el servidor y una sola sesión activa por usuario.
- Protección CSRF en todos los formularios y límites de peticiones por ruta y por usuario.
- `SECRET_KEY` y `DATABASE_URL` obligatorias: la app no arranca sin ellas.
- Las fotos de perfil se recodifican, se guardan fuera de carpetas públicas y solo se entregan con permiso.
- Límites de caracteres, etiquetas HTML quitadas del texto libre y cookies seguras detrás de proxy.
- El manejo de datos personales sigue la Ley 1581 de 2012 (incluye página de política de privacidad).

## Estructura

```
app/
├── models/      modelos SQLAlchemy (usuarios, accesos, entidades, asistencia, mensajes)
├── routes/      blueprints: auth, main, usuarios, porteria, equipos
├── templates/   vistas Jinja2
├── static/      css/ y js/ divididos por vista
└── utils/       código de barras, captcha, cola de correo, fotos, límites, respaldos, tareas
config/          clase Config y .env.example
docker/          Dockerfile, docker-compose.yml, entrypoint
docs/            estructura, despliegue y operación, guía de migraciones, manuales
scripts/         create_admin, prueba de correo, generadores de carnets y manuales
tests/           modulos/ (por módulo), roles/ (por perfil), vistas/ (por vista)
```

Más detalle en [`docs/ESTRUCTURA_PROYECTO.md`](docs/ESTRUCTURA_PROYECTO.md) y [`docs/DESPLIEGUE_Y_OPERACION.md`](docs/DESPLIEGUE_Y_OPERACION.md).

## Cómo ponerlo a correr

Se necesita Python 3.12 y una base de datos PostgreSQL.

```bash
# base de datos para desarrollo
docker run -d --name porteria-db -e POSTGRES_USER=porteria -e POSTGRES_PASSWORD=dev -e POSTGRES_DB=porteria -p 5432:5432 postgres:16

python -m venv .venv
.venv\Scripts\activate            # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt

copy config\.env.example config\.env   # Linux/macOS: cp config/.env.example config/.env
```

Llenar `config/.env`: `SECRET_KEY`, `DATABASE_URL` (`postgresql://porteria:dev@localhost:5432/porteria`), `ADMIN_EMAIL`, `ADMIN_PASSWORD` (12 caracteres o más) y `COOKIES_SEGURAS=false` para HTTP sin cifrar. Luego:

```bash
python scripts/create_admin.py
python run.py
```

## Docker y Coolify

`docker/docker-compose.yml` construye el servicio web (python:3.12-slim, usuario sin privilegios, hora de Bogotá); la base de datos es externa y se conecta con `DATABASE_URL`. En Coolify, definir las variables de `config/.env.example` como variables de entorno y exponer el puerto 5000.

## Pruebas

```bash
pip install -r requirements-dev.txt
pytest
```

Más de 800 pruebas corren en cada push con GitHub Actions contra PostgreSQL 16. Están organizadas de tres formas: por módulo, por rol (qué puede y qué no puede hacer cada perfil) y por vista (cada vista con todos los perfiles).

## Autor

Cristian Muñoz · [GitHub](https://github.com/cristianyesidmquiroga-tech)
