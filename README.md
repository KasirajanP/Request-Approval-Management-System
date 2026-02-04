# Request Approval Management System

Minimal Django + DRF backend for creating requests and approving/rejecting them.

## Quick Start

1. Create and activate a virtual environment.
2. Install dependencies.
3. Run migrations.
4. Start the server.

```powershell
cd .\backend
.\venv\Scripts\python -m pip install django djangorestframework djangorestframework-simplejwt
.\venv\Scripts\python manage.py migrate
.\venv\Scripts\python manage.py runserver
```

## API Endpoints

- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/requests/`
- `GET  /api/requests/my/`
- `POST /api/requests/{id}/action/`

## Roles

- `EMPLOYEE`
- `APPROVER`

## Notes

- SQLite database at `backend/db.sqlite3`.
- JWT authentication required for protected endpoints.

## Deploy on Render

This repo includes `render.yaml` and `build.sh` for a one-click Render deploy.

1. Push to GitHub.
2. Create a new Render Blueprint from the repo.
3. Render will run `bash build.sh` and start the web service.

For the "New Web Service" flow, set:
- Build command: `bash build.sh`
- Start command: `python -m gunicorn approval_system.asgi:application -k uvicorn.workers.UvicornWorker --chdir backend`

SQLite is configured via `SQLITE_PATH` and a persistent disk in `render.yaml`.
If you prefer Render Postgres, set `DATABASE_URL` and remove the `disk`/`SQLITE_PATH` entries.
