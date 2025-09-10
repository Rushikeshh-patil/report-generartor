from django.core.management.base import BaseCommand
from rfis.models import RFI
from catrack.business_days import add_business_days


class Command(BaseCommand):
    help = "Recalculate due_date for all RFIs using business day logic"

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=5, help="Business days offset, default 5")

    def handle(self, *args, **options):
        days = options["days"]
        updated = 0
        for r in RFI.objects.exclude(date_received__isnull=True):
            new_due = add_business_days(r.date_received, days)
            if r.due_date != new_due:
                r.due_date = new_due
                r.save(update_fields=["due_date"]) 
                updated += 1
        self.stdout.write(self.style.SUCCESS(f"Updated due_date for {updated} RFIs."))

