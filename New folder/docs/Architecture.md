# Construction Administration Tracking Web App — Architecture

## Goals
- Self-hosted internal app for ~40 users to manage Projects, Submittals, and RFIs with clear roles (Admin, PIC, PM), searchable lists, and exportable reports.
- Prioritize fast delivery, maintainability, and simple ops.

## Recommended Stack
- Backend: Python 3.12, Django 5.x, Django REST Framework (DRF)
- DB: PostgreSQL 15+ (row-level locking, robust JSON support, full-text search optional)
- Cache/Broker: Redis (notifications, async tasks)
- Async/Jobs: Celery (notifications, scheduled reminders, CSV/PDF generation)
- Auth: Django auth (username/email + password), optional SSO via Azure AD/Okta (SAML/OIDC)
- Storage: Local/NFS or S3-compatible (e.g., MinIO) for attachments
- Web: gunicorn/uvicorn + Nginx (Linux) or IIS/wfastcgi (Windows). Recommended: Docker Compose for consistency
- UI: Server-rendered Django templates + HTMX/Alpine for speed; or add React later if needed

## High-Level Modules
- Accounts: Users, Groups (Admin, PIC, PM), profile settings
- Projects: Project database (number, name, assignments, active flag)
- Submittals: Core workflow, statuses, due-date logic, overdue detection
- RFIs: Similar tracking with simpler states
- Holidays/Calendars: Business-day calculations and configurable holidays
- Reporting & Export: CSV/PDF exports of filtered views
- Notifications: Email reminders/escalations (Celery)
- Audit & Activity: Status changes, assignments, and critical edits

## Key Design Decisions
- Roles via Groups: Admin (full CRUD), PIC (company-wide read + approve), PM (scoped to assigned items)
- Object scoping: PMs see only assigned items; PICs see all; Admins see all
- State transitions are validated server-side; only permitted roles can perform certain transitions
- Due dates computed using business-day calendar (weekends + configurable holiday set)
- Overdue flag derived dynamically (not stored), with DB index on `due_date` for fast queries

## Non-Functional Requirements
- Security: RBAC, CSRF protection, server-side validations, audit logs
- Performance: Indexed filters on `status`, `due_date`, `assigned_to`, `project`
- Reliability: Nightly DB backups; attachment backup/retention policy
- Observability: Structured logs, request/SQL timings, health checks (`/healthz`)
- Deployability: Docker Compose config with `.env` for secrets; staging environment parity

## Deployment Outline (Docker Compose)
- Services: `web` (Django), `worker` (Celery), `scheduler` (Celery beat), `db` (Postgres), `cache` (Redis), `nginx` (reverse-proxy)
- Volumes: Postgres data, media files (attachments), optional Nginx logs
- Envs: `DJANGO_SECRET_KEY`, `DATABASE_URL`, `REDIS_URL`, `EMAIL_*`
- TLS: Terminate at Nginx with organization TLS or reverse proxy; alternatively terminate upstream

## Email & Notifications
- SMTP integration (Office365/Exchange/Gmail relays). Template-driven messages for:
  - Assignment changes
  - Upcoming due (T-2 business days)
  - Due today
  - Overdue escalations

## Attachments
- Store on disk or S3-compatible backend with virus-scan hook (optional)
- Restrict file types/sizes via server-side validation

## Future Options
- Frontend SPA with React and DRF
- SSO integration (Azure AD/Okta)
- Advanced reporting with Metabase/Superset connected read-only to Postgres

