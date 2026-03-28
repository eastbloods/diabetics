from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_register():
    response = client.post("/auth/register", json={
      "email": "east@mail.com",
      "password": "pass",
      "name": "East",
      "surname": "Chamb",
      "age": 28,
      "diabetes_type": "1",
      "height_cm": 190,
      "weight_kg": 99
    })
    assert response.status_code == 200
    assert response.json()["email"]

def test_duplicate():
    response = client.post("/auth/register", json={
        "email": "east@mail.com",
        "password": "pass1234",
        "name": "East",
        "surname": "Chamb",
        "age": 28,
        "diabetes_type": "1",
        "height_cm": 190,
        "weight_kg": 99
    })

    assert response.status_code == 400
