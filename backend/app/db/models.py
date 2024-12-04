from sqlalchemy import Column, Integer, String, DateTime, UUID
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
    description = Column(String, nullable=True)
    user_id = Column(UUID, nullable=True)  # Pour future authentification
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    refresh_frequency = Column(String, nullable=False)

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())