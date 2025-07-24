# todo/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from .models import Task, Project # Make sure to import your models
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView
from .forms import ProjectForm, TaskForm, SubTaskForm
from django.views.generic.edit import CreateView
from django.urls import reverse_lazy
from django.db.models import Avg
from .models import Task, Project, User
from django.utils import timezone
from django.db.models import Count
import json
from datetime import datetime


from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, UpdateView, DeleteView # Add UpdateView and DeleteView
from django.db.models import Q # Import Q for complex lookups

# ... (keep all your existing views) ...

class TaskUpdateView(LoginRequiredMixin, UpdateView):
    """
    View to edit an existing task.
    """
    model = Task
    form_class = TaskForm
    template_name = 'todo/task_form.html' # We can reuse the same form template

    def get_form_kwargs(self):
        # Pass the current user to the form
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_queryset(self):
        # Users can only edit tasks if they are the assignee OR the project owner
        return Task.objects.filter(Q(assignee=self.request.user) | Q(project__owner=self.request.user))

    def get_success_url(self):
        # After editing, return to the project detail page
        return reverse_lazy('project_detail', kwargs={'pk': self.object.project.pk})

class TaskDeleteView(LoginRequiredMixin, DeleteView):
    """
    View to delete an existing task.
    """
    model = Task
    template_name = 'todo/task_confirm_delete.html'
    context_object_name = 'task'

    def get_queryset(self):
         # Users can only delete tasks if they are the assignee OR the project owner
        return Task.objects.filter(Q(assignee=self.request.user) | Q(project__owner=self.request.user))
    
    def get_success_url(self):
        # After deleting, return to the project detail page
        return reverse_lazy('project_detail', kwargs={'pk': self.object.project.pk})

class TaskListView(ListView):
    model = Project
    template_name = 'todo/task_list.html'
    context_object_name = 'projects'

    def get_queryset(self):
        # Get projects where the current user is a member, and prefetch related tasks
        return Project.objects.filter(members=self.request.user).prefetch_related('tasks')

class ProjectDetailView(LoginRequiredMixin, DetailView):
    model = Project
    template_name = 'todo/project_detail.html'
    context_object_name = 'project'

    def get_queryset(self):
        """
        Allow access if the user is a staff member OR a member of the project.
        """
        user = self.request.user
        if user.is_staff:
            return Project.objects.all()
        else:
            return Project.objects.filter(members=user)

    def get_context_data(self, **kwargs):
        """
        Adds separate lists for active and completed tasks to the context.
        """
        context = super().get_context_data(**kwargs)
        project = self.get_object()
        
        # Get all tasks and split them by status
        all_tasks = project.tasks.all().order_by('created_at')
        context['active_tasks'] = [task for task in all_tasks if task.status != 'done']
        context['completed_tasks'] = [task for task in all_tasks if task.status == 'done']
        
        return context



def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('task_list') # Redirect to the main task list after registration
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

class TaskListView(LoginRequiredMixin, ListView): # Add LoginRequiredMixin
    model = Task
    template_name = 'todo/task_list.html'
    context_object_name = 'tasks'

    def get_queryset(self):
        # Filter tasks to show only those assigned to the current user
        return Task.objects.filter(assignee=self.request.user).order_by('status', '-created_at')

    def get_context_data(self, **kwargs):
        # Add the user's projects to the context for easy access in the template
        context = super().get_context_data(**kwargs)
        context['projects'] = Project.objects.filter(members=self.request.user)
        return context
    

class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = 'todo/project_form.html'
    success_url = reverse_lazy('task_list')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)

class TaskCreateView(LoginRequiredMixin, CreateView):
    model = Task
    form_class = TaskForm
    template_name = 'todo/task_form.html'
    success_url = reverse_lazy('task_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
def update_task_status(request, pk):
    task = get_object_or_404(Task, pk=pk)
    
    # Ensure the user has permission to update this task
    if task.assignee != request.user and task.project.owner != request.user:
        return redirect('task_list') # Or show an error

    new_status = request.POST.get('status')
    if new_status in ['todo', 'inprogress', 'done']:
        task.status = new_status
        if new_status == 'inprogress' and not task.started_at:
            task.started_at = timezone.now()
        elif new_status == 'done':
            task.completed_at = timezone.now()
        task.save()
        
    # Redirect back to the project detail page
    return redirect('project_detail', pk=task.project.pk)

class PerformanceDashboardView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = User
    template_name = 'todo/performance_dashboard.html'
    context_object_name = 'non_staff_users' # Changed for clarity

    def test_func(self):
        return self.request.user.is_staff

    def get_queryset(self):
        # We only need the list of non-staff users for the dropdown
        return User.objects.filter(is_staff=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get filter parameters from the URL
        selected_user_id = self.request.GET.get('user')
        start_date_str = self.request.GET.get('start_date')
        end_date_str = self.request.GET.get('end_date')

        chart_data = None
        selected_user = None

        if selected_user_id:
            try:
                # Prepare filters
                selected_user = User.objects.get(pk=selected_user_id)
                date_filter = Q()
                if start_date_str:
                    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                    date_filter &= Q(created_at__gte=start_date)
                if end_date_str:
                    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                    # Add 1 day to end_date to make the range inclusive
                    end_date_inclusive = end_date + timezone.timedelta(days=1)
                    date_filter &= Q(created_at__lt=end_date_inclusive)

                # --- Query data with date filters ---
                # Task Status Pie Chart
                status_distribution = (
                    Task.objects.filter(assignee=selected_user)
                    .filter(date_filter) # Apply date filter
                    .values('status')
                    .annotate(count=Count('status'))
                )
                
                # Effort Variance Bar Chart
                completed_tasks = Task.objects.filter(
                    assignee=selected_user, status='done', actual_hours__isnull=False
                ).filter(date_filter) # Apply date filter

                chart_data = {
                    'username': selected_user.username,
                    'status_data': {item['status']: item['count'] for item in status_distribution},
                    'effort_data': {
                        'labels': [task.title for task in completed_tasks],
                        'estimated': [float(task.estimated_hours) for task in completed_tasks],
                        'actual': [float(task.actual_hours) for task in completed_tasks],
                    },
                }

            except User.DoesNotExist:
                chart_data = None

        # Pass data and current filter values to the template
        context['chart_data_json'] = json.dumps(chart_data) if chart_data else "null"
        context['selected_user_id'] = int(selected_user_id) if selected_user_id else None
        context['start_date'] = start_date_str
        context['end_date'] = end_date_str
        
        return context

def add_subtask(request, task_pk):
    task = get_object_or_404(Task, pk=task_pk)
    if request.method == 'POST':
        form = SubTaskForm(request.POST)
        if form.is_valid():
            subtask = form.save(commit=False)
            subtask.task = task
            subtask.save()
    # Redirect back to the project detail page regardless of success
    return redirect('project_detail', pk=task.project.pk)