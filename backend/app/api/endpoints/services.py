from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from app.db.session import get_db
from app.db.models import Service, RefreshFrequency
from app.api.models.service import ServiceCreate, ServiceResponse

router = APIRouter()

MOCK_USER_ID = UUID("550e8400-e29b-41d4-a716-446655440000")

@router.post("/services/", response_model=ServiceResponse, status_code=201)
def create_service(
    service: ServiceCreate,
    db: Session = Depends(get_db)
):
    db_service = Service(
        name=service.name,
        description=service.description,
        user_id=MOCK_USER_ID,
        refresh_frequency=service.refresh_frequency
    )
    db.add(db_service)
    db.commit()
    db.refresh(db_service)
    return db_service