# REST API Spec (Draft)

## Auth
- Session-based auth with CSRF for server-rendered UI
- Optional token/JWT for API-only clients

### Endpoints
- `POST /api/auth/login` → 200 with user + roles
- `POST /api/auth/logout` → 204
- `GET /api/auth/me` → current user context (id, name, roles)

## Users & Roles
- `GET /api/users?search=` (admin)
- `GET /api/roles` → [`admin`, `pic`, `pm`]

## Projects
- `GET /api/projects` (filters: `q`, `active`, `manager`, `principal`)
- `POST /api/projects` (admin)
- `GET /api/projects/:id`
- `PATCH /api/projects/:id` (admin)
- `POST /api/projects/:id/archive` (admin)

Project JSON
```
{
  "id": "uuid",
  "number": "25-001",
  "name": "Downtown Medical Center",
  "managers": ["user_uuid"],
  "principals": ["user_uuid"],
  "active": true,
  "created_at": "2025-01-15T10:00:00Z",
  "updated_at": "2025-01-15T10:00:00Z"
}
```

## Submittals
- `GET /api/submittals`
  - Filters: `project`, `status`, `assigned_pm`, `originator`, `received_from`, `received_to`, `due_from`, `due_to`, `overdue`
  - Sorting: `sort=due_date|-due_date`
  - Pagination: `page`, `page_size`
- `POST /api/submittals` (admin/pm)
- `GET /api/submittals/:id`
- `PATCH /api/submittals/:id` (role-guarded transitions)
- `POST /api/submittals/:id/transition` with `{ to_status, notes }` (preferred for workflow)
- `GET /api/submittals/export.csv` (applies current filters)
- `GET /api/submittals/export.pdf` (queued job; returns file when ready)

Submittal JSON
```
{
  "id": "uuid",
  "submittal_id": "SUB-2025-0001",
  "project": "project_uuid",
  "spec_section": "08 80 00",
  "description": "Glazing - shop drawings",
  "status": "IN_REVIEW",
  "assigned_pm": "user_uuid",
  "originator": "General Contractor",
  "date_received": "2025-01-10",
  "date_logged": "2025-01-10",
  "due_date": "2025-01-17",
  "date_returned": null,
  "notes": "Initial review started",
  "is_overdue": false
}
```

## RFIs
- `GET /api/rfis` (filters: `project`, `status`, `assigned_to`, `overdue`, date ranges)
- `POST /api/rfis`
- `GET /api/rfis/:id`
- `PATCH /api/rfis/:id`
- `GET /api/rfis/export.csv`

RFI JSON
```
{
  "id": "uuid",
  "rfi_id": "RFI-2025-0005",
  "project": "project_uuid",
  "assigned_to": "user_uuid",
  "originator": "General Contractor",
  "date_received": "2025-01-10",
  "due_date": "2025-01-17",
  "date_responded": null,
  "question": "Clarify door hardware spec.",
  "response": null,
  "status": "OPEN",
  "is_overdue": true
}
```

## Reporting
- Exports respect filters. CSV generation is synchronous for small datasets; PDF generation can be queued and downloaded via a token/URL when ready
- `GET /api/reports/overview` → dashboard metrics
  - `my_assigned_counts` (submittals, rfis)
  - `overdue_submittals`, `overdue_rfis`
  - `by_project` summaries

## Errors
- 400: validation/state transition errors (include `code` and `detail`)
- 403: unauthorized action (role/assignment)
- 404: not found or not visible to user

