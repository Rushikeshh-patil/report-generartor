import uuid
from datetime import date
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

from catrack.business_days import add_business_days
from projects.models import Project

User = get_user_model()


class SubmittalStatus(models.TextChoices):
    IN_REVIEW = "IN_REVIEW", "In Review"
    READY_PIC_REVIEW = "READY_PIC_REVIEW", "Ready for PIC Review"
    READY_TO_RETURN = "READY_TO_RETURN", "Ready to Return"
    RETURNED = "RETURNED", "Returned"
    VOID = "VOID", "Void"


def generate_submittal_id() -> str:
    ts = timezone.now().strftime("%Y%m%d%H%M%S")
    return f"SUB-{ts}-{str(uuid.uuid4())[:8]}"


class Submittal(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    submittal_id = models.CharField(max_length=40, unique=True, blank=True)
    name = models.CharField(max_length=200, blank=True, default="")
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="submittals")
    spec_section = models.CharField(max_length=20)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=SubmittalStatus.choices, default=SubmittalStatus.IN_REVIEW)
    assigned_pm = models.ForeignKey(User, on_delete=models.PROTECT, related_name="assigned_submittals")
    originator = models.CharField(max_length=120)
    date_received = models.DateField()
    date_logged = models.DateField(default=timezone.localdate)
    due_date = models.DateField(blank=True, null=True)
    date_returned = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["due_date", "date_received"]
        indexes = [
            models.Index(fields=["project", "status"]),
            models.Index(fields=["due_date"]),
            models.Index(fields=["assigned_pm"]),
        ]

    def save(self, *args, **kwargs):
        if not self.submittal_id:
            self.submittal_id = generate_submittal_id()
        if self.date_received and not self.due_date:
            self.due_date = add_business_days(self.date_received, 5)
        if self.status == SubmittalStatus.RETURNED and not self.date_returned:
            # Require date_returned; set default to today if not provided
            self.date_returned = self.date_returned or timezone.localdate()
        super().save(*args, **kwargs)

    @property
    def is_overdue(self) -> bool:
        if not self.due_date:
            return False
        if self.status in (SubmittalStatus.RETURNED, SubmittalStatus.VOID):
            return False
        today = timezone.localdate()
        return today > self.due_date


# Create your models here.
