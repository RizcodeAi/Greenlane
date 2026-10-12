from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "greenlane",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.report_tasks", "app.tasks.ais_sync", "app.tasks.smart_alerts"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)


from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    'sync-live-ais-every-minute': {
        'task': 'sync_live_ais_data',
        'schedule': 60.0,
    },
    'run-smart-alerts-every-5-minutes': {
        'task': 'run_smart_alerts',
        'schedule': 300.0,
    },
}
