"""APScheduler-based export job scheduler."""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from typing import Dict, Any, Callable
import structlog

logger = structlog.get_logger()


class ExportScheduler:
    """Manages scheduled export jobs."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.scheduler = AsyncIOScheduler()
        self.jobs = {}
        
    def start(self):
        """Start the scheduler."""
        self.scheduler.start()
        logger.info("Export scheduler started")
    
    def shutdown(self):
        """Shutdown the scheduler."""
        self.scheduler.shutdown()
        logger.info("Export scheduler stopped")
    
    def add_export_job(self, job_id: str, export_func: Callable,
                      cron_expression: str = "0 2 * * *"):
        """Add a scheduled export job."""
        trigger = CronTrigger.from_crontab(cron_expression)
        
        job = self.scheduler.add_job(
            export_func,
            trigger=trigger,
            id=job_id,
            replace_existing=True,
            misfire_grace_time=3600  # 1 hour grace period
        )
        
        self.jobs[job_id] = job
        logger.info(f"Added export job: {job_id} with schedule: {cron_expression}")
        
        return job
    
    def trigger_manual_export(self, export_func: Callable) -> None:
        """Trigger immediate export."""
        logger.info("Triggering manual export")
        self.scheduler.add_job(
            export_func,
            id=f'manual_export_{datetime.utcnow().isoformat()}',
            replace_existing=True
        )
    
    def get_next_run_time(self, job_id: str) -> str:
        """Get next scheduled run time for job."""
        job = self.scheduler.get_job(job_id)
        if job and job.next_run_time:
            return job.next_run_time.isoformat()
        return "Not scheduled"
    
    def list_jobs(self) -> list:
        """List all scheduled jobs."""
        return [
            {
                'id': job.id,
                'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger)
            }
            for job in self.scheduler.get_jobs()
        ]
