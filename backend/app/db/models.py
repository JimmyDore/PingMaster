from sqlalchemy import Column, Integer, String, DateTime, UUID, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from uuid import uuid4
from .session import Base
from enum import Enum
from datetime import datetime

class RefreshFrequency(str, Enum):
    ONE_MINUTE = "1 minute"
    TEN_MINUTES = "10 minutes" 
    ONE_HOUR = "1 hour"

class Service(Base):
    __tablename__ = "services"

    id = Column(UUID, primary_key=True, default=uuid4)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    user_id = Column(UUID, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    refresh_frequency = Column(String, nullable=False)
    
    # Relation avec les stats
    stats = relationship("ServiceStats", back_populates="service", order_by="desc(ServiceStats.ping_date)")
    user = relationship("User", back_populates="services")
    notification_preferences = relationship("NotificationPreference", back_populates="service", uselist=False)

class ServiceStats(Base):
    __tablename__ = "service_stats"

    id = Column(UUID, primary_key=True, default=uuid4)
    service_id = Column(UUID, ForeignKey('services.id'), nullable=False)
    ping_date = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(Boolean, nullable=False)  # True pour up, False pour down
    response_time = Column(Float, nullable=True)
    
    # Relation inverse
    service = relationship("Service", back_populates="stats")

    @property
    def is_down(self) -> bool:
        return not self.status

class User(Base):
    __tablename__ = "users"

    id = Column(UUID, primary_key=True, default=uuid4)
    username = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relation avec les services
    services = relationship("Service", back_populates="user")

class NotificationMethod(str, Enum):
    SLACK = "slack"

class AlertFrequency(str, Enum):
    ALWAYS = "always"
    DAILY = "daily"

class NotificationPreference(Base):
    __tablename__ = "notification_preferences"

    id = Column(UUID, primary_key=True, default=uuid4)
    service_id = Column(UUID, ForeignKey('services.id'), nullable=False)
    notification_method = Column(String, nullable=False)
    alert_frequency = Column(String, nullable=False)
    webhook_url = Column(String, nullable=False)
    last_alert_time = Column(DateTime(timezone=True), nullable=True)
    notify_on_recovery = Column(Boolean, default=True)
    
    # Relations
    service = relationship("Service", back_populates="notification_preferences")