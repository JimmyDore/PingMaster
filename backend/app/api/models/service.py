from pydantic import BaseModel, UUID4, HttpUrl
from datetime import datetime
from app.db.models import RefreshFrequency

class ServiceCreate(BaseModel):
    name: str
    url: HttpUrl
    refresh_frequency: RefreshFrequency = RefreshFrequency.ONE_HOUR

class ServiceResponse(BaseModel):
    id: UUID4
    name: str
    url: HttpUrl
    user_id: UUID4
    created_at: datetime
    refresh_frequency: RefreshFrequency

    class Config:
        from_attributes = True