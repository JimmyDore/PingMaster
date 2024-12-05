import pytest
from uuid import uuid4
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models import RefreshFrequency, Service, NotificationPreference, NotificationMethod, AlertFrequency

@pytest.fixture
def test_service(test_db: Session, test_user):
    """Crée un service de test"""
    service = Service(
        id=uuid4(),
        name="Test Service",
        url="https://test.com",
        user_id=test_user.id,
        refresh_frequency=RefreshFrequency.ONE_MINUTE,
    )
    test_db.add(service)
    test_db.commit()
    test_db.refresh(service)
    return service

@pytest.fixture
def test_notification(test_db: Session, test_service):
    """Crée une préférence de notification de test"""
    notification = NotificationPreference(
        service_id=test_service.id,
        notification_method=NotificationMethod.SLACK,
        alert_frequency=AlertFrequency.DAILY,
        webhook_url="https://hooks.slack.com/test",
        notify_on_recovery=True
    )
    test_db.add(notification)
    test_db.commit()
    return notification

def test_create_notification_preference(client: TestClient, test_db: Session, test_service, auth_headers):
    """Test la création d'une préférence de notification"""
    # Refresh the service to ensure it's attached to the session
    test_db.refresh(test_service)
    
    payload = {
        "service_id": str(test_service.id),
        "notification_method": "slack",
        "alert_frequency": "daily",
        "webhook_url": "https://hooks.slack.com/test",
        "notify_on_recovery": True
    }

    response = client.post(
        f"/api/services/{test_service.id}/notifications",
        json=payload,
        headers=auth_headers
    )

    assert response.status_code == 201
    data = response.json()
    assert data["service_id"] == str(test_service.id)
    assert data["notification_method"] == "slack"
    assert data["alert_frequency"] == "daily"
    assert data["webhook_url"] == "https://hooks.slack.com/test"
    assert data["notify_on_recovery"] is True

def test_create_notification_invalid_service(client: TestClient, auth_headers):
    """Test la création d'une notification pour un service inexistant"""
    payload = {
        "service_id": str(uuid4()),
        "notification_method": "slack",
        "alert_frequency": "daily",
        "webhook_url": "https://hooks.slack.com/test"
    }

    response = client.post(
        f"/api/services/{uuid4()}/notifications",
        json=payload,
        headers=auth_headers
    )

    assert response.status_code == 404
    assert "Service not found" in response.json()["detail"]

def test_update_notification_preference(client: TestClient, test_notification, test_service, auth_headers):
    """Test la mise à jour d'une préférence de notification"""
    payload = {
        "service_id": str(test_service.id),
        "notification_method": "slack",
        "alert_frequency": "always",  # Changed from daily
        "webhook_url": "https://hooks.slack.com/updated",
        "notify_on_recovery": False  # Changed from true
    }

    response = client.put(
        f"/api/services/{test_service.id}/notifications",
        json=payload,
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["alert_frequency"] == "always"
    assert data["webhook_url"] == "https://hooks.slack.com/updated"
    assert data["notify_on_recovery"] is False

def test_get_service_with_notification(client: TestClient, test_service, test_notification, auth_headers):
    """Test que le service inclut ses préférences de notification lors du fetch"""
    response = client.get(
        f"/api/services/",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    service = next(s for s in data if s["id"] == str(test_service.id))
    assert "notification_preferences" in service
    notification = service["notification_preferences"]
    assert notification["service_id"] == str(test_service.id)
    assert notification["notification_method"] == "slack"
    assert notification["alert_frequency"] == "daily"

def test_get_services_list_with_notifications(client: TestClient, test_service, test_notification, auth_headers):
    """Test que la liste des services inclut les préférences de notification"""
    response = client.get("/api/services/", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    
    service = next(s for s in data if s["id"] == str(test_service.id))
    assert "notification_preferences" in service
    notification = service["notification_preferences"]
    assert notification["service_id"] == str(test_service.id)
    assert notification["notification_method"] == "slack"

def test_delete_notification_preference(client: TestClient, test_notification, test_service, auth_headers):
    """Test la suppression d'une préférence de notification"""
    response = client.delete(
        f"/api/services/{test_service.id}/notifications",
        headers=auth_headers
    )

    assert response.status_code == 204
    
    # Verify the notification was deleted
    response = client.get(
        f"/api/services/{test_service.id}/notifications",
        headers=auth_headers
    )
    assert response.status_code == 404
    assert "No notification preferences found" in response.json()["detail"]

def test_delete_notification_invalid_service(client: TestClient, auth_headers):
    """Test la suppression d'une notification pour un service inexistant"""
    response = client.delete(
        f"/api/services/{uuid4()}/notifications",
        headers=auth_headers
    )

    assert response.status_code == 404
    assert "Service not found" in response.json()["detail"]
  