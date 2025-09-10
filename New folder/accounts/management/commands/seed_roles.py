from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group


ROLES = ["admin", "pic", "pm"]


class Command(BaseCommand):
    help = "Create default user groups (roles): admin, pic, pm"

    def handle(self, *args, **options):
        created = []
        for role in ROLES:
            group, was_created = Group.objects.get_or_create(name=role)
            if was_created:
                created.append(role)
        if created:
            self.stdout.write(self.style.SUCCESS(f"Created groups: {', '.join(created)}"))
        else:
            self.stdout.write("Groups already exist.")

