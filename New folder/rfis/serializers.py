from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import RFI, RFIStatus
from projects.models import Project


User = get_user_model()


class RFISerializer(serializers.ModelSerializer):
    is_overdue = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = RFI
        fields = [
            "id",
            "rfi_id",
            "rfi_number",
            "project",
            "assigned_to",
            "originator",
            "date_received",
            "due_date",
            "date_responded",
            "name",
            "status",
            "created_at",
            "updated_at",
            "is_overdue",
        ]
        read_only_fields = [
            "id",
            "rfi_id",
            "created_at",
            "updated_at",
            "is_overdue",
        ]

    def get_is_overdue(self, obj: RFI) -> bool:
        return obj.is_overdue
