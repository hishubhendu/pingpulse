import os
from celery import Celery

# Set default Django settings module for 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('pingpulse')

# Read config from Django settings using the CELERY_ prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Automatically discover tasks in all registered Django app configs.
app.autodiscover_tasks()