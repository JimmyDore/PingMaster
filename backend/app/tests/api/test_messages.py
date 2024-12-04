from fastapi.testclient import TestClient

def test_create_message(client: TestClient):
    response = client.post(
        "/api/messages/",
        json={"content": "Test message"}
    )
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["content"] == "Test message" 