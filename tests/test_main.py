from fastapi.testclient import TestClient
from app.main import app   # 👈 IMPORTANT CHANGE

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200