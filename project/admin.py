from django.contrib import admin


from .models import Project, ProjectFile, ProjectNote 


admin.site.register(Project)
admin.site.register(ProjectFile)
admin.site.register(ProjectNote)
