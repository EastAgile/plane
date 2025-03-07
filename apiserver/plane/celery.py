import os
from celery import Celery
from plane.settings.redis import redis_instance
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plane.settings.production")

ri = redis_instance()

app = Celery("plane")

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object("django.conf:settings", namespace="CELERY")

app.conf.beat_schedule = {
    # Executes every day at 12 AM
    "check-every-day-to-archive-and-close": {
        "task": "plane.bgtasks.issue_automation_task.archive_and_close_old_issues",
        "schedule": crontab(hour=0, minute=0),
    },
    "check-every-day-to-delete_exporter_history": {
        "task": "plane.bgtasks.exporter_expired_task.delete_old_s3_link",
        "schedule": crontab(hour=0, minute=0),
    },
    "check-every-day-to-delete-file-asset": {
        "task": "plane.bgtasks.file_asset_task.delete_unuploaded_file_asset",
        "schedule": crontab(hour=0, minute=0),
    },
    "check-every-minutes-to-send-email-notifications": {
        "task": "plane.bgtasks.email_notification_task.stack_email_notification",
        "schedule": crontab(minute="*/1"),
    },
    "check-every-day-to-delete-hard-delete": {
        "task": "plane.bgtasks.deletion_task.hard_delete",
        "schedule": crontab(hour=0, minute=0),
    },
    "check-every-day-to-delete-api-logs": {
        "task": "plane.bgtasks.api_logs_task.delete_api_logs",
        "schedule": crontab(hour=0, minute=0),
    },
    "run-every-6-hours-for-instance-trace": {
        "task": "plane.license.bgtasks.tracer.instance_traces",
        "schedule": crontab(hour="*/6", minute=0),
    },
    # Auto-transfer unfinished issues from completed cycles (run daily at 00:30 AM)
    "auto-transfer-cycle-issues-daily": {
        "task": "plane.bgtasks.cycle_issue_transfer_task.auto_transfer_unfinished_cycle_issues",
        "schedule": crontab(hour=0, minute=30),
    },
    # Recalculate all project velocities daily at 1 AM (after other midnight tasks)
    "recalculate-project-velocities-daily": {
        "task": "plane.bgtasks.project_velocity_task.recalculate_all_project_velocities",
        "schedule": crontab(hour=1, minute=0),
    },
    # Auto-create next cycle when current cycle is ending (run daily at 2 AM)
    "auto-create-next-cycle-daily": {
        "task": "plane.bgtasks.cycle_auto_create_task.auto_create_next_cycle",
        "schedule": crontab(hour=2, minute=0),
    },
}

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

app.conf.beat_scheduler = "django_celery_beat.schedulers.DatabaseScheduler"
