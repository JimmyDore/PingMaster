import logging
import os
from fastapi import FastAPI
from app.api.endpoints import hello, messages
from app.db.session import init_db, SQLITE_URL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="MonitoringDashboard API",
    description="Backend API for Monitoring Dashboard",
    version="0.1.0"
)

@app.on_event("startup")
def startup_event():
    logger.info(f"Using database at: {SQLITE_URL}")
    logger.info(f"Current directory: {os.getcwd()}")
    logger.info(f"Directory contents of /app/data: {os.listdir('/app/data')}")
    init_db()
    logger.info("Database initialized")

app.include_router(hello.router, prefix="/api")
app.include_router(messages.router, prefix="/api")