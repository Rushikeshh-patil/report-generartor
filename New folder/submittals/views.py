from rest_framework import viewsets, permissions, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend

from accounts.permissions import IsAdminOrAssigned
from .models import Submittal, SubmittalStatus
from .serializers import SubmittalSerializer
from activity.models import ActivityLog
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponse
from django.utils import timezone
import csv


class SubmittalViewSet(viewsets.ModelViewSet):
    queryset = Submittal.objects.select_related("project", "assigned_pm").all()
    serializer_class = SubmittalSerializer
    permission_classes = [IsAuthenticated, IsAdminOrAssigned]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["project", "status", "assigned_pm", "originator"]
    search_fields = ["submittal_id", "spec_section", "description", "originator"]
    ordering_fields = ["due_date", "date_received", "status", "created_at"]
    assigned_user_attr = "assigned_pm"

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if not user.is_authenticated:
            return qs.none()
        if user.is_superuser or user.groups.filter(name__in=["admin", "pic"]).exists():
            base_qs = qs
        else:
            # PMs only see their assigned submittals
            base_qs = qs.filter(assigned_pm=user)
        overdue = self.request.query_params.get("overdue")
        if overdue and overdue.lower() in ("1", "true", "yes"): 
            from django.utils import timezone
            from .models import SubmittalStatus
            today = timezone.localdate()
            base_qs = base_qs.filter(due_date__lt=today).exclude(status__in=[SubmittalStatus.RETURNED, SubmittalStatus.VOID])
        return base_qs

    def create(self, request, *args, **kwargs):
        user = request.user
        if not (user.is_superuser or user.groups.filter(name__in=["admin", "pm"]).exists()):
            raise PermissionDenied("Not allowed to create submittals.")
        return super().create(request, *args, **kwargs)

    def perform_update(self, serializer):
        serializer.save()

    @action(detail=True, methods=["post"], url_path="transition")
    def transition(self, request, pk=None):
        submittal = self.get_object()
        user = request.user
        to_status = request.data.get("to_status")
        notes = request.data.get("notes", "")

        if to_status not in SubmittalStatus.values:
            raise PermissionDenied("Invalid target status")

        from_status = submittal.status

        def in_group(name: str) -> bool:
            return user.is_superuser or user.groups.filter(name=name).exists()

        # Guards per spec
        allowed = False
        if to_status == SubmittalStatus.READY_PIC_REVIEW:
            allowed = in_group("admin") or (in_group("pm") and submittal.assigned_pm_id == user.id)
        elif to_status == SubmittalStatus.READY_TO_RETURN:
            allowed = in_group("admin") or in_group("pic")
        elif to_status == SubmittalStatus.RETURNED:
            allowed = in_group("admin")
        elif to_status == SubmittalStatus.VOID:
            allowed = in_group("admin")
        elif to_status == SubmittalStatus.IN_REVIEW:
            # Allow revert to IN_REVIEW by Admin or assigned PM
            allowed = in_group("admin") or (in_group("pm") and submittal.assigned_pm_id == user.id)

        if not allowed:
            raise PermissionDenied("Not allowed to perform this transition")

        # Apply changes
        update_fields = {"status": to_status}
        if to_status == SubmittalStatus.RETURNED:
            from datetime import date as _date
            date_str = request.data.get("date_returned")
            if date_str:
                try:
                    update_fields["date_returned"] = _date.fromisoformat(date_str)
                except Exception:
                    update_fields["date_returned"] = timezone.localdate()
            else:
                update_fields["date_returned"] = timezone.localdate()
        for k, v in update_fields.items():
            setattr(submittal, k, v)
        submittal.save()

        # Audit log
        ActivityLog.objects.create(
            actor=user,
            action="STATUS_CHANGE",
            target_content_type=ContentType.objects.get_for_model(Submittal),
            target_object_id=str(submittal.id),
            from_status=from_status,
            to_status=to_status,
            notes=notes,
        )

        return Response(SubmittalSerializer(submittal, context=self.get_serializer_context()).data)

    @action(detail=False, methods=["get"], url_path=r"export\.csv")
    def export_csv(self, request):
        qs = self.filter_queryset(self.get_queryset())
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename=submittals.csv"
        writer = csv.writer(response)
        writer.writerow([
            "Submittal ID", "Project", "Spec Section", "Description", "Status", "Assigned PM",
            "Originator", "Date Received", "Date Logged", "Due Date", "Date Returned", "Notes", "Is Overdue",
        ])
        for s in qs.iterator():
            pm_name = getattr(s.assigned_pm, "get_full_name", None)
            if callable(pm_name):
                pm_name = s.assigned_pm.get_full_name() or s.assigned_pm.username
            else:
                pm_name = s.assigned_pm.username
            writer.writerow([
                s.submittal_id,
                f"{s.project.number} — {s.project.name}",
                s.spec_section,
                (s.description or "").replace("\n", " ").strip(),
                s.status,
                pm_name,
                s.originator,
                s.date_received,
                s.date_logged,
                s.due_date,
                s.date_returned or "",
                (s.notes or "").replace("\n", " ").strip(),
                "YES" if s.is_overdue else "NO",
            ])
        return response
