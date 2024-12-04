from pydantic import BaseModel, UUID4, HttpUrl
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
    response_time: Optional[float]
    ping_date: datetime = datetime.utcnow()

class ServiceStatsResponse(BaseModel):
    status: bool
    response_time: Optional[float]
    ping_date: datetime

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