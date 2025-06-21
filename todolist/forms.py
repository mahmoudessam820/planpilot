from django import forms

from .models import Todolist


class TodolistForm(forms.ModelForm):
    class Meta:
        model = Todolist
        fields = ['name', 'description']

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        if not name:
            raise forms.ValidationError('Name cannot be empty.')
        if len(name) > 100:
            raise forms.ValidationError('Name cannot be longer than 100 characters.')
        if name.isalnum():
            raise forms.ValidationError('Name must be alphabetical.')
        if Todolist.objects.filter(name=name).exists():
            raise forms.ValidationError('A todo list with this name already exists.')
        return name

    def clean_description(self):
        description = self.cleaned_data['description'].strip()
        if len(description) > 500:
            raise forms.ValidationError('Description cannot be longer than 500 characters.')
        return description


class EditTodolistForm(forms.ModelForm):
    class Meta:
        model = Todolist
        fields = ['name', 'description']

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        if not name:
            raise forms.ValidationError('Name cannot be empty.')
        if len(name) > 100:
            raise forms.ValidationError('Name cannot be longer than 100 characters.')
        if name.isalnum():
            raise forms.ValidationError('Name must be alphabetical.')
        return name

    def clean_description(self):
        description = self.cleaned_data['description'].strip()
        if len(description) > 500:
            raise forms.ValidationError('Description cannot be longer than 500 characters.')
        return description
