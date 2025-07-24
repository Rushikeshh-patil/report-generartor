# todo/urls.py

from django.urls import path
from . import views
from .views import ProjectCreateView, TaskCreateView

urlpatterns = [
    path('', views.TaskListView.as_view(), name='task_list'),
    path('register/', views.register, name='register'),
    path('project/new/', ProjectCreateView.as_view(), name='project_create'),
    path('task/new/', TaskCreateView.as_view(), name='task_create'),

    path('project/<int:pk>/', views.ProjectDetailView.as_view(), name='project_detail'),

    path('project/<int:pk>/', views.ProjectDetailView.as_view(), name='project_detail'),
    path('task/<int:pk>/update_status/', views.update_task_status, name='update_task_status'),
    path('dashboard/performance/', views.PerformanceDashboardView.as_view(), name='performance_dashboard'),
    path('task/<int:task_pk>/add_subtask/', views.add_subtask, name='add_subtask'),

    path('task/<int:pk>/edit/', views.TaskUpdateView.as_view(), name='task_edit'),
    path('task/<int:pk>/delete/', views.TaskDeleteView.as_view(), name='task_delete'),
]