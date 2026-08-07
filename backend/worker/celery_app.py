from celery import Celery
from celery.schedules import crontab
from core.config import settings

celery_app = Celery(
    "worker",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

celery_app.conf.task_routes = {"worker.tasks.*": "main-queue"}

# Schedule the workflow to run every 6 hours
celery_app.conf.beat_schedule = {
    "run-job-discovery-every-6-hours": {
        "task": "worker.tasks.run_job_discovery_workflow",
        "schedule": crontab(minute=0, hour="*/6"),
    },
}
