from fastapi import FastAPI
from app.api.endpoints import hello

app = FastAPI(
    title="MonitoringDashboard API",
    description="Backend API for Monitoring Dashboard",
    version="0.1.0"
)

# Include routers
app.include_router(hello.router, prefix="/api")