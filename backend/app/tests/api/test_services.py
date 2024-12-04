import pytest
from uuid import UUID
from fastapi.testclient import TestClient
from app.main import app
from app.api.endpoints.services import MOCK_USER_ID
from app.db.models import RefreshFrequency, Service, ServiceStats
from sqlalchemy.orm import Session
from uuid import uuid4
from datetime import datetime, timedelta

def test_create_service(client: TestClient):
    response = client.post(
        "/api/services/",
        json={
            "name": "Test Service",
            "url": "https://example.com",
            "refresh_frequency": RefreshFrequency.ONE_HOUR
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["name"] == "Test Service"
    assert data["url"] == "https://example.com/"
    assert str(data["user_id"]) == str(MOCK_USER_ID)
    assert data["refresh_frequency"] == RefreshFrequency.ONE_HOUR.value

def test_create_service_invalid_url(client: TestClient):
    response = client.post(
        "/api/services/",
        json={
            "name": "Test Service",
            "url": "not-a-url",
            "refresh_frequency": RefreshFrequency.ONE_HOUR
        }
    )
    assert response.status_code == 422

def test_create_service_invalid_data(client: TestClient):
    response = client.post(
        "/api/services/",
        json={}
    )
    assert response.status_code == 422

client = TestClient(app)

def test_get_services_with_stats(client: TestClient, test_db: Session):
    # Créer un service de test
    service = client.post("/api/services/", json={
        "name": "Test Service",
        "url": "https://example.com",
        "refresh_frequency": RefreshFrequency.ONE_HOUR
    })
    
    service_stats = client.post(f"/api/services/{service.json()['id']}/stats/", json={
        "service_id": service.json()["id"],
        "status": True,
        "response_time": 200.0,
        "ping_date": datetime.utcnow().isoformat()
    })
    
    # Appeler l'endpoint pour récupérer les services
    response = client.get("/api/services/")
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Test Service"
    assert data[0]["url"] == "https://example.com/"
    assert len(data[0]["stats"]) == 1
    assert data[0]["stats"][0]["status"] is True
    assert data[0]["stats"][0]["response_time"] == 200.0

def test_get_services_without_stats(client: TestClient):
    # Créer un service de test sans stats
    client.post("/api/services/", json={
        "name": "Test Service No Stats",
        "url": "https://example.org",
        "refresh_frequency": RefreshFrequency.ONE_HOUR
    })
    
    # Appeler l'endpoint pour récupérer les services
    response = client.get("/api/services/")
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Test Service No Stats"
    assert data[0]["url"] == "https://example.org/"
    assert len(data[0]["stats"]) == 0

def test_create_service_stats(client: TestClient):
    # Create a test service first
    service_response = client.post(
        "/api/services/",
        json={
            "name": "Test Service",
            "url": "https://example.com",
            "refresh_frequency": RefreshFrequency.ONE_HOUR
        }
    )
    service_id = service_response.json()["id"]
    
    # Create stats for the service
    response = client.post(
        f"/api/services/{service_id}/stats/",
        json={
            "service_id": service_id,
            "status": True,
            "response_time": 200.5,
            "ping_date": datetime.utcnow().isoformat()
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] is True
    assert data["response_time"] == 200.5
    assert "ping_date" in data

def test_create_service_stats_invalid_service(client: TestClient):
    invalid_id = str(uuid4())
    response = client.post(
        f"/api/services/{invalid_id}/stats/",
        json={
            "service_id": invalid_id,
            "status": True,
            "response_time": 200.5,
            "ping_date": datetime.utcnow().isoformat()
        }
    )
    assert response.status_code == 404

def test_get_services_with_multiple_stats(client: TestClient, test_db: Session):
    # Créer un service de test
    service_response = client.post(
        "/api/services/",
        json={
            "name": "Test Service",
            "url": "https://example.com",
            "refresh_frequency": RefreshFrequency.ONE_HOUR
        }
    )
    service_id = service_response.json()["id"]
    
    # Créer deux statistiques avec des dates différentes
    older_date = datetime.utcnow() - timedelta(hours=1)
    newer_date = datetime.utcnow()
    
    # Ajouter la statistique plus ancienne
    client.post(
        f"/api/services/{service_id}/stats/",
        json={
            "service_id": service_id,
            "status": True,
            "response_time": 100.0,
            "ping_date": older_date.isoformat()
        }
    )
    
    # Ajouter la statistique plus récente
    client.post(
        f"/api/services/{service_id}/stats/",
        json={
            "service_id": service_id,
            "status": False,
            "response_time": 200.0,
            "ping_date": newer_date.isoformat()
        }
    )
    
    # Récupérer les services avec leurs stats
    response = client.get("/api/services/")
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) == 1
    service_data = data[0]
    
    # Vérifier que les stats sont présentes et triées
    assert len(service_data["stats"]) == 2
    assert service_data["stats"][0]["response_time"] == 200.0  # La plus récente
    assert service_data["stats"][1]["response_time"] == 100.0  # La plus ancienne
    
    # Vérifier l'ordre des dates
    first_date = datetime.fromisoformat(service_data["stats"][0]["ping_date"])
    second_date = datetime.fromisoformat(service_data["stats"][1]["ping_date"])
    assert first_date > second_date