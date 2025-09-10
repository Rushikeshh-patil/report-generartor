from django.contrib import admin
from .models import ActivityLog


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "actor", "action", "from_status", "to_status", "target")
    search_fields = ("action", "notes")
    list_filter = ("action", "created_at")


# Register your models here.
