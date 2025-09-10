from django.contrib import admin
from .models import Holiday


@admin.register(Holiday)
class HolidayAdmin(admin.ModelAdmin):
    list_display = ("date", "name", "is_business_day")
    search_fields = ("name",)
    list_filter = ("is_business_day",)


# Register your models here.
