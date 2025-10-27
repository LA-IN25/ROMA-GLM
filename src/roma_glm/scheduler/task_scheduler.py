"""Task scheduler using apscheduler for autonomous agent."""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Callable, Dict, Optional, Any
from uuid import uuid4

from loguru import logger
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger


class TaskScheduler:
    """
    Wrapper around apscheduler AsyncIOScheduler for autonomous agent.

    Provides simplified interface for scheduling periodic tasks and one-time events
    in the autonomous trading agent.
    """

    def __init__(self):
        """Initialize the async scheduler."""
        self.scheduler = AsyncIOScheduler()
        self._registered_tasks: Dict[str, Callable] = {}
        logger.info("TaskScheduler initialized")

    def schedule_interval(
        self,
        task_func: Callable,
        interval_seconds: int,
        task_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        **kwargs,
    ) -> str:
        """
        Schedule a task to run at regular intervals.

        Args:
            task_func: Async function to execute
            interval_seconds: Interval in seconds between executions
            task_id: Unique identifier for the task (auto-generated if None)
            start_date: When to start the task (defaults to now)
            **kwargs: Additional arguments passed to task_func

        Returns:
            Task ID for managing the scheduled task
        """
        if task_id is None:
            task_id = f"interval_{uuid4().hex[:8]}"

        self._registered_tasks[task_id] = task_func

        async def wrapped_task():
            try:
                await task_func(**kwargs)
            except Exception as e:
                logger.error(f"Error executing scheduled task {task_id}: {e}")

        self.scheduler.add_job(
            wrapped_task,
            trigger=IntervalTrigger(seconds=interval_seconds, start_date=start_date),
            id=task_id,
            name=task_id,
            replace_existing=True,
        )

        logger.info(f"Scheduled interval task {task_id} every {interval_seconds}s")
        return task_id

    def schedule_cron(
        self,
        task_func: Callable,
        cron_expression: str,
        task_id: Optional[str] = None,
        **kwargs,
    ) -> str:
        """
        Schedule a task using cron expression.

        Args:
            task_func: Async function to execute
            cron_expression: Cron expression (e.g., "*/5 * * * *" for every 5 minutes)
            task_id: Unique identifier for the task
            **kwargs: Additional arguments passed to task_func

        Returns:
            Task ID for managing the scheduled task
        """
        if task_id is None:
            task_id = f"cron_{uuid4().hex[:8]}"

        self._registered_tasks[task_id] = task_func

        async def wrapped_task():
            try:
                await task_func(**kwargs)
            except Exception as e:
                logger.error(f"Error executing cron task {task_id}: {e}")

        # Parse cron expression (simplified for common patterns)
        parts = cron_expression.split()
        if len(parts) != 5:
            raise ValueError(f"Invalid cron expression: {cron_expression}")

        minute, hour, day, month, day_of_week = parts

        self.scheduler.add_job(
            wrapped_task,
            trigger=CronTrigger(
                minute=minute, hour=hour, day=day, month=month, day_of_week=day_of_week
            ),
            id=task_id,
            name=task_id,
            replace_existing=True,
        )

        logger.info(f"Scheduled cron task {task_id} with expression {cron_expression}")
        return task_id

    def schedule_once(
        self,
        task_func: Callable,
        run_date: datetime,
        task_id: Optional[str] = None,
        **kwargs,
    ) -> str:
        """
        Schedule a task to run once at a specific time.

        Args:
            task_func: Async function to execute
            run_date: When to run the task
            task_id: Unique identifier for the task
            **kwargs: Additional arguments passed to task_func

        Returns:
            Task ID for managing the scheduled task
        """
        if task_id is None:
            task_id = f"once_{uuid4().hex[:8]}"

        self._registered_tasks[task_id] = task_func

        async def wrapped_task():
            try:
                await task_func(**kwargs)
                # Remove the task after execution
                self.remove_task(task_id)
            except Exception as e:
                logger.error(f"Error executing one-time task {task_id}: {e}")

        self.scheduler.add_job(
            wrapped_task,
            trigger=DateTrigger(run_date=run_date),
            id=task_id,
            name=task_id,
            replace_existing=True,
        )

        logger.info(f"Scheduled one-time task {task_id} for {run_date}")
        return task_id

    def remove_task(self, task_id: str) -> bool:
        """
        Remove a scheduled task.

        Args:
            task_id: ID of the task to remove

        Returns:
            True if task was removed, False if not found
        """
        try:
            self.scheduler.remove_job(task_id)
            if task_id in self._registered_tasks:
                del self._registered_tasks[task_id]
            logger.info(f"Removed scheduled task {task_id}")
            return True
        except:
            logger.warning(f"Task {task_id} not found for removal")
            return False

    def pause_task(self, task_id: str) -> bool:
        """Pause a scheduled task."""
        try:
            self.scheduler.pause_job(task_id)
            logger.info(f"Paused task {task_id}")
            return True
        except:
            logger.warning(f"Task {task_id} not found for pausing")
            return False

    def resume_task(self, task_id: str) -> bool:
        """Resume a paused task."""
        try:
            self.scheduler.resume_job(task_id)
            logger.info(f"Resumed task {task_id}")
            return True
        except:
            logger.warning(f"Task {task_id} not found for resuming")
            return False

    def list_tasks(self) -> Dict[str, Dict[str, Any]]:
        """
        List all scheduled tasks with their details.

        Returns:
            Dictionary of task_id -> task_info
        """
        tasks = {}
        for job in self.scheduler.get_jobs():
            tasks[job.id] = {
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat()
                if job.next_run_time
                else None,
                "trigger": str(job.trigger),
                "active": True,
            }
        return tasks

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific task."""
        try:
            job = self.scheduler.get_job(task_id)
            if job:
                return {
                    "id": job.id,
                    "name": job.name,
                    "next_run_time": job.next_run_time.isoformat()
                    if job.next_run_time
                    else None,
                    "trigger": str(job.trigger),
                    "active": True,
                }
        except:
            pass
        return None

    def start(self) -> None:
        """Start the scheduler."""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("TaskScheduler started")

    def stop(self) -> None:
        """Stop the scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("TaskScheduler stopped")

    def is_running(self) -> bool:
        """Check if scheduler is running."""
        return self.scheduler.running

    async def shutdown(self) -> None:
        """Gracefully shutdown the scheduler."""
        logger.info("Shutting down TaskScheduler...")
        if self.scheduler.running:
            self.scheduler.shutdown(wait=True)
        logger.info("TaskScheduler shutdown complete")
