from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.core.monitor import check_services
from app.db.session import SessionLocal
import logging

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

async def monitoring_job():
    """Job that runs every minute to check services"""
    try:
        db = SessionLocal()
        await check_services(db)
        logger.info("Monitoring job completed successfully")
    except Exception as e:
        logger.error(f"Error in monitoring job: {str(e)}")
    finally:
        db.close()

def init_scheduler():
    """Initialize the scheduler with all jobs"""
    try:
        # Ajoute la tâche de monitoring pour s'exécuter chaque minute
        scheduler.add_job(
            monitoring_job,
            CronTrigger(minute='*'),  # Toutes les minutes
            id='monitoring_job',
            name='Check all services status',
            replace_existing=True
        )
        
        # Démarre le scheduler
        scheduler.start()
        logger.info("Scheduler started successfully")
    except Exception as e:
        logger.error(f"Failed to initialize scheduler: {str(e)}")
        raise