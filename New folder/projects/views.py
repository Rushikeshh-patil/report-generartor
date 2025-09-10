from rest_framework import viewsets, permissions, filters
from django.db.models import Q
from django.contrib.auth import get_user_model

from accounts.permissions import IsAdminOrReadOnly
from .models import Project
from .serializers import ProjectSerializer


User = get_user_model()


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all().prefetch_related("managers", "principals")
    serializer_class = ProjectSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["number", "name"]
    ordering_fields = ["number", "name", "created_at", "updated_at"]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if not user.is_authenticated:
            return qs.none()
        if user.is_superuser or user.groups.filter(name__in=["admin", "pic"]).exists():
            return qs
        # PMs: show only projects where they are manager or principal
        return qs.filter(Q(managers=user) | Q(principals=user)).distinct()

