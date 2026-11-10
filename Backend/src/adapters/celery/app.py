"""Celery application with Aiven Redis broker/backend."""

from celery import Celery
from celery.signals import worker_process_init, worker_process_shutdown
import logging

from src.config.settings import settings

logger = logging.getLogger(__name__)


# Create Celery app with Aiven Redis
celery_app = Celery(
    settings.APP_NAME,
    broker=settings.get_celery_broker_url,
    backend=settings.get_celery_result_backend,
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,
    task_soft_time_limit=25 * 60,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    broker_connection_retry_on_startup=True,
    broker_heartbeat=30,
    broker_transport_options={
        "visibility_timeout": 3600,
        "socket_keepalive": True,
        "retry_on_timeout": True,
    },
    redis_socket_keepalive=True,
    redis_socket_timeout=30,
)

# Auto-discover tasks
celery_app.autodiscover_tasks(["src.adapters.celery.tasks"])


@worker_process_init.connect
def init_worker(**kwargs):
    """Initialize worker process."""
    logger.info("Celery worker process starting...")


@worker_process_shutdown.connect
def shutdown_worker(**kwargs):
    """Cleanup on worker shutdown."""
    logger.info("Celery worker process shutting down...")


if __name__ == "__main__":
    celery_app.start()
