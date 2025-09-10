# Workflows & Business Rules

## Submittal Workflow
- States: `IN_REVIEW` → `READY_PIC_REVIEW` → `READY_TO_RETURN` → `RETURNED`
- Terminal/Side: `VOID` (from any state by Admin)

### Transitions & Role Permissions
- `New`/`In Review`: Admin creates; assigns PM; status defaults to `IN_REVIEW`
- `IN_REVIEW` → `READY_PIC_REVIEW`: by PM or Admin
- `READY_PIC_REVIEW` → `READY_TO_RETURN`: by PIC or Admin
- `READY_TO_RETURN` → `RETURNED`: by Admin (enter `date_returned` required)
- `*` → `VOID`: by Admin only
- Optional reversal: PIC can request changes → Admin/PM may revert to `IN_REVIEW` with note (audit logged)

### Due Date (Business Days)
- Default: `due_date = date_received + 5 business days`
- Business day definition: Mon–Fri excluding configured holidays
- Holidays stored in DB (table `Holiday`), optional per-year import

### Overdue Flag
- `is_overdue = (today > due_date) AND status NOT IN {RETURNED, VOID}`
- Calculated dynamically for UI and filters; do not store unless denormalization is later required

## RFI Workflow
- States: `OPEN` → `AWAITING_RESPONSE` → `CLOSED`
- Roles:
  - Admin: full CRUD
  - PIC: view all; can move to `AWAITING_RESPONSE` or `CLOSED` if assigned
  - PM: view and update only if assigned
- Due date defaults to 5 business days (configurable)

## Business Day Calculation (Pseudocode)
```
function add_business_days(start_date, days):
    d = start_date
    added = 0
    while added < days:
        d = d + 1 day
        if is_business_day(d):
            added += 1
    return d

function is_business_day(d):
    if weekday(d) in [Saturday, Sunday]:
        return false
    if exists Holiday where date = d and is_business_day = false:
        return false
    return true
```

## Notifications
- T-2 business days: reminder to `assigned_pm` (Submittal) / `assigned_to` (RFI)
- T-0 (due date): escalation to assigned PIC and Admin
- T+1 and onward: daily overdue summary to PIC/Admin
- All notifications are opt-in per user (profile setting) initially

## Audit & Activity
- Log: actor, transition (from→to), timestamp, notes
- Show timeline on detail pages for Submittals and RFIs

## Search/Filter Rules
- Filters: Project, Status, Assigned User, Date Range (`date_received` / `due_date`), Overdue
- Sort by: Due Date (default asc), Date Received, Status

