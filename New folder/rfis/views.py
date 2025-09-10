from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from accounts.permissions import IsAdminOrAssigned
from .models import RFI, RFIStatus
from .serializers import RFISerializer
from django.http import HttpResponse
from activity.models import ActivityLog
from django.contrib.contenttypes.models import ContentType
import csv


class RFIViewSet(viewsets.ModelViewSet):
    queryset = RFI.objects.select_related("project", "assigned_to").all()
    serializer_class = RFISerializer
    permission_classes = [IsAuthenticated, IsAdminOrAssigned]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["project", "status", "assigned_to", "originator"]
    search_fields = ["rfi_id", "originator", "name"]
    ordering_fields = ["due_date", "date_received", "status", "created_at"]
    assigned_user_attr = "assigned_to"

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if not user.is_authenticated:
            return qs.none()
        if user.is_superuser or user.groups.filter(name__in=["admin", "pic"]).exists():
            base_qs = qs
        else:
            # PMs: only their assigned RFIs
            base_qs = qs.filter(assigned_to=user)
        overdue = self.request.query_params.get("overdue")
        if overdue and overdue.lower() in ("1", "true", "yes"):
            from django.utils import timezone
            today = timezone.localdate()
            base_qs = base_qs.filter(due_date__lt=today).exclude(status__in=[RFIStatus.RETURNED, RFIStatus.VOID])
        return base_qs

    def create(self, request, *args, **kwargs):
        user = request.user
        if not (user.is_superuser or user.groups.filter(name__in=["admin", "pm", "pic"]).exists()):
            raise PermissionDenied("Not allowed to create RFIs.")
        return super().create(request, *args, **kwargs)

    @action(detail=True, methods=["post"], url_path="transition")
    def transition(self, request, pk=None):
        rfi = self.get_object()
        user = request.user
        to_status = request.data.get("to_status")
        if to_status not in RFIStatus.values:
            return Response({"detail": "Invalid target status"}, status=400)
        # Admin always allowed; assigned user allowed; PIC allowed if in group
        if not (
            user.is_superuser
            or user.groups.filter(name__in=["admin", "pic"]).exists()
            or rfi.assigned_to_id == user.id
        ):
            raise PermissionDenied("Not allowed to transition this RFI.")
        from_status = rfi.status
        rfi.status = to_status
        if to_status == RFIStatus.RETURNED:
            from django.utils import timezone
            from datetime import date as _date
            date_str = request.data.get("date_returned") or request.data.get("date_responded")
            if date_str:
                try:
                    rfi.date_responded = _date.fromisoformat(date_str)
                except Exception:
                    rfi.date_responded = timezone.localdate()
            elif not rfi.date_responded:
                rfi.date_responded = timezone.localdate()
        rfi.save()
        # Audit log
        ActivityLog.objects.create(
            actor=user,
            action="STATUS_CHANGE",
            target_content_type=ContentType.objects.get_for_model(RFI),
            target_object_id=str(rfi.id),
            from_status=from_status,
            to_status=to_status,
            notes=request.data.get("notes", ""),
        )
        return Response(RFISerializer(rfi, context=self.get_serializer_context()).data)

    @action(detail=False, methods=["get"], url_path=r"export\.csv")
    def export_csv(self, request):
        qs = self.filter_queryset(self.get_queryset())
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename=rfis.csv"
        writer = csv.writer(response)
        writer.writerow([
            "RFI No", "RFI ID", "Project", "Assigned To", "Originator", "Date Received", "Due Date", "Returned Date",
            "Name", "Status", "Is Overdue",
        ])
        for r in qs.iterator():
            assignee = getattr(r.assigned_to, "get_full_name", None)
            if callable(assignee):
                assignee = r.assigned_to.get_full_name() or r.assigned_to.username
            else:
                assignee = r.assigned_to.username
            project_label = f"{r.project.number} - {r.project.name}"
            writer.writerow([
                r.rfi_number or "",
                r.rfi_id,
                project_label,
                assignee,
                r.originator,
                r.date_received,
                r.due_date,
                r.date_responded or "",
                (getattr(r, 'name', '') or "").replace("\n", " ").strip(),
                r.status,
                "YES" if r.is_overdue else "NO",
            ])
        return response
