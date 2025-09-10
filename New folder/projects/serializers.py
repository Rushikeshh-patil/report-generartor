from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Project


User = get_user_model()


class ProjectSerializer(serializers.ModelSerializer):
    managers = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=True, required=False)
    principals = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=True, required=False)

    class Meta:
        model = Project
        fields = [
            "id",
            "number",
            "name",
            "managers",
            "principals",
            "active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

