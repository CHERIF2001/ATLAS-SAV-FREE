import time
from fastapi.testclient import TestClient
from app.main import app
from app.core.ratelimit import ticket_limiter

client = TestClient(app)

def test_rate_limit_tickets():
    # Reset limiter for this test IP (mocked usually, but here we use local)
    # Note: TestClient uses "testclient" as host or similar, so we need to be careful.
    # For simplicity, we just try to hit the limit.
    
    # Clear previous limits
    ticket_limiter.requests.clear()
    
    # Limit is 5 per hour. Let's try to create 6.
    for i in range(5):
        response = client.post(
            "/public/tickets/",
            json={"initial_message": f"Spam {i}", "channel": "chat"}
        )
        assert response.status_code == 200
        
    # The 6th one should fail
    response = client.post(
        "/public/tickets/",
        json={"initial_message": "Spam 6", "channel": "chat"}
    )
    assert response.status_code == 429
    assert "Trop de tickets" in response.json()["detail"]
