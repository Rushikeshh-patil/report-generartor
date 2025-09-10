from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

from submittals.models import Submittal, SubmittalStatus
from rfis.models import RFI, RFIStatus


class OverviewView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        today = timezone.localdate()

        # Scope: Admin/PIC -> all; PM -> assigned only
        if user.is_superuser or user.groups.filter(name__in=["admin", "pic"]).exists():
            subs_qs = Submittal.objects.all()
            rfis_qs = RFI.objects.all()
        else:
            subs_qs = Submittal.objects.filter(assigned_pm=user)
            rfis_qs = RFI.objects.filter(assigned_to=user)

        my_assigned = {
            "submittals": subs_qs.count(),
            "rfis": rfis_qs.count(),
        }

        overdue_submittals = subs_qs.filter(due_date__lt=today).exclude(status__in=[SubmittalStatus.RETURNED, SubmittalStatus.VOID]).count()
        overdue_rfis = rfis_qs.filter(due_date__lt=today).exclude(status__in=[RFIStatus.RETURNED, RFIStatus.VOID]).count()

        # Basic per-project summary (top 10 by open count)
        from django.db.models import Count
        by_project = list(
            subs_qs.values("project__number", "project__name")
            .annotate(open_count=Count("id"))
            .order_by("-open_count")[:10]
        )

        return Response({
            "my_assigned_counts": my_assigned,
            "overdue_submittals": overdue_submittals,
            "overdue_rfis": overdue_rfis,
            "by_project": by_project,
        })
