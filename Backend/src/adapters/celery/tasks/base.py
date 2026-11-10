"""Base Celery task for async event loop execution."""

import asyncio
import sys
from celery import Task


class AsyncTask(Task):
    """Base task that handles async execution."""

    def __call__(self, *args, **kwargs):
        """Run async tasks in event loop with proper loop management."""
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(self.run(*args, **kwargs))

    async def run(self, *args, **kwargs):
        raise NotImplementedError
