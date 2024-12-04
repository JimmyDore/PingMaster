import pytest
from uuid import UUID
from fastapi.testclient import TestClient
from app.main import app
from app.api.endpoints.services import MOCK_USER_ID
from app.db.models import RefreshFrequency

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