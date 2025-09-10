from __future__ import annotations

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView
from django.views import View
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.http import HttpRequest, HttpResponse

from projects.models import Project
from submittals.models import Submittal, SubmittalStatus
from rfis.models import RFI, RFIStatus
from .forms import ProjectFilterForm, ProjectForm, SubmittalFilterForm, RfiFilterForm, SubmittalForm, RfiForm
from activity.models import ActivityLog
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model


def is_htmx(request: HttpRequest) -> bool:
    return request.headers.get("HX-Request", "false").lower() == "true"


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "ui/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        today = timezone.localdate()
        if user.is_superuser or user.groups.filter(name__in=["admin", "pic"]).exists():
            subs_qs = Submittal.objects.all()
            rfis_qs = RFI.objects.all()
        else:
            subs_qs = Submittal.objects.filter(assigned_pm=user)
            rfis_qs = RFI.objects.filter(assigned_to=user)

        ctx["my_assigned_counts"] = {
            "submittals": subs_qs.count(),
            "rfis": rfis_qs.count(),
        }
        ctx["overdue_submittals"] = subs_qs.filter(due_date__lt=today).exclude(status__in=[SubmittalStatus.RETURNED, SubmittalStatus.VOID]).count()
        ctx["overdue_rfis"] = rfis_qs.filter(due_date__lt=today).exclude(status__in=[RFIStatus.RETURNED, RFIStatus.VOID]).count()
        ctx["by_project"] = list(
            subs_qs.values("project__number", "project__name").annotate(open_count=Count("id")).order_by("-open_count")[:10]
        )
        # Due next 7 days (inclusive)
        from datetime import timedelta
        upcoming = []
        subs_map = {r["due_date"].isoformat(): r["c"] for r in subs_qs.filter(due_date__gte=today, due_date__lte=today+timedelta(days=7)).values("due_date").annotate(c=Count("id"))}
        rfis_map = {r["due_date"].isoformat(): r["c"] for r in rfis_qs.filter(due_date__gte=today, due_date__lte=today+timedelta(days=7)).values("due_date").annotate(c=Count("id"))}
        for i in range(0,8):
            d = (today + timedelta(days=i)).isoformat()
            upcoming.append({"date": d, "submittals": subs_map.get(d, 0), "rfis": rfis_map.get(d, 0)})
        ctx["due_next_7"] = upcoming
        # My overdue lists
        ctx["submittals_overdue"] = list(
            Submittal.objects.filter(assigned_pm=user, due_date__lt=today)
            .exclude(status__in=[SubmittalStatus.RETURNED, SubmittalStatus.VOID])
            .values("id", "project__number", "due_date")
            .order_by("due_date")[:10]
        )
        ctx["rfis_overdue"] = list(
            RFI.objects.filter(assigned_to=user, due_date__lt=today)
            .exclude(status__in=[RFIStatus.RETURNED, RFIStatus.VOID])
            .values("id", "project__number", "due_date")
            .order_by("due_date")[:10]
        )
        return ctx


class ProjectsListView(LoginRequiredMixin, TemplateView):
    template_name = "ui/projects/list.html"
    partial_template_name = "ui/projects/_table.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        user = request.user
        form = ProjectFilterForm(request.GET or None)
        qs = Project.objects.all().prefetch_related("managers", "principals")
        if not (user.is_superuser or user.groups.filter(name__in=["admin", "pic"]).exists()):
            qs = qs.filter(Q(managers=user) | Q(principals=user)).distinct()

        if form.is_valid():
            q = form.cleaned_data.get("q")
            if q:
                qs = qs.filter(Q(number__icontains=q) | Q(name__icontains=q))
            active = form.cleaned_data.get("active")
            if active is not None:
                qs = qs.filter(active=bool(active))
            manager = form.cleaned_data.get("manager")
            if manager:
                qs = qs.filter(managers=manager)
            principal = form.cleaned_data.get("principal")
            if principal:
                qs = qs.filter(principals=principal)

        qs = qs.order_by("number")
        page = int(request.GET.get("page", 1))
        paginator = Paginator(qs, 25)
        page_obj = paginator.get_page(page)
        ctx = {"form": form, "page_obj": page_obj, "paginator": paginator, "object_list": page_obj.object_list}
        if is_htmx(request):
            return render(request, self.partial_template_name, ctx)
        return self.render_to_response(ctx)


class ProjectCreateView(LoginRequiredMixin, View):
    template_name = "ui/projects/create.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        # Only Admin can create projects
        user = request.user
        if not (user.is_superuser or user.groups.filter(name="admin").exists()):
            return HttpResponse("Forbidden", status=403)
        form = ProjectForm()
        return render(request, self.template_name, {"form": form})


class ProjectUpdateView(LoginRequiredMixin, View):
    template_name = "ui/projects/edit.html"

    def get_object(self, pk):
        return get_object_or_404(Project, pk=pk)

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if not (user.is_superuser or user.groups.filter(name="admin").exists()):
            return HttpResponse("Forbidden", status=403)
        return super().dispatch(request, *args, **kwargs)

    def get(self, request: HttpRequest, pk: str) -> HttpResponse:
        project = self.get_object(pk)
        form = ProjectForm(instance=project)
        return render(request, self.template_name, {"form": form, "obj": project})

    def post(self, request: HttpRequest, pk: str) -> HttpResponse:
        project = self.get_object(pk)
        if "archive" in request.POST:
            project.active = False
            project.save(update_fields=["active"])
            return redirect("ui:projects")
        if "unarchive" in request.POST:
            project.active = True
            project.save(update_fields=["active"])
            return redirect("ui:projects")
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            return redirect("ui:projects")
        return render(request, self.template_name, {"form": form, "obj": project})

    def post(self, request: HttpRequest) -> HttpResponse:
        user = request.user
        if not (user.is_superuser or user.groups.filter(name="admin").exists()):
            return HttpResponse("Forbidden", status=403)
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save()
            return redirect("ui:projects")
        return render(request, self.template_name, {"form": form})


class SubmittalsListView(LoginRequiredMixin, TemplateView):
    template_name = "ui/submittals/list.html"
    partial_template_name = "ui/submittals/_table.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        user = request.user
        form = SubmittalFilterForm(request.GET or None)
        qs = Submittal.objects.select_related("project", "assigned_pm").all()
        if not (user.is_superuser or user.groups.filter(name__in=["admin", "pic"]).exists()):
            qs = qs.filter(assigned_pm=user)

        if form.is_valid():
            if form.cleaned_data.get("project"):
                qs = qs.filter(project=form.cleaned_data["project"])
            status = form.cleaned_data.get("status")
            if status:
                qs = qs.filter(status=status)
            if form.cleaned_data.get("assigned_pm"):
                qs = qs.filter(assigned_pm=form.cleaned_data["assigned_pm"])
            if form.cleaned_data.get("originator"):
                qs = qs.filter(originator__icontains=form.cleaned_data["originator"])
            drf = form.cleaned_data.get("date_received_from")
            if drf:
                qs = qs.filter(date_received__gte=drf)
            drt = form.cleaned_data.get("date_received_to")
            if drt:
                qs = qs.filter(date_received__lte=drt)
            df = form.cleaned_data.get("due_from")
            if df:
                qs = qs.filter(due_date__gte=df)
            dt = form.cleaned_data.get("due_to")
            if dt:
                qs = qs.filter(due_date__lte=dt)
            if form.cleaned_data.get("overdue"):
                today = timezone.localdate()
                qs = qs.filter(due_date__lt=today).exclude(status__in=[SubmittalStatus.RETURNED, SubmittalStatus.VOID])

        ordering = request.GET.get("ordering") or "due_date"
        if ordering not in {"due_date", "-due_date", "date_received", "-date_received", "status", "-status"}:
            ordering = "due_date"
        qs = qs.order_by(ordering)

        page = int(request.GET.get("page", 1))
        paginator = Paginator(qs, 25)
        page_obj = paginator.get_page(page)
        User = get_user_model()
        users = User.objects.all().order_by("first_name", "username")
        can_assign = request.user.is_superuser or request.user.groups.filter(name="admin").exists()
        ctx = {
            "form": form,
            "page_obj": page_obj,
            "paginator": paginator,
            "object_list": page_obj.object_list,
            "ordering": ordering,
            "users": users,
            "can_assign": can_assign,
        }
        if is_htmx(request):
            return render(request, self.partial_template_name, ctx)
        return self.render_to_response(ctx)


class RfisListView(LoginRequiredMixin, TemplateView):
    template_name = "ui/rfis/list.html"
    partial_template_name = "ui/rfis/_table.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        user = request.user
        form = RfiFilterForm(request.GET or None)
        qs = RFI.objects.select_related("project", "assigned_to").all()
        if not (user.is_superuser or user.groups.filter(name__in=["admin", "pic"]).exists()):
            qs = qs.filter(assigned_to=user)

        if form.is_valid():
            if form.cleaned_data.get("project"):
                qs = qs.filter(project=form.cleaned_data["project"])
            status = form.cleaned_data.get("status")
            if status:
                qs = qs.filter(status=status)
            if form.cleaned_data.get("assigned_to"):
                qs = qs.filter(assigned_to=form.cleaned_data["assigned_to"])
            if form.cleaned_data.get("rfi_number"):
                qs = qs.filter(rfi_number__icontains=form.cleaned_data["rfi_number"])
            if form.cleaned_data.get("name"):
                qs = qs.filter(name__icontains=form.cleaned_data["name"])
            if form.cleaned_data.get("originator"):
                qs = qs.filter(originator__icontains=form.cleaned_data["originator"])
            if form.cleaned_data.get("q"):
                q = form.cleaned_data["q"]
                from django.db.models import Q
                qs = qs.filter(
                    Q(name__icontains=q)
                    | Q(rfi_number__icontains=q)
                    | Q(originator__icontains=q)
                    | Q(project__number__icontains=q)
                    | Q(project__name__icontains=q)
                )
            drf = form.cleaned_data.get("date_received_from")
            if drf:
                qs = qs.filter(date_received__gte=drf)
            drt = form.cleaned_data.get("date_received_to")
            if drt:
                qs = qs.filter(date_received__lte=drt)
            df = form.cleaned_data.get("due_from")
            if df:
                qs = qs.filter(due_date__gte=df)
            dt = form.cleaned_data.get("due_to")
            if dt:
                qs = qs.filter(due_date__lte=dt)
            if form.cleaned_data.get("overdue"):
                today = timezone.localdate()
                qs = qs.filter(due_date__lt=today).exclude(status__in=[RFIStatus.RETURNED, RFIStatus.VOID])

        ordering = request.GET.get("ordering") or "due_date"
        if ordering not in {"due_date", "-due_date", "date_received", "-date_received", "status", "-status"}:
            ordering = "due_date"
        qs = qs.order_by(ordering)

        page = int(request.GET.get("page", 1))
        paginator = Paginator(qs, 25)
        page_obj = paginator.get_page(page)
        User = get_user_model()
        users = User.objects.all().order_by("first_name", "username")
        can_assign = request.user.is_superuser or request.user.groups.filter(name="admin").exists()
        ctx = {
            "form": form,
            "page_obj": page_obj,
            "paginator": paginator,
            "object_list": page_obj.object_list,
            "ordering": ordering,
            "users": users,
            "can_assign": can_assign,
        }
        if is_htmx(request):
            return render(request, self.partial_template_name, ctx)
        return self.render_to_response(ctx)


class SubmittalCreateView(LoginRequiredMixin, View):
    template_name = "ui/submittals/create.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        project_id = request.GET.get("project") or None
        project = None
        if project_id:
            try:
                project = Project.objects.get(pk=project_id)
            except Project.DoesNotExist:
                project = None
        form = SubmittalForm(project=project)
        return render(request, self.template_name, {"form": form})

    def post(self, request: HttpRequest) -> HttpResponse:
        user = request.user
        # Only Admin or PM can create
        if not (user.is_superuser or user.groups.filter(name__in=["admin", "pm"]).exists()):
            return HttpResponse("Forbidden", status=403)
        project = None
        try:
            if request.POST.get("project"):
                project = Project.objects.get(pk=request.POST.get("project"))
        except Project.DoesNotExist:
            project = None
        form = SubmittalForm(request.POST, project=project)
        if form.is_valid():
            sub = form.save(commit=False)
            sub.status = SubmittalStatus.IN_REVIEW
            sub.save()
            form.save_m2m() if hasattr(form, 'save_m2m') else None
            return redirect("ui:submittal-detail", pk=sub.id)
        return render(request, self.template_name, {"form": form})


class RfiCreateView(LoginRequiredMixin, View):
    template_name = "ui/rfis/create.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        project = None
        pid = request.GET.get("project")
        if pid:
            try:
                project = Project.objects.get(pk=pid)
            except Project.DoesNotExist:
                project = None
        form = RfiForm(project=project)
        return render(request, self.template_name, {"form": form})

    def post(self, request: HttpRequest) -> HttpResponse:
        user = request.user
        if not (user.is_superuser or user.groups.filter(name__in=["admin", "pm", "pic"]).exists()):
            return HttpResponse("Forbidden", status=403)
        project = None
        try:
            if request.POST.get("project"):
                project = Project.objects.get(pk=request.POST.get("project"))
        except Project.DoesNotExist:
            project = None
        form = RfiForm(request.POST, project=project)
        if form.is_valid():
            rfi = form.save()
            return redirect("ui:rfi-detail", pk=rfi.id)
        return render(request, self.template_name, {"form": form})


class SubmittalAssignedPmPartial(LoginRequiredMixin, View):
    def get(self, request: HttpRequest) -> HttpResponse:
        project_id = request.GET.get("project")
        project = None
        if project_id:
            try:
                project = Project.objects.get(pk=project_id)
            except Project.DoesNotExist:
                project = None
        form = SubmittalForm(project=project)
        return render(request, "ui/submittals/_assigned_pm_field.html", {"form": form, "project": project})


class RfiAssignedToPartial(LoginRequiredMixin, View):
    def get(self, request: HttpRequest) -> HttpResponse:
        project_id = request.GET.get("project")
        project = None
        if project_id:
            try:
                project = Project.objects.get(pk=project_id)
            except Project.DoesNotExist:
                project = None
        form = RfiForm(project=project)
        return render(request, "ui/rfis/_assigned_to_field.html", {"form": form, "project": project})


class SubmittalDetailView(LoginRequiredMixin, TemplateView):
    template_name = "ui/submittals/detail.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        sub = get_object_or_404(Submittal.objects.select_related("project", "assigned_pm"), pk=kwargs.get("pk"))
        # Scope: PM must be assigned; PIC/Admin see all
        user = self.request.user
        if not (user.is_superuser or user.groups.filter(name__in=["admin", "pic"]).exists() or sub.assigned_pm_id == user.id):
            from django.http import Http404
            raise Http404
        ctx["obj"] = sub
        ctx["can_edit_submittal"] = bool(
            user.is_superuser or user.groups.filter(name="admin").exists() or sub.assigned_pm_id == user.id
        )
        ctx["activity"] = ActivityLog.objects.filter(
            target_content_type=ContentType.objects.get_for_model(Submittal),
            target_object_id=str(sub.id),
        ).order_by("-created_at")[:50]
        # External folder paths (Windows network drive P:) — not stored in app
        proj_num = sub.project.number
        # Display strings
        ctx["ext_submittals_path"] = fr"P:\\{proj_num}\\Construction Admin\\Submittals"
        ctx["ext_rfis_path"] = fr"P:\\{proj_num}\\Construction Admin\\RFI's"
        # File URLs (attempt to allow clicking in intranet browsers)
        from urllib.parse import quote
        base = f"file:///P:/{quote(proj_num)}"
        ctx["ext_submittals_url"] = base + "/" + quote("Construction Admin") + "/" + quote("Submittals")
        ctx["ext_rfis_url"] = base + "/" + quote("Construction Admin") + "/" + quote("RFI's")
        return ctx


class SubmittalTransitionView(LoginRequiredMixin, View):
    template_name = "ui/submittals/_status_block.html"

    def post(self, request: HttpRequest, pk: str) -> HttpResponse:
        sub = get_object_or_404(Submittal, pk=pk)
        user = request.user
        to_status = request.POST.get("to_status")
        notes = request.POST.get("notes", "")
        date_returned_str = request.POST.get("date_returned")

        # Guards mirror API
        def in_group(name: str) -> bool:
            return user.is_superuser or user.groups.filter(name=name).exists()

        allowed = False
        if to_status == SubmittalStatus.READY_PIC_REVIEW:
            allowed = in_group("admin") or (in_group("pm") and sub.assigned_pm_id == user.id)
        elif to_status == SubmittalStatus.READY_TO_RETURN:
            allowed = in_group("admin") or in_group("pic")
        elif to_status == SubmittalStatus.RETURNED:
            allowed = in_group("admin")
        elif to_status == SubmittalStatus.VOID:
            allowed = in_group("admin")
        elif to_status == SubmittalStatus.IN_REVIEW:
            allowed = in_group("admin") or (in_group("pm") and sub.assigned_pm_id == user.id)

        if not allowed:
            return HttpResponse("Forbidden", status=403)

        sub.status = to_status
        if to_status == SubmittalStatus.RETURNED:
            from django.utils import timezone
            from datetime import date
            try:
                if date_returned_str:
                    sub.date_returned = date.fromisoformat(date_returned_str)
                else:
                    sub.date_returned = timezone.localdate()
            except Exception:
                sub.date_returned = timezone.localdate()
        sub.save()

        ActivityLog.objects.create(
            actor=user,
            action="STATUS_CHANGE",
            target_content_type=ContentType.objects.get_for_model(Submittal),
            target_object_id=str(sub.id),
            from_status=request.POST.get("from_status", ""),
            to_status=to_status,
            notes=notes,
        )

        # Render a small block to replace status area
        return render(request, self.template_name, {"obj": sub})


class RfiDetailView(LoginRequiredMixin, TemplateView):
    template_name = "ui/rfis/detail.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        rfi = get_object_or_404(RFI.objects.select_related("project", "assigned_to"), pk=kwargs.get("pk"))
        user = self.request.user
        if not (user.is_superuser or user.groups.filter(name__in=["admin", "pic"]).exists() or rfi.assigned_to_id == user.id):
            from django.http import Http404
            raise Http404
        ctx["obj"] = rfi
        ctx["can_edit_rfi"] = bool(
            user.is_superuser or user.groups.filter(name="admin").exists() or rfi.assigned_to_id == user.id
        )
        from activity.models import ActivityLog
        from django.contrib.contenttypes.models import ContentType
        ctx["activity"] = ActivityLog.objects.filter(
            target_content_type=ContentType.objects.get_for_model(RFI),
            target_object_id=str(rfi.id),
        ).order_by("-created_at")[:50]
        return ctx


class RfiTransitionView(LoginRequiredMixin, View):
    template_name = "ui/rfis/_status_block.html"

    def post(self, request: HttpRequest, pk: str) -> HttpResponse:
        rfi = get_object_or_404(RFI, pk=pk)
        user = request.user
        to_status = request.POST.get("to_status")

        if to_status not in RFIStatus.values:
            return HttpResponse("Bad Request", status=400)
        if not (
            user.is_superuser
            or user.groups.filter(name__in=["admin", "pic"]).exists()
            or rfi.assigned_to_id == user.id
        ):
            return HttpResponse("Forbidden", status=403)
        rfi.status = to_status
        if to_status == RFIStatus.CLOSED and not rfi.date_responded:
            rfi.date_responded = timezone.localdate()
        rfi.save()
        return render(request, self.template_name, {"obj": rfi})


class RfiUpdateView(LoginRequiredMixin, View):
    template_name = "ui/rfis/edit.html"

    def get_object(self, pk):
        return get_object_or_404(RFI, pk=pk)

    def has_perm(self, user, obj) -> bool:
        return bool(user.is_superuser or user.groups.filter(name="admin").exists() or obj.assigned_to_id == user.id)

    def get(self, request: HttpRequest, pk: str) -> HttpResponse:
        obj = self.get_object(pk)
        if not self.has_perm(request.user, obj):
            return HttpResponse("Forbidden", status=403)
        form = RfiForm(instance=obj)
        return render(request, self.template_name, {"form": form, "obj": obj})

    def post(self, request: HttpRequest, pk: str) -> HttpResponse:
        obj = self.get_object(pk)
        if not self.has_perm(request.user, obj):
            return HttpResponse("Forbidden", status=403)
        form = RfiForm(request.POST, instance=obj)
        if form.is_valid():
            if "recalc_due" in request.POST and form.cleaned_data.get("date_received"):
                from catrack.business_days import add_business_days
                obj = form.save(commit=False)
                obj.due_date = add_business_days(obj.date_received, 5)
                obj.save()
            else:
                form.save()
            return redirect("ui:rfi-detail", pk=obj.id)
        return render(request, self.template_name, {"form": form, "obj": obj})


def _render_submittal_row(request, obj: Submittal):
    User = get_user_model()
    users = User.objects.all().order_by("first_name", "username")
    can_assign = request.user.is_superuser or request.user.groups.filter(name="admin").exists()
    ordering = request.GET.get("ordering", "due_date")
    return render(request, "ui/submittals/_row.html", {"s": obj, "users": users, "can_assign": can_assign, "ordering": ordering})


class SubmittalInlineStatusView(LoginRequiredMixin, View):
    def post(self, request: HttpRequest, pk: str) -> HttpResponse:
        sub = get_object_or_404(Submittal, pk=pk)
        user = request.user
        to_status = request.POST.get("to_status")
        notes = request.POST.get("notes", "")
        date_returned_str = request.POST.get("date_returned")

        if to_status not in SubmittalStatus.values:
            return HttpResponse("Bad Request", status=400)

        def in_group(name: str) -> bool:
            return user.is_superuser or user.groups.filter(name=name).exists()

        allowed = False
        if to_status == SubmittalStatus.READY_PIC_REVIEW:
            allowed = in_group("admin") or (in_group("pm") and sub.assigned_pm_id == user.id)
        elif to_status == SubmittalStatus.READY_TO_RETURN:
            allowed = in_group("admin") or in_group("pic")
        elif to_status == SubmittalStatus.RETURNED:
            allowed = in_group("admin")
        elif to_status == SubmittalStatus.VOID:
            allowed = in_group("admin")
        elif to_status == SubmittalStatus.IN_REVIEW:
            allowed = in_group("admin") or (in_group("pm") and sub.assigned_pm_id == user.id)

        if not allowed:
            return HttpResponse("Forbidden", status=403)

        from_status = sub.status
        sub.status = to_status
        if to_status == SubmittalStatus.RETURNED:
            from django.utils import timezone
            from datetime import date
            try:
                if date_returned_str:
                    sub.date_returned = date.fromisoformat(date_returned_str)
                else:
                    sub.date_returned = timezone.localdate()
            except Exception:
                sub.date_returned = timezone.localdate()
        sub.save()

        ActivityLog.objects.create(
            actor=user,
            action="STATUS_CHANGE",
            target_content_type=ContentType.objects.get_for_model(Submittal),
            target_object_id=str(sub.id),
            from_status=from_status,
            to_status=to_status,
            notes=notes,
        )

        return _render_submittal_row(request, sub)


class SubmittalInlineNameView(LoginRequiredMixin, View):
    def post(self, request: HttpRequest, pk: str) -> HttpResponse:
        sub = get_object_or_404(Submittal, pk=pk)
        user = request.user
        if not (user.is_superuser or user.groups.filter(name__in=["admin", "pm"]).exists() or sub.assigned_pm_id == user.id):
            return HttpResponse("Forbidden", status=403)
        new_val = (request.POST.get("name") or "").strip()
        old_val = sub.name
        sub.name = new_val
        sub.save(update_fields=["name"])
        ActivityLog.objects.create(
            actor=user,
            action="FIELD_EDIT",
            target_content_type=ContentType.objects.get_for_model(Submittal),
            target_object_id=str(sub.id),
            notes=f"name: {old_val} -> {new_val}",
        )
        return _render_submittal_row(request, sub)


class SubmittalInlineOriginatorView(LoginRequiredMixin, View):
    def post(self, request: HttpRequest, pk: str) -> HttpResponse:
        sub = get_object_or_404(Submittal, pk=pk)
        user = request.user
        if not (user.is_superuser or user.groups.filter(name__in=["admin", "pm"]).exists() or sub.assigned_pm_id == user.id):
            return HttpResponse("Forbidden", status=403)
        new_val = (request.POST.get("originator") or "").strip()
        old_val = sub.originator
        sub.originator = new_val
        sub.save(update_fields=["originator"])
        ActivityLog.objects.create(
            actor=user,
            action="FIELD_EDIT",
            target_content_type=ContentType.objects.get_for_model(Submittal),
            target_object_id=str(sub.id),
            notes=f"originator: {old_val} -> {new_val}",
        )
        return _render_submittal_row(request, sub)


class SubmittalInlineSpecView(LoginRequiredMixin, View):
    def post(self, request: HttpRequest, pk: str) -> HttpResponse:
        sub = get_object_or_404(Submittal, pk=pk)
        user = request.user
        if not (user.is_superuser or user.groups.filter(name__in=["admin", "pm"]).exists() or sub.assigned_pm_id == user.id):
            return HttpResponse("Forbidden", status=403)
        new_val = (request.POST.get("spec_section") or "").strip()
        old_val = sub.spec_section
        sub.spec_section = new_val
        sub.save(update_fields=["spec_section"])
        ActivityLog.objects.create(
            actor=user,
            action="FIELD_EDIT",
            target_content_type=ContentType.objects.get_for_model(Submittal),
            target_object_id=str(sub.id),
            notes=f"spec_section: {old_val} -> {new_val}",
        )
        return _render_submittal_row(request, sub)


class SubmittalInlineAssignView(LoginRequiredMixin, View):
    def post(self, request: HttpRequest, pk: str) -> HttpResponse:
        sub = get_object_or_404(Submittal, pk=pk)
        user = request.user
        if not (user.is_superuser or user.groups.filter(name="admin").exists()):
            return HttpResponse("Forbidden", status=403)
        assigned_pm = request.POST.get("assigned_pm")
        if not assigned_pm:
            return HttpResponse("Bad Request", status=400)
        User = get_user_model()
        try:
            new_user = User.objects.get(pk=assigned_pm)
        except User.DoesNotExist:
            return HttpResponse("Bad Request", status=400)
        old = sub.assigned_pm
        sub.assigned_pm = new_user
        sub.save(update_fields=["assigned_pm"])
        # Activity log
        ActivityLog.objects.create(
            actor=user,
            action="ASSIGNMENT_CHANGE",
            target_content_type=ContentType.objects.get_for_model(Submittal),
            target_object_id=str(sub.id),
            notes=f"assigned_pm: {getattr(old,'username',old)} -> {new_user.username}",
        )
        return _render_submittal_row(request, sub)


def _render_rfi_row(request, obj: RFI):
    User = get_user_model()
    users = User.objects.all().order_by("first_name", "username")
    can_assign = request.user.is_superuser or request.user.groups.filter(name="admin").exists()
    ordering = request.GET.get("ordering", "due_date")
    return render(request, "ui/rfis/_row.html", {"r": obj, "users": users, "can_assign": can_assign, "ordering": ordering})


class RfiInlineStatusView(LoginRequiredMixin, View):
    def post(self, request: HttpRequest, pk: str) -> HttpResponse:
        rfi = get_object_or_404(RFI, pk=pk)
        user = request.user
        to_status = request.POST.get("to_status")
        date_returned_str = request.POST.get("date_returned")
        if to_status not in RFIStatus.values:
            return HttpResponse("Bad Request", status=400)
        if not (
            user.is_superuser
            or user.groups.filter(name__in=["admin", "pic"]).exists()
            or rfi.assigned_to_id == user.id
        ):
            return HttpResponse("Forbidden", status=403)
        from_status = rfi.status
        rfi.status = to_status
        if to_status == RFIStatus.RETURNED:
            from datetime import date
            try:
                if date_returned_str:
                    rfi.date_responded = date.fromisoformat(date_returned_str)
                else:
                    rfi.date_responded = timezone.localdate()
            except Exception:
                rfi.date_responded = timezone.localdate()
        rfi.save()
        ActivityLog.objects.create(
            actor=user,
            action="STATUS_CHANGE",
            target_content_type=ContentType.objects.get_for_model(RFI),
            target_object_id=str(rfi.id),
            from_status=from_status,
            to_status=to_status,
            notes=request.POST.get("notes", ""),
        )
        return _render_rfi_row(request, rfi)


class RfiInlineAssignView(LoginRequiredMixin, View):
    def post(self, request: HttpRequest, pk: str) -> HttpResponse:
        rfi = get_object_or_404(RFI, pk=pk)
        user = request.user
        if not (user.is_superuser or user.groups.filter(name="admin").exists()):
            return HttpResponse("Forbidden", status=403)
        assigned_to = request.POST.get("assigned_to")
        if not assigned_to:
            return HttpResponse("Bad Request", status=400)
        User = get_user_model()
        try:
            new_user = User.objects.get(pk=assigned_to)
        except User.DoesNotExist:
            return HttpResponse("Bad Request", status=400)
        old = rfi.assigned_to
        rfi.assigned_to = new_user
        rfi.save(update_fields=["assigned_to"])
        ActivityLog.objects.create(
            actor=user,
            action="ASSIGNMENT_CHANGE",
            target_content_type=ContentType.objects.get_for_model(RFI),
            target_object_id=str(rfi.id),
            notes=f"assigned_to: {getattr(old,'username',old)} -> {new_user.username}",
        )
        return _render_rfi_row(request, rfi)


class RfiInlineNameView(LoginRequiredMixin, View):
    def post(self, request: HttpRequest, pk: str) -> HttpResponse:
        rfi = get_object_or_404(RFI, pk=pk)
        user = request.user
        if not (user.is_superuser or user.groups.filter(name__in=["admin", "pic"]).exists() or rfi.assigned_to_id == user.id):
            return HttpResponse("Forbidden", status=403)
        new_name = (request.POST.get("name") or "").strip()
        old = rfi.name
        rfi.name = new_name
        rfi.save(update_fields=["name"])
        ActivityLog.objects.create(
            actor=user,
            action="FIELD_EDIT",
            target_content_type=ContentType.objects.get_for_model(RFI),
            target_object_id=str(rfi.id),
            notes=f"name: {old} -> {new_name}",
        )
        return _render_rfi_row(request, rfi)


class RfiInlineNumberView(LoginRequiredMixin, View):
    def post(self, request: HttpRequest, pk: str) -> HttpResponse:
        rfi = get_object_or_404(RFI, pk=pk)
        user = request.user
        if not (user.is_superuser or user.groups.filter(name__in=["admin", "pic"]).exists() or rfi.assigned_to_id == user.id):
            return HttpResponse("Forbidden", status=403)
        new_no = (request.POST.get("rfi_number") or "").strip()
        old = rfi.rfi_number
        rfi.rfi_number = new_no
        rfi.save(update_fields=["rfi_number"])
        ActivityLog.objects.create(
            actor=user,
            action="FIELD_EDIT",
            target_content_type=ContentType.objects.get_for_model(RFI),
            target_object_id=str(rfi.id),
            notes=f"rfi_number: {old} -> {new_no}",
        )
        return _render_rfi_row(request, rfi)


class SubmittalUpdateView(LoginRequiredMixin, View):
    template_name = "ui/submittals/edit.html"

    def get_object(self, pk):
        return get_object_or_404(Submittal, pk=pk)

    def has_perm(self, user, obj) -> bool:
        return bool(user.is_superuser or user.groups.filter(name="admin").exists() or obj.assigned_pm_id == user.id)

    def get(self, request: HttpRequest, pk: str) -> HttpResponse:
        obj = self.get_object(pk)
        if not self.has_perm(request.user, obj):
            return HttpResponse("Forbidden", status=403)
        form = SubmittalForm(instance=obj)
        return render(request, self.template_name, {"form": form, "obj": obj})

    def post(self, request: HttpRequest, pk: str) -> HttpResponse:
        obj = self.get_object(pk)
        if not self.has_perm(request.user, obj):
            return HttpResponse("Forbidden", status=403)
        form = SubmittalForm(request.POST, instance=obj)
        if form.is_valid():
            if "recalc_due" in request.POST and form.cleaned_data.get("date_received"):
                from catrack.business_days import add_business_days
                obj = form.save(commit=False)
                obj.due_date = add_business_days(obj.date_received, 5)
                obj.save()
            else:
                form.save()
            return redirect("ui:submittal-detail", pk=obj.id)
        return render(request, self.template_name, {"form": form, "obj": obj})
