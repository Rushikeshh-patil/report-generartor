# Implementation Plan

## Phase 0 — Project Setup (0.5–1 day)
- Initialize Django project (`poetry` or `pip-tools` for deps)
- Add apps: `accounts`, `projects`, `submittals`, `rfis`, `holidays`, `reports`
- Configure Postgres, Redis, Celery, DRF, static/media storage
- Seed roles/groups: `admin`, `pic`, `pm`

## Phase 1 — Models & Admin (1–2 days)
- Implement models per DataModel
- Auto-generate human IDs (`submittal_id`, `rfi_id`)
- Business day utilities and signals to compute `due_date`
- Django admin with list filters/search, role-based readonly fields

## Phase 2 — Permissions & Workflows (1–2 days)
- Implement queryset scoping for PM vs PIC/Admin
- DRF permissions for object-level access
- Workflow endpoints (`transition`), validation/guards, audit logging

## Phase 3 — UI & Dashboards (2–3 days)
- Server-rendered list/detail pages with filters (HTMX)
- Dashboard: my assignments, overdue submittals/RFIs, by-project cards
- Visibility differences by role

## Phase 4 — Reporting & Exports (1 day)
- CSV export for current filters (Submittals/RFIs)
- PDF export for submittal log (queued job with download link)

## Phase 5 — Notifications (1 day)
- Email templates and Celery schedules for reminders/escalations
- User preference toggles for emails

## Phase 6 — Hardening & Deploy (1–2 days)
- Add tests (business days, permissions, transitions)
- Docker Compose, `.env`, health checks, logging
- Backups and basic runbook

## Acceptance Criteria (Samples)
- Submittal `due_date` excludes weekends/holidays; unit tests cover edge cases
- Overdue items flagged when `today > due_date` and status not `RETURNED/VOID`
- PMs cannot see items outside assignments; PIC sees all; Admin full
- Status transitions restricted by role; invalid transitions blocked with clear errors
- CSV export matches filtered view; PDF renders correctly for basic dataset

## Risks & Mitigations
- Ambiguity in reassignment/role overrides → capture in ActivityLog, require notes
- Holiday calendar maintenance → provide import from CSV
- PDF rendering in restricted environments → fall back to CSV/HTML print styles

## Next Steps
- Confirm tech stack choice (Django/DRF as recommended)
- Approve model and workflow specs
- Decide on SSO vs local auth
- Provide SMTP details and initial holiday list

