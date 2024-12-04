from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session
from uuid import UUID
from app.db.session import get_db
from app.db.models import Service, RefreshFrequency, ServiceStats
from app.api.models.service import ServiceCreate, ServiceResponse, ServiceStatsCreate, ServiceStatsResponse

router = APIRouter()

MOCK_USER_ID = UUID("550e8400-e29b-41d4-a716-446655440000")

@router.post("/services/", response_model=ServiceResponse, status_code=201)
def create_service(
    service: ServiceCreate,
    db: Session = Depends(get_db)
):
    db_service = Service(
        name=service.name,
        url=str(service.url),
        user_id=MOCK_USER_ID,
        refresh_frequency=service.refresh_frequency
    )
    db.add(db_service)
    db.commit()
    db.refresh(db_service)
    return db_service

@router.get("/services/", response_model=List[ServiceResponse])
def get_services(db: Session = Depends(get_db)):
    services = db.query(Service).all()
    
    # Pour chaque service, on récupère toutes ses stats triées par date
    for service in services:
        stats = db.query(ServiceStats)\
            .filter(ServiceStats.service_id == service.id)\
            .order_by(desc(ServiceStats.ping_date))\
            .all()
        
        service.stats = stats
    
    return services

@router.post("/services/{service_id}/stats/", response_model=ServiceStatsResponse)
def create_service_stats(
    service_id: UUID,
    stats: ServiceStatsCreate,
    db: Session = Depends(get_db)
):
    # Verify that service exists
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    # Create stats
    db_stats = ServiceStats(
        service_id=service_id,
        status=stats.status,
        response_time=stats.response_time,
        ping_date=stats.ping_date
    )
    
    db.add(db_stats)
    db.commit()
    db.refresh(db_stats)
    
    return db_stats

@router.delete("/services/{service_id}", status_code=204)
def delete_service(
    service_id: UUID,
    db: Session = Depends(get_db)
):
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    # Delete associated stats first (due to foreign key constraint)
    db.query(ServiceStats).filter(ServiceStats.service_id == service_id).delete()
    
    # Delete the service
    db.delete(service)
    db.commit()
    
    return None