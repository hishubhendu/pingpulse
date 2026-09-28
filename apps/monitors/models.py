from django.db import models
from django.contrib.auth.models import User

class Monitor(models.Model):
    STATUS_CHOICES = [
        ('UP', 'Up'),
        ('DOWN', 'Down'),
        ('PENDING', 'Pending'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='monitors')
    name = models.CharField(max_length=255)
    url = models.URLField(max_length=500)
    interval_seconds = models.IntegerField(default=120)  # Check frequency in seconds
    expected_status_code = models.IntegerField(default=200)
    timeout_seconds = models.IntegerField(default=5)
    
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    is_active = models.BooleanField(default=True)
    
    last_checked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.url})"


class HeartbeatLog(models.Model):
    monitor = models.ForeignKey(Monitor, on_delete=models.CASCADE, related_name='logs')
    status_code = models.IntegerField(null=True, blank=True)
    response_time_ms = models.IntegerField(null=True, blank=True)
    is_successful = models.BooleanField(default=False)
    error_message = models.TextField(blank=True, default='')
    checked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-checked_at']
        indexes = [
            models.Index(fields=['monitor', '-checked_at']),
        ]

    def __str__(self):
        status = "SUCCESS" if self.is_successful else "FAILED"
        return f"{self.monitor.name} - {status} at {self.checked_at}"