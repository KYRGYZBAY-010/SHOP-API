from django.contrib import admin
from .models import Project, Clients

# Register your models here.
@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['id','title', 'date']


@admin.register(Clients)
class ClientsAdmin(admin.ModelAdmin):
    list_display = ['title', 'date']