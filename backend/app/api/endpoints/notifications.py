from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import NotificationPreference, Service, User
from app.api.models.notification import NotificationPreferenceCreate, NotificationPreferenceResponse
from app.core.auth import get_current_user
from app.core.url_safety import UnsafeURLError, assert_public_url_async
from uuid import UUID

router = APIRouter()

@router.post("/services/{service_id}/notifications", response_model=NotificationPreferenceResponse, status_code=201)
async def create_notification_preference(
    service_id: UUID,
    preference: NotificationPreferenceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Vérifier que le service appartient à l'utilisateur
    service = db.query(Service)\
        .filter(Service.id == service_id, Service.user_id == current_user.id)\
        .first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    try:
        await assert_public_url_async(preference.webhook_url)
    except UnsafeURLError as e:
        raise HTTPException(status_code=400, detail=f"Invalid webhook URL: {str(e)}")

    # Le service_id du body est ignoré : seul celui du chemin (dont la propriété est vérifiée) fait foi
    preference_data = preference.model_dump(exclude={"service_id"})

    # Créer ou mettre à jour les préférences
    db_preference = db.query(NotificationPreference)\
        .filter(NotificationPreference.service_id == service_id)\
        .first()
        
    if db_preference:
        for key, value in preference_data.items():
            setattr(db_preference, key, value)
    else:
        db_preference = NotificationPreference(service_id=service_id, **preference_data)
        db.add(db_preference)
        
    db.commit()
    db.refresh(db_preference)
    return db_preference

@router.put("/services/{service_id}/notifications", response_model=NotificationPreferenceResponse, status_code=200)
async def update_notification_preference(
    service_id: UUID,
    preference: NotificationPreferenceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return await create_notification_preference(service_id, preference, current_user, db)

@router.get("/services/{service_id}/notifications", response_model=NotificationPreferenceResponse)
async def get_notification_preference(
    service_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Vérifier que le service appartient à l'utilisateur
    service = db.query(Service)\
        .filter(Service.id == service_id, Service.user_id == current_user.id)\
        .first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    preference = db.query(NotificationPreference)\
        .filter(NotificationPreference.service_id == service_id)\
        .first()
    if not preference:
        raise HTTPException(status_code=404, detail="No notification preferences found")
        
    return preference 

@router.delete("/services/{service_id}/notifications", status_code=204)
async def delete_notification_preference(
    service_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Vérifier que le service appartient à l'utilisateur
    service = db.query(Service)\
        .filter(Service.id == service_id, Service.user_id == current_user.id)\
        .first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    # Supprimer les préférences de notification
    result = db.query(NotificationPreference)\
        .filter(NotificationPreference.service_id == service_id)\
        .delete()
    
    if result == 0:
        raise HTTPException(status_code=404, detail="No notification preferences found")
        
    db.commit()
    return None 