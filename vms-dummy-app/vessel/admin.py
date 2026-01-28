from django.contrib import admin
from .models import Vessel, DeploymentLog


@admin.register(Vessel)
class VesselAdmin(admin.ModelAdmin):
    list_display = ['name', 'imo_number', 'vessel_type', 'vms_version', 'is_online', 'last_updated']
    list_filter = ['vessel_type', 'is_online', 'flag']
    search_fields = ['name', 'imo_number']
    readonly_fields = ['last_updated']


@admin.register(DeploymentLog)
class DeploymentLogAdmin(admin.ModelAdmin):
    list_display = ['vessel', 'version', 'status', 'deployed_at', 'duration_seconds']
    list_filter = ['status', 'deployed_at']
    search_fields = ['vessel__name', 'version']
    readonly_fields = ['deployed_at']
