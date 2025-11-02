"""Scheduler service for managing scheduled snapshot jobs."""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session
from datetime import datetime
from app.core.database import SessionLocal
from app.models import SnapshotJob
from app.services.snapshot import SnapshotService
import logging

logger = logging.getLogger(__name__)


class SchedulerService:
    """Service for managing scheduled snapshot jobs using APScheduler."""

    def __init__(self):
        """Initialize scheduler service."""
        self.scheduler = AsyncIOScheduler()
        self.scheduler.start()
        logger.info("Scheduler service started")

    def shutdown(self):
        """Shutdown the scheduler."""
        self.scheduler.shutdown()
        logger.info("Scheduler service stopped")

    async def _execute_snapshot_job(self, job_id: int, zone_id: int):
        """Execute a snapshot job.

        Args:
            job_id: ID of the SnapshotJob
            zone_id: ID of the zone to snapshot
        """
        db = SessionLocal()
        try:
            logger.info(f"Executing scheduled snapshot job {job_id} for zone {zone_id}")

            # Create snapshot
            service = SnapshotService(db)
            await service.create_snapshot(zone_id)

            # Update job last_run time
            job = db.query(SnapshotJob).filter(SnapshotJob.id == job_id).first()
            if job:
                job.last_run = datetime.utcnow()
                db.commit()

            logger.info(f"Completed scheduled snapshot job {job_id}")

        except Exception as e:
            logger.error(f"Error executing snapshot job {job_id}: {e}")
        finally:
            db.close()

    def load_jobs_from_database(self):
        """Load all enabled jobs from database and schedule them."""
        db = SessionLocal()
        try:
            jobs = db.query(SnapshotJob).filter(SnapshotJob.enabled == True).all()

            for job in jobs:
                self.schedule_job(job)

            logger.info(f"Loaded {len(jobs)} jobs from database")

        finally:
            db.close()

    def schedule_job(self, job: SnapshotJob):
        """Schedule a snapshot job.

        Args:
            job: SnapshotJob instance
        """
        job_id_str = f"snapshot_job_{job.id}"

        # Remove existing job if present
        if self.scheduler.get_job(job_id_str):
            self.scheduler.remove_job(job_id_str)

        # Create trigger based on schedule type
        trigger = None
        if job.schedule_type == "cron":
            # Parse cron expression
            # Expected format: "minute hour day month day_of_week"
            # Example: "0 2 * * *" for daily at 2 AM
            try:
                parts = job.schedule_value.split()
                if len(parts) == 5:
                    trigger = CronTrigger(
                        minute=parts[0],
                        hour=parts[1],
                        day=parts[2],
                        month=parts[3],
                        day_of_week=parts[4]
                    )
                else:
                    logger.error(f"Invalid cron expression for job {job.id}: {job.schedule_value}")
                    return
            except Exception as e:
                logger.error(f"Failed to parse cron expression for job {job.id}: {e}")
                return

        elif job.schedule_type == "interval":
            # Parse interval in seconds
            try:
                seconds = int(job.schedule_value)
                trigger = IntervalTrigger(seconds=seconds)
            except ValueError:
                logger.error(f"Invalid interval value for job {job.id}: {job.schedule_value}")
                return

        if trigger:
            self.scheduler.add_job(
                self._execute_snapshot_job,
                trigger=trigger,
                args=[job.id, job.zone_id],
                id=job_id_str,
                name=f"Snapshot job for zone {job.zone_id}",
                replace_existing=True
            )
            logger.info(f"Scheduled job {job.id} ({job.schedule_type}: {job.schedule_value})")

            # Update next_run time
            db = SessionLocal()
            try:
                db_job = db.query(SnapshotJob).filter(SnapshotJob.id == job.id).first()
                if db_job:
                    scheduled_job = self.scheduler.get_job(job_id_str)
                    if scheduled_job and scheduled_job.next_run_time:
                        db_job.next_run = scheduled_job.next_run_time
                        db.commit()
            finally:
                db.close()

    def unschedule_job(self, job_id: int):
        """Remove a job from the scheduler.

        Args:
            job_id: ID of the SnapshotJob
        """
        job_id_str = f"snapshot_job_{job_id}"
        if self.scheduler.get_job(job_id_str):
            self.scheduler.remove_job(job_id_str)
            logger.info(f"Unscheduled job {job_id}")


# Global scheduler instance
scheduler_service = SchedulerService()
