# Roles & Permissions

## Roles (Groups)
- `admin`: Full CRUD across all modules; manage users and roles
- `pic`: Read all projects/items; can approve submittals for their review; limited write on assigned items
- `pm`: Access limited to assigned projects/items; can move Submittals to `READY_PIC_REVIEW`

## Module Permissions
- Projects:
  - Admin: create, edit, archive
  - PIC: read all
  - PM: read if assigned (via managers/principals M2M)
- Submittals:
  - Admin: full CRUD, status changes, set `date_returned`
  - PIC: read all; change `READY_PIC_REVIEW` → `READY_TO_RETURN` when applicable
  - PM: create (if allowed), edit only if assigned_pm; change `IN_REVIEW` → `READY_PIC_REVIEW`
- RFIs:
  - Admin: full CRUD
  - PIC: read all; update if assigned
  - PM: read/update if assigned

## Enforcement Strategy (Django)
- Use Groups for role membership
- Global Permissions: map to coarse actions (e.g., `projects.view_all` for PIC/Admin)
- Object Scoping:
  - Queryset filtering in views/admin: PMs restricted to items where they are assigned or on the project team
  - PICs see all items; PMs see only assigned
- Admin site customizations:
  - Override `get_queryset` to restrict PM visibility
  - Read-only fields based on role and state
- DRF API:
  - Custom `permissions.BasePermission` enforcing role + assignment checks
  - Serializer-level validation for allowed transitions

## Status Transition Guards
- Submittal:
  - Only PM/Admin can move `IN_REVIEW` → `READY_PIC_REVIEW`
  - Only PIC/Admin can move `READY_PIC_REVIEW` → `READY_TO_RETURN`
  - Only Admin can set `RETURNED` and must provide `date_returned`
  - Only Admin can set `VOID`
- RFI:
  - Updates allowed by assigned PIC/PM or Admin

