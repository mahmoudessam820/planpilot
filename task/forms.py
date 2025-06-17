from django import forms

from .models import Task


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['name', 'description']

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        if not name:
            raise forms.ValidationError('Name cannot be empty.')
        if len(name) > 100:
            raise forms.ValidationError('Name cannot exceed 100 characters.')
        if Task.objects.filter(name=name).exists():
            raise forms.ValidationError('A task with this name already exists.')
        return name

    def clean_description(self):
        description = self.cleaned_data['description'].strip()
        return description


class EditTaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['name', 'description']

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        if not name:
            raise forms.ValidationError('Name cannot be empty.')
        if len(name) > 100:
            raise forms.ValidationError('Name cannot exceed 100 characters.')
        return name

    def clean_description(self):
        description = self.cleaned_data['description'].strip()
        return description
