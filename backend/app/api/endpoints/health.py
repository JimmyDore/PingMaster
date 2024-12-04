from fastapi import APIRouter
from app.core.scheduler import scheduler

router = APIRouter()

@router.get("/health")
async def health_check():
    """Check if the application and scheduler are running"""
    return {
        "status": "healthy",
        "scheduler_running": scheduler.running,
        "job_count": len(scheduler.get_jobs())
    } 