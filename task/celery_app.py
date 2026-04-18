from celery import Celery
from celery.schedules import crontab
celery_app = Celery(
    "rayyan",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1",
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Africa/Lagos",
    enable_utc=True,
    task_soft_time_limit=300,
    task_time_limit=360,
    beat_max_loop_interval=5,
)

celery_app.conf.beat_schedule = {
    "run-product-updates-every-60-seconds": {
        "task": "task.tasks.run_product_updates", 
        "schedule": crontab(minute=0, hour=0),
    },
    "requery-pending-transactions": {
        "task": "task.tasks.requery_pending_transactions",
        "schedule": 120.0,
        #"options": {"queue": "requery"},
    },
}
celery_app.autodiscover_tasks(["task"])