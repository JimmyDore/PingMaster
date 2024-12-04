from sqlalchemy import Column, Integer, String, DateTime, UUID, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from uuid import uuid4
from .session import Base
from enum import Enum

class RefreshFrequency(str, Enum):
    ONE_MINUTE = "1 minute"
    TEN_MINUTES = "10 minutes" 
    ONE_HOUR = "1 hour"

class Service(Base):
    __tablename__ = "services"

    id = Column(UUID, primary_key=True, default=uuid4)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    user_id = Column(UUID, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    refresh_frequency = Column(String, nullable=False)
    
    # Relation avec les stats
    stats = relationship("ServiceStats", back_populates="service", order_by="desc(ServiceStats.ping_date)")

class ServiceStats(Base):
    __tablename__ = "service_stats"

    id = Column(UUID, primary_key=True, default=uuid4)
    service_id = Column(UUID, ForeignKey('services.id'), nullable=False)
    ping_date = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(Boolean, nullable=False)  # True pour up, False pour down
    response_time = Column(Float, nullable=True)
    
    # Relation inverse
    service = relationship("Service", back_populates="stats")

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())