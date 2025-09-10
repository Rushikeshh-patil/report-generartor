from django.contrib import admin
from .models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("number", "name", "active", "created_at")
    search_fields = ("number", "name")
    list_filter = ("active",)
    filter_horizontal = ("managers", "principals")


# Register your models here.
