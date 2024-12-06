from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session
from uuid import UUID
from app.db.session import get_db
from app.db.models import Service, RefreshFrequency, ServiceStats
from app.api.models.service import ServiceCreate, ServiceResponse, ServiceStatsCreate, ServiceStatsResponse, ServiceStatsAggregated
from app.core.monitor import calculate_period_stats
from datetime import datetime, timedelta
from app.core.auth import get_current_user
from app.db.models import User

router = APIRouter()

@router.post("/services/", response_model=ServiceResponse, status_code=201)
def create_service(
    service: ServiceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_service = Service(
        name=service.name,
        url=str(service.url),
        user_id=current_user.id,
        refresh_frequency=service.refresh_frequency
    )
    db.add(db_service)
    db.commit()
    db.refresh(db_service)
    return db_service

@router.get("/services/", response_model=List[ServiceResponse])
def get_services(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    services = db.query(Service).filter(Service.user_id == current_user.id).all()
    services_response = []
    # Pour chaque service, on récupère uniquement la stat la plus récente
    for service in services:
        service_response = ServiceResponse.from_db(service)
        stats = db.query(ServiceStats)\
            .filter(ServiceStats.service_id == service.id)\
            .order_by(desc(ServiceStats.ping_date))\
            .limit(1)\
            .all()
        stats_response = [ServiceStatsResponse.from_db(stat) for stat in stats]
        service_response.stats = stats_response

        total_checks = db.query(ServiceStats)\
            .filter(ServiceStats.service_id == service.id)\
            .count()
        service_response.total_checks = total_checks
        services_response.append(service_response)
    
    return services_response

@router.post("/services/{service_id}/stats/", response_model=ServiceStatsResponse, status_code=201)
def create_service_stats(
    service_id: UUID,
    stats: ServiceStatsCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify that service exists
    service = db.query(Service).filter(Service.id == service_id, Service.user_id == current_user.id).first()
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = db.query(Service).filter(Service.id == service_id, Service.user_id == current_user.id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    # Delete associated stats first (due to foreign key constraint)
    db.query(ServiceStats).filter(ServiceStats.service_id == service_id).delete()
    
    # Delete the service
    db.delete(service)
    db.commit()
    
    return None

@router.get("/services/{service_id}/stats/aggregated", 
           response_model=ServiceStatsAggregated)
async def get_service_stats_aggregated(
    service_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = db.query(Service).filter(Service.id == service_id, Service.user_id == current_user.id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    now = datetime.utcnow()
    
    stats_1h = calculate_period_stats(
        db, service_id, now - timedelta(hours=1), "1h")
    stats_24h = calculate_period_stats(
        db, service_id, now - timedelta(hours=24), "24h")
    stats_7d = calculate_period_stats(
        db, service_id, now - timedelta(days=7), "7d")
    stats_30d = calculate_period_stats(
        db, service_id, now - timedelta(days=30), "30d")
    
    return ServiceStatsAggregated(
        service_id=service_id,
        stats_1h=stats_1h,
        stats_24h=stats_24h,
        stats_7d=stats_7d,
        stats_30d=stats_30d
    )