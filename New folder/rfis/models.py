import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

from catrack.business_days import add_business_days
from projects.models import Project

User = get_user_model()


class RFIStatus(models.TextChoices):
    IN_REVIEW = "IN_REVIEW", "In Review"
    READY_PIC_REVIEW = "READY_PIC_REVIEW", "Ready for PIC Review"
    READY_TO_RETURN = "READY_TO_RETURN", "Ready to Return"
    RETURNED = "RETURNED", "Returned"
    VOID = "VOID", "Void"


def generate_rfi_id() -> str:
    ts = timezone.now().strftime("%Y%m%d%H%M%S")
    return f"RFI-{ts}-{str(uuid.uuid4())[:8]}"


class RFI(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rfi_id = models.CharField(max_length=40, unique=True, blank=True)
    rfi_number = models.CharField(max_length=50, blank=True, default="")
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="rfis")
    assigned_to = models.ForeignKey(User, on_delete=models.PROTECT, related_name="assigned_rfis")
    originator = models.CharField(max_length=120)
    date_received = models.DateField()
    due_date = models.DateField(blank=True, null=True)
    date_responded = models.DateField(blank=True, null=True)
    name = models.CharField(max_length=200, blank=True, default="")
    status = models.CharField(max_length=20, choices=RFIStatus.choices, default=RFIStatus.IN_REVIEW)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["due_date", "date_received"]
        indexes = [
            models.Index(fields=["project", "status"]),
            models.Index(fields=["due_date"]),
            models.Index(fields=["assigned_to"]),
            models.Index(fields=["rfi_number"]),
        ]

    def save(self, *args, **kwargs):
        if not self.rfi_id:
            self.rfi_id = generate_rfi_id()
        if self.date_received and not self.due_date:
            self.due_date = add_business_days(self.date_received, 5)
        super().save(*args, **kwargs)

    @property
    def is_overdue(self) -> bool:
        if not self.due_date:
            return False
        if self.status in (RFIStatus.RETURNED, RFIStatus.VOID):
            return False
        today = timezone.localdate()
        return today > self.due_date


# Create your models here.
