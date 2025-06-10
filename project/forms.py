from django import forms

from .models import ProjectFile, Project, ProjectNote


# Project form validation

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'description']

    def clean_name(self):
        name = self.cleaned_data['name']
        if len(name) > 100:
            raise forms.ValidationError("Name cannot exceed 100 characters.")
        elif Project.objects.filter(name=name).exists():
            raise forms.ValidationError("A project with this name already exists.")
        return name

# Project File form validation


class ProjectFileForm(forms.ModelForm):
    class Meta:
        model = ProjectFile
        fields = ['name', 'attachment']

    def clean_name(self):
        name = self.cleaned_data['name']
        if len(name) > 100:
            raise forms.ValidationError("Name cannot exceed 100 characters.")
        return name

    def clean_file(self):
        file = self.cleaned_data['attachment']
        max_size = 5 * 1024 * 1024  # 5MB
        allowed_types = ['application/pdf', 'image/jpeg', 'image/png']
        if file.size > max_size:
            raise forms.ValidationError('File size must be under 5MB.')
        if file.content_type not in allowed_types:
            raise forms.ValidationError('Invalid file type.')
        return file


# Project Note form validation

class ProjectNoteForm(forms.ModelForm):
    class Meta:
        model = ProjectNote
        fields = ['name', 'body']

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        if not name:
            raise forms.ValidationError('Name cannot be empty.')
        if len(name) > 100:
            raise forms.ValidationError("Name cannot exceed 100 characters.")
        return name

    def clean_body(self):
        body = self.cleaned_data['body'].strip()
        if not body:
            raise forms.ValidationError('Body cannot be empty.')
        return body
