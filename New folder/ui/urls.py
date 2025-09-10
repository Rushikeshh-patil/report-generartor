from django.urls import path
from django.contrib.auth import views as auth_views

from .views import (
    DashboardView,
    ProjectsListView,
    ProjectCreateView,
    SubmittalsListView,
    RfisListView,
    SubmittalCreateView,
    RfiCreateView,
    SubmittalDetailView,
    RfiDetailView,
    SubmittalTransitionView,
    RfiTransitionView,
    SubmittalUpdateView,
    SubmittalInlineStatusView,
    SubmittalInlineAssignView,
    RfiInlineStatusView,
    RfiInlineAssignView,
    RfiUpdateView,
    RfiInlineNameView,
    SubmittalAssignedPmPartial,
    RfiAssignedToPartial,
)


app_name = "ui"

urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard"),
    path("projects/", ProjectsListView.as_view(), name="projects"),
    path("projects/new/", ProjectCreateView.as_view(), name="project-create"),
    path("submittals/", SubmittalsListView.as_view(), name="submittals"),
    path("rfis/", RfisListView.as_view(), name="rfis"),
    path("submittals/new/", SubmittalCreateView.as_view(), name="submittal-create"),
    path("rfis/new/", RfiCreateView.as_view(), name="rfi-create"),
    path("submittals/<uuid:pk>/", SubmittalDetailView.as_view(), name="submittal-detail"),
    path("submittals/<uuid:pk>/edit/", SubmittalUpdateView.as_view(), name="submittal-edit"),
    path("rfis/<uuid:pk>/", RfiDetailView.as_view(), name="rfi-detail"),
    path("rfis/<uuid:pk>/edit/", RfiUpdateView.as_view(), name="rfi-edit"),
    path("submittals/<uuid:pk>/transition/", SubmittalTransitionView.as_view(), name="submittal-transition"),
    path("rfis/<uuid:pk>/transition/", RfiTransitionView.as_view(), name="rfi-transition"),
    path("submittals/<uuid:pk>/inline/status/", SubmittalInlineStatusView.as_view(), name="submittal-inline-status"),
    path("submittals/<uuid:pk>/inline/assign/", SubmittalInlineAssignView.as_view(), name="submittal-inline-assign"),
    path("rfis/<uuid:pk>/inline/status/", RfiInlineStatusView.as_view(), name="rfi-inline-status"),
    path("rfis/<uuid:pk>/inline/assign/", RfiInlineAssignView.as_view(), name="rfi-inline-assign"),
    path("submittals/assigned-pm/", SubmittalAssignedPmPartial.as_view(), name="submittal-assigned-pm-partial"),
    path("rfis/assigned-to/", RfiAssignedToPartial.as_view(), name="rfi-assigned-to-partial"),
    path("rfis/<uuid:pk>/inline/name/", RfiInlineNameView.as_view(), name="rfi-inline-name"),
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="/login/"), name="logout"),
]
