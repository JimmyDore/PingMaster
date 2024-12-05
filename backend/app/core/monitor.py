from datetime import datetime, timedelta
import httpx
import asyncio
import logging
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models import Service, ServiceStats
from app.api.models.service import AggregatedStats
from typing import List, Dict, Tuple
from sqlalchemy import func
from uuid import UUID
from app.core.notifications import send_service_notification

logger = logging.getLogger(__name__)

# Configuration des constantes
MAX_CONCURRENT_REQUESTS = 20  # Limite de requêtes simultanées
REQUEST_TIMEOUT = 10.0  # Timeout en secondes
BATCH_SIZE = 50  # Nombre de services traités par lot

async def ping_service(service: Service) -> tuple[bool, float | None]:
    """Ping a service and return its status and response time."""
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            start_time = datetime.utcnow()
            response = await client.get(str(service.url))
            end_time = datetime.utcnow()
            
            response_time = (end_time - start_time).total_seconds() * 1000
            return response.status_code < 400, response_time
    except Exception as e:
        logger.error(f"Error pinging service {service.name}: {str(e)}")
        return False, None

async def process_service_batch(services: List[Service], semaphore: asyncio.Semaphore, db: Session) -> List[ServiceStats]:
    """Process a batch of services concurrently with rate limiting."""
    async def process_single_service(service: Service) -> ServiceStats:
        async with semaphore:
            previous_stat = db.query(ServiceStats)\
                .filter(ServiceStats.service_id == service.id)\
                .order_by(ServiceStats.ping_date.desc())\
                .first()
            status, response_time = await ping_service(service)
            
            new_stat = ServiceStats(
                service_id=service.id,
                status=status,
                response_time=response_time,
                ping_date=datetime.utcnow()
            )

            await send_service_notification(
                db,
                service.name,
                not status,  # is_down
                new_stat,
                previous_stat,
                service.notification_preferences,
            )

            return new_stat

    # Traite les services en parallèle avec le sémaphore
    tasks = [process_single_service(service) for service in services]
    return await asyncio.gather(*tasks, return_exceptions=True)

async def check_services(db: Session) -> None:
    """Check all services that need to be monitored based on their frequency."""
    try:
        # Récupère tous les services qui doivent être vérifiés
        services_to_check = []
        services = db.query(Service).all()
        
        current_time = datetime.utcnow()
        for service in services:
            last_stat = db.query(ServiceStats)\
                .filter(ServiceStats.service_id == service.id)\
                .order_by(ServiceStats.ping_date.desc())\
                .first()
            
            if should_check_service(service, last_stat, current_time):
                services_to_check.append(service)

        if not services_to_check:
            logger.info("No services need checking at this time")
            return

        # Crée un sémaphore pour limiter les requêtes concurrentes
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
        
        # Traite les services par lots
        for i in range(0, len(services_to_check), BATCH_SIZE):
            batch = services_to_check[i:i + BATCH_SIZE]
            results = await process_service_batch(batch, semaphore, db)
            
            # Filtre les résultats valides et les ajoute à la base de données
            valid_stats = [r for r in results if isinstance(r, ServiceStats)]
            db.bulk_save_objects(valid_stats)
            db.commit()
            
            logger.info(f"Processed batch of {len(valid_stats)} services")
            
            # Petit délai entre les lots pour éviter la surcharge
            if i + BATCH_SIZE < len(services_to_check):
                await asyncio.sleep(1)

    except Exception as e:
        logger.error(f"Error in check_services: {str(e)}")
        db.rollback()
        raise
    finally:
        logger.info(f"Finished checking {len(services_to_check)} services")

def should_check_service(service: Service, last_stat: ServiceStats, current_time: datetime) -> bool:
    """Determine if a service should be checked based on its frequency."""
    if not last_stat:
        return True
        
    frequency_minutes = {
        "1 minute": 1,
        "10 minutes": 10,
        "1 hour": 60
    }.get(service.refresh_frequency, 60)
    
    next_check = last_stat.ping_date + timedelta(minutes=frequency_minutes)
    return current_time >= next_check

async def monitor_loop():
    """Main monitoring loop that runs continuously."""
    while True:
        try:
            db = SessionLocal()
            await check_services(db)
        except Exception as e:
            logger.error(f"Error in monitor loop: {str(e)}")
        finally:
            db.close()
        
        # Wait for 1 minute before next iteration
        await asyncio.sleep(60) 

def calculate_period_stats(db: Session, service_id: UUID, start_time: datetime, period: str) -> AggregatedStats:
    stats = db.query(ServiceStats)\
        .filter(ServiceStats.service_id == service_id)\
        .filter(ServiceStats.ping_date >= start_time)\
        .order_by(ServiceStats.ping_date.desc())\
        .all()

    if not stats:
        return AggregatedStats(
            period=period,
            uptime_percentage=0,
            avg_response_time=0,
            status_counts={"up": 0, "down": 0},
            timestamps=[],
            response_times=[]
        )

    aggregated_data = {}
    if period == "1h":
        # Agrégation par 10 minutes exactes
        for stat in stats:
            # Arrondir à la tranche de 10 minutes inférieure
            minute = (stat.ping_date.minute // 10) * 10
            ten_min_key = stat.ping_date.replace(
                minute=minute, 
                second=0, 
                microsecond=0
            )
            if ten_min_key not in aggregated_data:
                aggregated_data[ten_min_key] = {"up": 0, "down": 0, "response_times": []}
            
            if stat.response_time is not None:
                aggregated_data[ten_min_key]["response_times"].append(stat.response_time)
            if stat.status:
                aggregated_data[ten_min_key]["up"] += 1
            else:
                aggregated_data[ten_min_key]["down"] += 1
    elif period == "24h":
        # Garder les données individuelles pour le test sequence
        for stat in stats:
            stat_time = stat.ping_date
            if stat_time not in aggregated_data:
                aggregated_data[stat_time] = {"up": 0, "down": 0, "response_times": []}
            
            if stat.response_time is not None:
                aggregated_data[stat_time]["response_times"].append(stat.response_time)
            if stat.status:
                aggregated_data[stat_time]["up"] += 1
            else:
                aggregated_data[stat_time]["down"] += 1
    else:
        # Code existant pour 7d et 30d
        for stat in stats:
            day_key = stat.ping_date.replace(hour=0, minute=0, second=0, microsecond=0)
            if day_key not in aggregated_data:
                aggregated_data[day_key] = {"up": 0, "down": 0, "response_times": []}
            
            if stat.response_time is not None:
                aggregated_data[day_key]["response_times"].append(stat.response_time)
            if stat.status:
                aggregated_data[day_key]["up"] += 1
            else:
                aggregated_data[day_key]["down"] += 1

    # Calcul des statistiques finales
    total_up = sum(period_data["up"] for period_data in aggregated_data.values())
    total_down = sum(period_data["down"] for period_data in aggregated_data.values())
    total_checks = total_up + total_down

    all_response_times = [rt for period_data in aggregated_data.values() 
                         for rt in period_data["response_times"] if rt is not None]

    return AggregatedStats(
        period=period,
        uptime_percentage=round((total_up / total_checks * 100) if total_checks > 0 else 0, 2),
        avg_response_time=round(sum(all_response_times) / len(all_response_times) if all_response_times else 0, 2),
        status_counts={"up": total_up, "down": total_down},
        timestamps=sorted(aggregated_data.keys()),
        response_times=[round(sum(data["response_times"]) / len(data["response_times"]), 2) 
                       if data["response_times"] else 0 
                       for data in [aggregated_data[ts] for ts in sorted(aggregated_data.keys())]]
    ) 