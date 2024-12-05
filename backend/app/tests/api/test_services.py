import pytest
from uuid import UUID, uuid4
from fastapi.testclient import TestClient
from app.main import app
from app.db.models import RefreshFrequency, Service, ServiceStats
from sqlalchemy.orm import Session
from uuid import uuid4
from datetime import datetime, timedelta

from app.core.auth import get_user_id_from_headers

def test_create_service(client: TestClient, auth_headers: dict):
    response = client.post(
        "/api/services/",
        headers=auth_headers,
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
    assert str(data["user_id"]) == str(get_user_id_from_headers(auth_headers))
    assert data["refresh_frequency"] == RefreshFrequency.ONE_HOUR.value

def test_create_service_invalid_url(client: TestClient, auth_headers: dict):
    response = client.post(
        "/api/services/",
        headers=auth_headers,
        json={
            "name": "Test Service",
            "url": "not-a-url",
            "refresh_frequency": RefreshFrequency.ONE_HOUR
        }
    )
    assert response.status_code == 422

def test_create_service_invalid_data(client: TestClient, auth_headers: dict):
    response = client.post(
        "/api/services/",
        headers=auth_headers,
        json={}
    )
    assert response.status_code == 422

client = TestClient(app)

def test_get_services_with_stats(client: TestClient, test_db: Session, auth_headers: dict):
    # Créer un service de test
    service = client.post(
        "/api/services/",
        headers=auth_headers,
        json={
            "name": "Test Service",
            "url": "https://example.com",
            "refresh_frequency": RefreshFrequency.ONE_HOUR
        }
    )
    
    service_stats = client.post(
        f"/api/services/{service.json()['id']}/stats/",
        headers=auth_headers,
        json={
            "service_id": service.json()["id"],
            "status": True,
            "response_time": 200.0,
            "ping_date": datetime.utcnow().isoformat()
        }
    )
    
    # Appeler l'endpoint pour récupérer les services
    response = client.get("/api/services/", headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Test Service"
    assert data[0]["url"] == "https://example.com/"
    assert len(data[0]["stats"]) == 1
    assert data[0]["stats"][0]["status"] is True
    assert data[0]["stats"][0]["response_time"] == 200.0

def test_get_services_without_stats(client: TestClient, auth_headers: dict):
    # Créer un service de test sans stats
    client.post(
        "/api/services/",
        headers=auth_headers,
        json={
            "name": "Test Service No Stats",
            "url": "https://example.org",
            "refresh_frequency": RefreshFrequency.ONE_HOUR
        }
    )
    
    # Appeler l'endpoint pour récupérer les services
    response = client.get("/api/services/", headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Test Service No Stats"
    assert data[0]["url"] == "https://example.org/"
    assert len(data[0]["stats"]) == 0

def test_create_service_stats(client: TestClient, auth_headers: dict):
    # Create a test service first
    service_response = client.post(
        "/api/services/",
        headers=auth_headers,
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
        headers=auth_headers,
        json={
            "service_id": service_id,
            "status": True,
            "response_time": 200.5,
            "ping_date": datetime.utcnow().isoformat()
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["status"] is True
    assert data["response_time"] == 200.5
    assert "ping_date" in data

def test_create_service_stats_invalid_service(client: TestClient, auth_headers: dict):
    invalid_id = str(uuid4())
    response = client.post(
        f"/api/services/{invalid_id}/stats/",
        headers=auth_headers,
        json={
            "service_id": invalid_id,
            "status": True,
            "response_time": 200.5,
            "ping_date": datetime.utcnow().isoformat()
        }
    )
    assert response.status_code == 404

def test_get_services_with_multiple_stats(client: TestClient, test_db: Session, auth_headers: dict):
    # Créer un service de test
    service_response = client.post(
        "/api/services/",
        headers=auth_headers,
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
        headers=auth_headers,
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
        headers=auth_headers,
        json={
            "service_id": service_id,
            "status": False,
            "response_time": 200.0,
            "ping_date": newer_date.isoformat()
        }
    )
    
    # Récupérer les services avec leurs stats
    response = client.get("/api/services/", headers=auth_headers)
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

def test_delete_service(client: TestClient, auth_headers: dict):
    # Create a test service first
    service_response = client.post(
        "/api/services/",
        headers=auth_headers,
        json={
            "name": "Test Service",
            "url": "https://example.com",
            "refresh_frequency": RefreshFrequency.ONE_HOUR
        }
    )
    assert service_response.status_code == 201
    service_id = service_response.json()["id"]
    
    # Delete the service
    delete_response = client.delete(
        f"/api/services/{service_id}",
        headers=auth_headers
    )
    assert delete_response.status_code == 204
    
    # Verify service is deleted
    get_response = client.get("/api/services/", headers=auth_headers)
    assert get_response.status_code == 200
    assert len(get_response.json()) == 0

def test_delete_nonexistent_service(client: TestClient, auth_headers: dict):
    response = client.delete(
        f"/api/services/{uuid4()}",
        headers=auth_headers
    )
    assert response.status_code == 404

@pytest.fixture
def test_service_with_api_stats(client, auth_headers):
    """Fixture qui crée un service et ses stats via l'API"""
    service_response = client.post(
        "/api/services/",
        json={
            "name": "Test Service",
            "url": "https://example.com",
            "refresh_frequency": RefreshFrequency.ONE_MINUTE,
        },
        headers=auth_headers
    )
    assert service_response.status_code == 201
    service_id = service_response.json()["id"]

    base_time = datetime.utcnow()
    
    # Création des stats sur les 30 derniers jours (mais pas les dernières 24h)
    for i in range(2, 30):  # Commence à 2 jours pour éviter le chevauchement
        client.post(
            f"/api/services/{service_id}/stats/",
            json={
                "service_id": service_id,
                "status": i % 6 != 0,  # ~83% uptime
                "response_time": 200 + i,
                "ping_date": (base_time - timedelta(days=i)).isoformat()
            },
            headers=auth_headers
        )

    # Création des stats sur les 7 derniers jours (mais pas les dernières 24h)
    for i in range(2, 7):  # Commence à 2 jours pour éviter le chevauchement
        client.post(
            f"/api/services/{service_id}/stats/",
            json={
                "service_id": service_id,
                "status": i % 5 != 0,  # 80% uptime
                "response_time": 150 + i,
                "ping_date": (base_time - timedelta(days=i, hours=12)).isoformat()
            },
            headers=auth_headers
        )

    # Création des stats sur les dernières 24h uniquement
    for i in range(24):
        client.post(
            f"/api/services/{service_id}/stats/",
            json={
                "service_id": service_id,
                "status": i % 4 != 0,  # 75% uptime
                "response_time": 100 + i * 2,
                "ping_date": (base_time - timedelta(hours=i)).isoformat()
            },
            headers=auth_headers
        )

    return service_id

def test_get_service_stats_aggregated_via_api(client, test_service_with_api_stats, auth_headers):
    """Test la récupération des statistiques agrégées via l'API"""
    response = client.get(f"/api/services/{test_service_with_api_stats}/stats/aggregated", headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    
    # Vérification de la structure
    assert "stats_24h" in data
    assert "stats_7d" in data
    assert "stats_30d" in data
    
    # Vérification des statistiques 24h
    stats_24h = data["stats_24h"]
    assert 70 <= stats_24h["uptime_percentage"] <= 80  # ~75% uptime
    assert 100 <= stats_24h["avg_response_time"] <= 150  # Ajusté pour les nouvelles valeurs
    assert len(stats_24h["timestamps"]) > 0
    assert len(stats_24h["response_times"]) > 0
    
    # Vérification des statistiques 7j
    stats_7d = data["stats_7d"]
    assert 75 <= stats_7d["uptime_percentage"] <= 85  # ~80% uptime
    assert 130 <= stats_7d["avg_response_time"] <= 180  # Ajusté pour les nouvelles valeurs
    assert stats_7d["status_counts"]["up"] > 0
    assert stats_7d["status_counts"]["down"] > 0
    
    # Vérification des statistiques 30j
    stats_30d = data["stats_30d"]
    assert 80 <= stats_30d["uptime_percentage"] <= 90  # ~83% uptime
    assert 150 <= stats_30d["avg_response_time"] <= 250  # Ajusté pour les nouvelles valeurs
    assert stats_30d["status_counts"]["up"] > 0
    assert stats_30d["status_counts"]["down"] > 0

def test_create_and_get_service_stats_sequence(client: TestClient, auth_headers: dict):
    """Test la création séquentielle de stats et leur récupération"""
    # Création du service
    service_response = client.post(
        "/api/services/",
        headers=auth_headers,
        json={
            "name": "Sequential Test Service",
            "url": "https://example.com",
            "refresh_frequency": RefreshFrequency.ONE_MINUTE
        }
    )
    service_id = service_response.json()["id"]

    # Création de 5 stats avec des états alternés
    base_time = datetime.utcnow()
    expected_states = []
    
    for i in range(5):
        is_up = i % 2 == 0
        expected_states.append(is_up)
        
        response = client.post(
            f"/api/services/{service_id}/stats/",
            headers=auth_headers,
            json={
                "service_id": service_id,
                "status": is_up,
                "response_time": 100 + i * 10,
                "ping_date": (base_time - timedelta(minutes=i*5)).isoformat()
            }
        )
        assert response.status_code == 201

    # Vérification des stats agrégées
    stats_response = client.get(
        f"/api/services/{service_id}/stats/aggregated",
        headers=auth_headers
    )
    assert stats_response.status_code == 200
    
    data = stats_response.json()
    stats_24h = data["stats_24h"]
    
    # Vérification du nombre de stats
    assert len(stats_24h["timestamps"]) == 5
    
    # Vérification de l'uptime (3 up sur 5 = 60%)
    assert abs(stats_24h["uptime_percentage"] - 60) <= 1
    
    # Vérification des compteurs de status
    assert stats_24h["status_counts"]["up"] == 3
    assert stats_24h["status_counts"]["down"] == 2

def test_create_service_stats_invalid_data(client, auth_headers):
    """Test la création de stats avec des données invalides"""
    # Création du service
    service_response = client.post(
        "/api/services/",
        json={
            "name": "Invalid Stats Test Service",
            "url": "https://example.com",
            "refresh_frequency": RefreshFrequency.ONE_MINUTE
        },
        headers=auth_headers
    )
    service_id = service_response.json()["id"]

    # Test avec response_time négatif
    response = client.post(
        f"/api/services/{service_id}/stats/",
        json={
            "service_id": service_id,
            "status": True,
            "response_time": -100,
            "ping_date": datetime.utcnow().isoformat()
        },
        headers=auth_headers
    )
    assert response.status_code == 422

    # Test avec une date future
    response = client.post(
        f"/api/services/{service_id}/stats/",
        json={
            "service_id": service_id,
            "status": True,
            "response_time": 100,
            "ping_date": (datetime.utcnow() + timedelta(days=1)).isoformat()
        },
        headers=auth_headers
    )
    assert response.status_code == 422

    # Test avec un service_id invalide
    response = client.post(
        f"/api/services/{uuid4()}/stats/",
        json={
            "service_id": str(uuid4()),
            "status": True,
            "response_time": 100,
            "ping_date": datetime.utcnow().isoformat()
        },
        headers=auth_headers
    )
    assert response.status_code == 404

def test_get_service_stats_1h_aggregation(client, auth_headers):
    """Test l'agrégation des statistiques sur 1 heure"""
    # Création du service
    service_response = client.post(
        "/api/services/",
        json={
            "name": "1h Test Service",
            "url": "https://example.com",
            "refresh_frequency": RefreshFrequency.ONE_MINUTE
        },
        headers=auth_headers
    )
    service_id = service_response.json()["id"]
    
    # Création de stats pour chaque minute de la dernière heure
    base_time = datetime.utcnow()
    for i in range(60):
        client.post(
            f"/api/services/{service_id}/stats/",
            json={
                "service_id": service_id,
                "status": i % 3 != 0,  # 66% uptime
                "response_time": 100 + i,
                "ping_date": (base_time - timedelta(minutes=i)).isoformat()
            },
            headers=auth_headers
        )

    # Vérification des stats agrégées
    response = client.get(f"/api/services/{service_id}/stats/aggregated", headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    stats_1h = data["stats_1h"]
    
    assert len(stats_1h["timestamps"]) == 7
    assert len(stats_1h["response_times"]) == 7
    
    # Vérification de l'uptime (~66%)
    assert 60 <= stats_1h["uptime_percentage"] <= 70
    
    # Vérification des compteurs de status
    total_checks = stats_1h["status_counts"]["up"] + stats_1h["status_counts"]["down"]
    assert total_checks > 0

# Add new auth-specific test cases
def test_unauthorized_access(client: TestClient, auth_headers: dict):
    """Test that endpoints require authentication"""
    endpoints = [
        ("GET", "/api/services/"),
        ("POST", "/api/services/"),
        ("DELETE", f"/api/services/{uuid4()}"),
        ("POST", f"/api/services/{uuid4()}/stats/"),
        ("GET", f"/api/services/{uuid4()}/stats/aggregated"),
    ]
    
    for method, endpoint in endpoints:
        response = client.request(method, endpoint)
        assert response.status_code == 401, f"Endpoint {method} {endpoint} should require authentication"

def test_service_isolation(client: TestClient, auth_headers: dict, auth_headers2: dict):
    """Test that users can't access each other's services"""
    # Create service with first user
    service_response = client.post(
        "/api/services/",
        headers=auth_headers,
        json={
            "name": "User1 Service",
            "url": "https://example.com",
            "refresh_frequency": RefreshFrequency.ONE_HOUR
        }
    )
    service_id = service_response.json()["id"]
    
    # Try to access with second user
    response = client.get(f"/api/services/{service_id}/stats/aggregated", headers=auth_headers2)
    assert response.status_code == 404