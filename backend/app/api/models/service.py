from pydantic import BaseModel, UUID4, HttpUrl, Field, field_validator
from datetime import datetime
from app.db.models import RefreshFrequency, Service
from typing import List, Optional

from app.api.models.notification import NotificationPreferenceResponse

class ServiceCreate(BaseModel):
    name: str
    url: HttpUrl
    refresh_frequency: RefreshFrequency = RefreshFrequency.ONE_HOUR

class ServiceStatsCreate(BaseModel):
    service_id: UUID4
    status: bool
    response_time: Optional[float] = Field(None, ge=0)
    ping_date: datetime

    @field_validator('response_time')
    def round_response_time(cls, v):
        if v is not None:
            return round(v, 1)
        return v

    @field_validator('ping_date')
    def validate_ping_date(cls, v):
        if v > datetime.utcnow():
            raise ValueError("ping_date cannot be in the future")
        return v

class ServiceStatsResponse(ServiceStatsCreate):
    id: UUID4

    class Config:
        from_attributes = True

class ServiceResponse(BaseModel):
    id: UUID4
    name: str
    url: HttpUrl
    user_id: UUID4
    created_at: datetime
    refresh_frequency: RefreshFrequency
    stats: Optional[List[ServiceStatsResponse]] = []
    notification_preferences: Optional[NotificationPreferenceResponse] = None
    total_checks: Optional[int] = None
    class Config:
        from_attributes = True

    @classmethod
    def from_db(cls, db_service: Service):
        return cls(
            id=db_service.id,
            name=db_service.name,
            url=db_service.url,
            user_id=db_service.user_id,
            created_at=db_service.created_at,
            refresh_frequency=db_service.refresh_frequency,
            notification_preferences=db_service.notification_preferences,
        )

class AggregatedStats(BaseModel):
    period: str  # '24h', '7d', '30d'
    uptime_percentage: float
    avg_response_time: float
    status_counts: dict[str, int]  # {'up': X, 'down': Y}
    timestamps: list[datetime]
    response_times: list[float]

class ServiceStatsAggregated(BaseModel):
    service_id: UUID4
    stats_1h: AggregatedStats
    stats_24h: AggregatedStats
    stats_7d: AggregatedStats
    stats_30d: AggregatedStats