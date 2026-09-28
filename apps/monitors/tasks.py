import time
import urllib.request
from urllib.error import URLError, HTTPError
from celery import shared_task
from django.utils import timezone
from .models import Monitor, HeartbeatLog


@shared_task
def ping_monitor(monitor_id):
    try:
        monitor = Monitor.objects.get(id=monitor_id, is_active=True)
    except Monitor.DoesNotExist:
        return f"Monitor {monitor_id} not found or inactive."

    start_time = time.time()
    is_successful = False
    status_code = None
    error_message = ""

    req = urllib.request.Request(
        monitor.url,
        headers={'User-Agent': 'PingPulse-Bot/1.0'}
    )

    try:
        with urllib.request.urlopen(req, timeout=monitor.timeout_seconds) as response:
            status_code = response.getcode()
            response_time_ms = int((time.time() - start_time) * 1000)
            
            if status_code == monitor.expected_status_code:
                is_successful = True
                monitor.status = 'UP'
            else:
                monitor.status = 'DOWN'
                error_message = f"Unexpected status code: {status_code} (expected {monitor.expected_status_code})"

    except HTTPError as e:
        response_time_ms = int((time.time() - start_time) * 1000)
        status_code = e.code
        monitor.status = 'DOWN'
        error_message = f"HTTP Error: {e.code} {e.reason}"

    except URLError as e:
        response_time_ms = int((time.time() - start_time) * 1000)
        monitor.status = 'DOWN'
        error_message = f"Connection Failed: {e.reason}"

    except Exception as e:
        response_time_ms = int((time.time() - start_time) * 1000)
        monitor.status = 'DOWN'
        error_message = f"Error: {str(e)}"

    # Update monitor metadata
    monitor.last_checked_at = timezone.now()
    monitor.save()

    # Record heartbeat log entry
    HeartbeatLog.objects.create(
        monitor=monitor,
        status_code=status_code,
        response_time_ms=response_time_ms,
        is_successful=is_successful,
        error_message=error_message
    )

    return f"Pinged {monitor.url}: Status {monitor.status} ({response_time_ms}ms)"


@shared_task
def ping_all_monitors():
    active_monitors = Monitor.objects.filter(is_active=True)
    for monitor in active_monitors:
        ping_monitor.delay(monitor.id)
    return f"Dispatched {active_monitors.count()} monitor check tasks."