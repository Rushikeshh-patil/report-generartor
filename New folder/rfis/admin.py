from django.contrib import admin
from .models import RFI


@admin.register(RFI)
class RFIAdmin(admin.ModelAdmin):
    list_display = (
        "rfi_number",
        "name",
        "project",
        "assigned_to",
        "status",
        "date_received",
        "due_date",
        "date_responded",
    )
    search_fields = ("rfi_id", "rfi_number", "originator", "name")
    list_filter = ("status", "project", "assigned_to")
    date_hierarchy = "date_received"
    autocomplete_fields = ("project", "assigned_to")


# Register your models here.
