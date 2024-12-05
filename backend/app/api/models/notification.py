from pydantic import BaseModel, UUID4, HttpUrl, validator
from datetime import datetime
from typing import Optional
from app.db.models import NotificationMethod, AlertFrequency

class NotificationPreferenceCreate(BaseModel):
    service_id: UUID4
    notification_method: NotificationMethod = NotificationMethod.SLACK
    alert_frequency: AlertFrequency = AlertFrequency.ALWAYS
    webhook_url: str
    notify_on_recovery: bool = True

class NotificationPreferenceResponse(NotificationPreferenceCreate):
    id: UUID4
    last_alert_time: Optional[datetime] = None

    class Config:
        from_attributes = True 