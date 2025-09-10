from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import Submittal, SubmittalStatus
from projects.models import Project


User = get_user_model()


class SubmittalSerializer(serializers.ModelSerializer):
    is_overdue = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Submittal
        fields = [
            "id",
            "submittal_id",
            "name",
            "project",
            "spec_section",
            "description",
            "status",
            "assigned_pm",
            "originator",
            "date_received",
            "date_logged",
            "due_date",
            "date_returned",
            "notes",
            "created_at",
            "updated_at",
            "is_overdue",
        ]
        read_only_fields = [
            "id",
            "submittal_id",
            "status",
            "created_at",
            "updated_at",
            "is_overdue",
        ]

    def get_is_overdue(self, obj: Submittal) -> bool:
        return obj.is_overdue

    def validate(self, attrs):
        return attrs
