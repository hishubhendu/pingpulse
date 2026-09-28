from django.contrib import admin
from .models import Monitor, HeartbeatLog


@admin.register(Monitor)
class MonitorAdmin(admin.ModelAdmin):
    list_display = ('name', 'url', 'status', 'interval_seconds', 'last_checked_at', 'is_active')
    list_filter = ('status', 'is_active')
    search_fields = ('name', 'url')


@admin.register(HeartbeatLog)
class HeartbeatLogAdmin(admin.ModelAdmin):
    list_display = ('monitor', 'status_code', 'response_time_ms', 'is_successful', 'checked_at')
    list_filter = ('is_successful', 'checked_at')
    search_fields = ('monitor__name', 'monitor__url')
    readonly_fields = ('checked_at',)