# Construction Administration Tracking (Django + DRF)

## Quickstart (Dev)
- Create env: `python -m venv .venv`
- Install deps: `.venv\\Scripts\\python -m pip install -U pip && .venv\\Scripts\\python -m pip install -r requirements.txt` (or use the preinstalled venv if already created)
- Copy `.env.example` to `.env` and adjust as needed
- Run migrations: `.venv\\Scripts\\python manage.py migrate`
- Seed roles: `.venv\\Scripts\\python manage.py seed_roles`
- Create superuser: `.venv\\Scripts\\python manage.py createsuperuser`
- Start server: `.venv\\Scripts\\python manage.py runserver`

## API
- Admin: `/admin/`
- API root: `/api/`
  - Projects: `/api/projects/`
  - Submittals: `/api/submittals/`
  - RFIs: `/api/rfis/`

## Notes
- Default DB is SQLite for dev; switch to Postgres via `.env` when deploying.
- SMTP/email not wired yet; will be added in later phase.
- Business-day logic lives in `catrack/business_days.py` and excludes weekends and configured holidays.

