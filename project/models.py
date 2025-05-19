import uuid 
from django.db import models
    
from account.models import User


# Project Model

class Project(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    # Relationship models.
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects')

    def __str__(self):
        return self.name


# Files model

class ProjectFile(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    attachment = models.FileField(upload_to='projectfiles')

    # Relationship models.
    project = models.ForeignKey(Project, related_name='files', on_delete=models.CASCADE)

    def __str__(self):
        return self.name


# Note Model

class ProjectNote(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    body = models.TextField(blank=True, null=True)

    # Relationship models.
    project = models.ForeignKey(Project, related_name='notes', on_delete=models.CASCADE)
    
    def __str__(self):
        return self.name
