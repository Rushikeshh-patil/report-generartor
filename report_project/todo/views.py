# todo/views.py

from django.shortcuts import render
from django.views.generic import ListView
from .models import Task

class TaskListView(ListView):
    model = Task
    template_name = 'todo/task_list.html'
    context_object_name = 'tasks'

    def get_queryset(self):
        # This can be expanded to filter tasks by user, project, etc.
        return Task.objects.all()