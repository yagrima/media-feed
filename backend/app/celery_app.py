"""
Celery Application Configuration
Handles background tasks and periodic jobs
"""
from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

# Create Celery app
celery_app = Celery(
    "mefeed",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=['app.tasks.session_tasks']
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    # Fix for read-only filesystem in containers
    beat_schedule_filename='/var/run/celery/celerybeat-schedule',
)

# Configure periodic tasks (Celery Beat)
celery_app.conf.beat_schedule = {
    'cleanup-expired-sessions': {
        'task': 'app.tasks.session_tasks.cleanup_expired_sessions',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2:00 AM UTC
        'options': {
            'expires': 3600,  # Task expires after 1 hour if not picked up
        }
    },
}

# Optional: Configure result backend expiration
celery_app.conf.result_expires = 3600  # Results expire after 1 hour
