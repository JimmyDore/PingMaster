from pydantic import BaseModel, UUID4
from datetime import datetime
from typing import Optional
from app.db.models import RefreshFrequency

class ServiceCreate(BaseModel):
    name: str
    description: Optional[str] = None
    refresh_frequency: RefreshFrequency = RefreshFrequency.ONE_HOUR

class ServiceResponse(BaseModel):
    id: UUID4
    name: str
    description: Optional[str]
    user_id: UUID4
    created_at: datetime
    refresh_frequency: RefreshFrequency

    class Config:
        from_attributes = True