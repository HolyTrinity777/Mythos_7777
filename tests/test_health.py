from app import app

def test_health():
    app.config["TESTING"] = True
    client = app.test_client()
    response = client.get("/health")
    assert response.status_code == 200
