from django.contrib import admin
from .models import Submittal


@admin.register(Submittal)
class SubmittalAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "submittal_id",
        "project",
        "spec_section",
        "status",
        "assigned_pm",
        "date_received",
        "due_date",
        "date_returned",
    )
    search_fields = ("submittal_id", "name", "spec_section", "description", "originator")
    list_filter = ("status", "project", "assigned_pm")
    date_hierarchy = "date_received"
    autocomplete_fields = ("project", "assigned_pm")


# Register your models here.
