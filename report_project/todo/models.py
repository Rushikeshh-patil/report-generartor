# todo/models.py

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Project(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_projects')
    members = models.ManyToManyField(User, related_name='projects')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Task(models.Model):
    STATUS_CHOICES = (
        ('todo', 'To Do'),
        ('inprogress', 'In Progress'),
        ('done', 'Done'),
    )

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    assignee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks')
    estimated_hours = models.DecimalField(max_digits=5, decimal_places=2, help_text="Estimated time in hours to complete the task.")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='todo')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title

    def mark_as_complete(self):
        self.status = 'done'
        self.completed_at = timezone.now()
        self.save()

    @property
    def time_variance(self):
        if self.completed_at:
            # This is a simplified calculation. A more complex calculation would be needed
            # to only account for working hours.
            actual_hours = (self.completed_at - self.created_at).total_seconds() / 3600
            return actual_hours - float(self.estimated_hours)
        return None

class SubTask(models.Model):
    title = models.CharField(max_length=200)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='subtasks')
    done = models.BooleanField(default=False)

    def __str__(self):
        return self.title