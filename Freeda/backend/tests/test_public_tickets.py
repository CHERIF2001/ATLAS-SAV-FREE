from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_ticket_public():
    response = client.post(
        "/public/tickets/",
        json={"initial_message": "Test message", "channel": "chat"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "ticket_id" in data
    assert data["ticket_id"].startswith("FRE-")

def test_get_ticket_public():
    # 1. Create ticket
    create_response = client.post(
        "/public/tickets/",
        json={"initial_message": "Test message", "channel": "chat"}
    )
    ticket_id = create_response.json()["ticket_id"]
    
    # 2. Get ticket
    response = client.get(f"/public/tickets/{ticket_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["ticket_id"] == ticket_id
    assert data["status"] == "nouveau"

def test_smart_reply_integration():
    # Test a message that should trigger a smart reply (no AI call)
    response = client.post(
        "/public/tickets/",
        json={"initial_message": "Bonjour", "channel": "chat"}
    )
    assert response.status_code == 200
    data = response.json()
    # Check if we got an assistant message
    assert "assistant_message" in data
    # "Bonjour" usually triggers a greeting
    assert "Bonjour" in data["assistant_message"]["content"]
