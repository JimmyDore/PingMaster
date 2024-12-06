import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.models import User
from sqlalchemy.orm import Session

def test_sign_up_success(client: TestClient):
    response = client.post(
        "/api/auth/sign-up",
        json={
            "username": "newuser@example.com",
            "password": "testpassword123"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_sign_up_duplicate_username(client: TestClient, test_user):
    response = client.post(
        "/api/auth/sign-up",
        json={
            "username": "testuser@example.com",  # Same username as test_user fixture
            "password": "testpassword123"
        }
    )
    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]

def test_sign_in_success(client: TestClient, test_user):
    response = client.post(
        "/api/auth/sign-in",
        json={
            "username": "testuser@example.com",
            "password": "testpass"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_sign_in_invalid_credentials(client: TestClient):
    response = client.post(
        "/api/auth/sign-in",
        json={
            "username": "nonexistent@example.com",
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]

def test_sign_up_invalid_email(client: TestClient):
    response = client.post(
        "/api/auth/sign-up",
        json={"username": "invalidemail", "password": "testpassword123"}
    )
    assert response.status_code == 400

def test_access_services_with_token(client: TestClient):
    # First, create a new user and get token
    signup_response = client.post(
        "/api/auth/sign-up",
        json={
            "username": "serviceuser@example.com",
            "password": "testpassword123"
        }
    )
    assert signup_response.status_code == 201
    token = signup_response.json()["access_token"]
    
    # Try to access services with the token
    services_response = client.get(
        "/api/services/",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert services_response.status_code == 200
    assert isinstance(services_response.json(), list)

def test_access_services_without_token(client: TestClient):
    response = client.get("/api/services/")
    assert response.status_code == 401
    assert "Not authenticated" in response.json()["detail"]

def test_access_services_with_invalid_token(client: TestClient):
    response = client.get(
        "/api/services/",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401
    assert "Could not validate credentials" in response.json()["detail"]

def test_get_current_user(client: TestClient):
    # Sign up and get token
    signup_response = client.post(
        "/api/auth/sign-up",
        json={
            "username": "meuser@example.com",
            "password": "testpassword123"
        }
    )
    token = signup_response.json()["access_token"]
    
    # Get current user info
    me_response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert me_response.status_code == 200
    user_data = me_response.json()
    assert user_data["username"] == "meuser@example.com"
    assert "id" in user_data
    assert "created_at" in user_data 