"""Task Queue Port - Abstract interface for background task execution."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Callable
from enum import Enum


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class TaskQueue(ABC):
    """Abstract base class for task queue systems (Celery, RQ, etc.)."""

    @abstractmethod
    async def enqueue(
        self,
        task_name: str,
        args: tuple = (),
        kwargs: Optional[Dict[str, Any]] = None,
        priority: int = 5,
        eta: Optional[float] = None,
    ) -> str:
        """
        Enqueue a task for background execution.

        Args:
            task_name: Name of the task function to execute
            args: Positional arguments for the task
            kwargs: Keyword arguments for the task
            priority: Task priority (0-10, higher = more urgent)
            eta: Optional Unix timestamp for delayed execution

        Returns:
            Task ID (UUID as string)
        """
        pass

    @abstractmethod
    async def get_task_status(self, task_id: str) -> TaskStatus:
        """
        Get the current status of a task.

        Args:
            task_id: Task UUID

        Returns:
            TaskStatus enum value
        """
        pass

    @abstractmethod
    async def get_task_result(self, task_id: str) -> Optional[Any]:
        """
        Get the result of a completed task.

        Args:
            task_id: Task UUID

        Returns:
            Task result if completed, None otherwise
        """
        pass

    @abstractmethod
    async def get_task_error(self, task_id: str) -> Optional[str]:
        """
        Get error details if a task failed.

        Args:
            task_id: Task UUID

        Returns:
            Error message/traceback if failed, None otherwise
        """
        pass

    @abstractmethod
    async def cancel_task(self, task_id: str) -> bool:
        """
        Attempt to cancel a pending or running task.

        Args:
            task_id: Task UUID

        Returns:
            True if cancellation was successful, False otherwise
        """
        pass

    @abstractmethod
    async def schedule_periodic(
        self,
        task_name: str,
        schedule: str,
        args: tuple = (),
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Schedule a task to run periodically.

        Args:
            task_name: Name of the task function
            schedule: Cron expression or interval string (e.g., '0 2 * * *' or 'every 1h')
            args: Positional arguments
            kwargs: Keyword arguments

        Returns:
            Schedule ID
        """
        pass

    @abstractmethod
    async def remove_schedule(self, schedule_id: str) -> None:
        """
        Remove a periodic task schedule.

        Args:
            schedule_id: Schedule identifier
        """
        pass
