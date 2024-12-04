from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "MonitoringDashboard API"
    VERSION: str = "0.1.0"
    API_STR: str = "/api/"
    SQLITE_URL: str = "sqlite:///./sql_app.db"

    class Config:
        env_file = ".env"

settings = Settings()