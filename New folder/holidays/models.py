import uuid
from django.db import models


class Holiday(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date = models.DateField(unique=True)
    name = models.CharField(max_length=120)
    is_business_day = models.BooleanField(default=False)

    class Meta:
        ordering = ["date"]

    def __str__(self) -> str:
        return f"{self.date} — {self.name}"


# Create your models here.
