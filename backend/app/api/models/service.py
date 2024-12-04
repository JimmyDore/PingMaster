from pydantic import BaseModel, UUID4, HttpUrl, Field, validator
from datetime import datetime
from app.db.models import RefreshFrequency
from typing import List, Optional

class ServiceCreate(BaseModel):
    name: str
    url: HttpUrl
    refresh_frequency: RefreshFrequency = RefreshFrequency.ONE_HOUR

class ServiceStatsCreate(BaseModel):
    service_id: UUID4
    status: bool
    response_time: Optional[float] = Field(None, ge=0)
    ping_date: datetime

    @validator('ping_date')
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

    class Config:
        from_attributes = True

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