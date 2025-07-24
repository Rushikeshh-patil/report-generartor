from django.contrib import admin
from .models import Project, Task, SubTask

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    """
    Customizes the admin interface for the Project model.
    """
    list_display = ('name', 'owner', 'created_at')
    search_fields = ('name', 'description')
    list_filter = ('owner',)
    filter_horizontal = ('members',) # Makes many-to-many selection easier

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """
    Customizes the admin interface for the Task model.
    """
    list_display = ('title', 'project', 'assignee', 'status', 'estimated_hours', 'actual_hours')
    search_fields = ('title', 'project__name')
    list_filter = ('status', 'project', 'assignee')
    # These fields are calculated automatically and should not be edited directly
    readonly_fields = ('started_at', 'completed_at', 'actual_hours', 'time_variance') 

@admin.register(SubTask)
class SubTaskAdmin(admin.ModelAdmin):
    """
    Customizes the admin interface for the SubTask model.
    """
    list_display = ('title', 'task', 'done')
    search_fields = ('title', 'task__title')
    list_filter = ('done',)