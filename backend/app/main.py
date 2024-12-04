from fastapi import FastAPI
from app.api.endpoints import hello, messages
from app.db.session import init_db

app = FastAPI(
    title="MonitoringDashboard API",
    description="Backend API for Monitoring Dashboard",
    version="0.1.0"
)

@app.on_event("startup")
def startup_event():
    init_db()

app.include_router(hello.router, prefix="/api")
app.include_router(messages.router, prefix="/api")