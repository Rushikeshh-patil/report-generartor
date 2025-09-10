from django.core.management.base import BaseCommand
from holidays.models import Holiday
from datetime import date


class Command(BaseCommand):
    help = "Import US federal/state holidays for a given year into Holiday table"

    def add_arguments(self, parser):
        parser.add_argument("year", type=int, nargs="?", help="Year to import (defaults to current year)")
        parser.add_argument("--state", dest="state", default=None, help="Two-letter state code, e.g., CA")
        parser.add_argument("--observed", dest="observed", action="store_true", help="Include observed dates")

    def handle(self, *args, **options):
        try:
            import holidays as pyholidays
        except ImportError:
            self.stderr.write("python-holidays is not installed. pip install holidays")
            return

        year = options.get("year") or date.today().year
        state = options.get("state")
        observed = options.get("observed", False)

        us = pyholidays.UnitedStates(years=year, state=state, observed=observed)
        created = 0
        for d, name in us.items():
            obj, was_created = Holiday.objects.get_or_create(date=d, defaults={"name": name, "is_business_day": False})
            if was_created:
                created += 1
        self.stdout.write(self.style.SUCCESS(f"Imported {created} holidays for {year}{' ('+state+')' if state else ''}."))

