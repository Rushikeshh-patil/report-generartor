# todo/forms.py

from django import forms
from .models import Project, Task, SubTask 

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        # Add 'project_manager' to the fields list
        fields = ['name', 'description', 'project_manager', 'members']

    def __init__(self, *args, **kwargs):
        super(ProjectForm, self).__init__(*args, **kwargs)
        # Style the form fields
        self.fields['name'].widget.attrs.update({'class': 'w-full p-2 border rounded'})
        self.fields['description'].widget.attrs.update({'class': 'w-full p-2 border rounded', 'rows': 3})
        self.fields['project_manager'].widget.attrs.update({'class': 'w-full p-2 border rounded'})
        self.fields['members'].widget.attrs.update({'class': 'w-full p-2 border rounded'})

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        # Add 'due_date' to the fields
        fields = ['title', 'description', 'project', 'assignee', 'estimated_hours', 'due_date']
        # Add a widget for a calendar-style date picker
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, user, *args, **kwargs):
        super(TaskForm, self).__init__(*args, **kwargs)
        self.fields['project'].queryset = Project.objects.filter(members=user)
        # Style all form fields
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'w-full p-2 border rounded'})

class SubTaskForm(forms.ModelForm):
    class Meta:
        model = SubTask
        fields = ['title']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full p-2 border rounded text-sm',
                'placeholder': 'Add a new sub-task...'
            })
        }