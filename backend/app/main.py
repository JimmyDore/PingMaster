import logging
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import hello, messages, services
from app.db.session import init_db, SQLITE_URL, DATA_DIR

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="MonitoringDashboard API",
    description="Backend API for Monitoring Dashboard",
    version="0.1.0"
)

# Middleware pour logger les requêtes
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Incoming request: {request.method} {request.url}")
    logger.info(f"Headers: {request.headers}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response

# Configuration CORS avec plage de ports
origins = [
    f"http://localhost:{port}" for port in range(4321, 4330)
] + [
    f"http://127.0.0.1:{port}" for port in range(4321, 4330)
] + [
    "http://127.0.0.1:8888",
    "https://pingmasterjimmydore.netlify.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Routes après le middleware
app.include_router(hello.router, prefix="/api")
app.include_router(messages.router, prefix="/api")
app.include_router(services.router, prefix="/api")

@app.on_event("startup")
def startup_event():
    logger.info(f"Using database at: {SQLITE_URL}")
    logger.info(f"Current directory: {os.getcwd()}")
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        logger.info(f"Directory contents of {DATA_DIR}: {os.listdir(DATA_DIR)}")
    except Exception as e:
        logger.error(f"Error accessing data directory: {str(e)}")
    init_db()
    logger.info("Database initialized")