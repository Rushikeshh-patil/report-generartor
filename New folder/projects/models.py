import uuid
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Project(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    number = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    managers = models.ManyToManyField(User, related_name="managed_projects", blank=True)
    principals = models.ManyToManyField(User, related_name="principal_projects", blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["number"]
        indexes = [
            models.Index(fields=["active"]),
        ]

    def __str__(self) -> str:
        return f"{self.number} — {self.name}"


# Create your models here.
