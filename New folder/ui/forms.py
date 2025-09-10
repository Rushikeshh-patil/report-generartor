from __future__ import annotations

from django import forms
from django.contrib.auth import get_user_model
from django.db.models import Q

from projects.models import Project
from submittals.models import SubmittalStatus
from rfis.models import RFIStatus
from submittals.models import Submittal
from rfis.models import RFI


User = get_user_model()


class ProjectFilterForm(forms.Form):
    q = forms.CharField(label="Search", required=False)
    active = forms.NullBooleanField(label="Active only", required=False)
    manager = forms.ModelChoiceField(queryset=User.objects.all(), required=False)
    principal = forms.ModelChoiceField(queryset=User.objects.all(), required=False)


class ProjectForm(forms.ModelForm):
    managers = forms.ModelMultipleChoiceField(queryset=User.objects.all(), required=False)
    principals = forms.ModelMultipleChoiceField(queryset=User.objects.all(), required=False)

    class Meta:
        model = Project
        fields = ["number", "name", "managers", "principals", "active"]


class SubmittalFilterForm(forms.Form):
    project = forms.ModelChoiceField(queryset=Project.objects.all(), required=False)
    status = forms.ChoiceField(choices=[("", "All")] + list(SubmittalStatus.choices), required=False)
    assigned_pm = forms.ModelChoiceField(queryset=User.objects.all(), required=False)
    originator = forms.CharField(required=False)
    date_received_from = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    date_received_to = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    due_from = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    due_to = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    overdue = forms.BooleanField(required=False)


class RfiFilterForm(forms.Form):
    project = forms.ModelChoiceField(queryset=Project.objects.all(), required=False)
    status = forms.ChoiceField(choices=[("", "All")] + list(RFIStatus.choices), required=False)
    assigned_to = forms.ModelChoiceField(queryset=User.objects.all(), required=False)
    rfi_number = forms.CharField(required=False, label="RFI No")
    name = forms.CharField(required=False)
    q = forms.CharField(required=False, label="Search")
    originator = forms.CharField(required=False)
    date_received_from = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    date_received_to = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    due_from = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    due_to = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    overdue = forms.BooleanField(required=False)


class SubmittalForm(forms.ModelForm):
    def __init__(self, *args, project=None, **kwargs):
        super().__init__(*args, **kwargs)
        if project is not None:
            managers_qs = project.managers.all()
            self.fields["assigned_pm"].queryset = managers_qs
            if managers_qs.count() == 1 and not self.initial.get("assigned_pm") and not self.data.get("assigned_pm"):
                self.fields["assigned_pm"].initial = managers_qs.first().pk

    class Meta:
        model = Submittal
        fields = [
            "project",
            "name",
            "spec_section",
            "description",
            "assigned_pm",
            "originator",
            "date_received",
            "date_logged",
            "notes",
        ]
        widgets = {
            "date_received": forms.DateInput(attrs={"type": "date"}),
            "date_logged": forms.DateInput(attrs={"type": "date"}),
            "name": forms.TextInput(),
            "description": forms.Textarea(attrs={"rows": 3}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }


class RfiForm(forms.ModelForm):
    def __init__(self, *args, project=None, **kwargs):
        super().__init__(*args, **kwargs)
        if project is not None:
            # Union of project managers and principals
            users_qs = get_user_model().objects.filter(
                Q(managed_projects=project) | Q(principal_projects=project)
            ).distinct()
            self.fields["assigned_to"].queryset = users_qs
            if users_qs.count() == 1 and not self.initial.get("assigned_to") and not self.data.get("assigned_to"):
                self.fields["assigned_to"].initial = users_qs.first().pk

    class Meta:
        model = RFI
        fields = [
            "project",
            "rfi_number",
            "assigned_to",
            "originator",
            "date_received",
            "name",
        ]
        widgets = {
            "date_received": forms.DateInput(attrs={"type": "date"}),
            "name": forms.TextInput(),
        }
