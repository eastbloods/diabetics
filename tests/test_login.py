from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_login():
    client.post("/auth/register", json={
        "email": "adam@mail.com",
        "password": "pass",
        "name": "East",
        "surname": "Chamb",
        "age": 28,
        "diabetes_type": "1",
        "height_cm": 190,
        "weight_kg": 99
    })

    response = client.post("auth/login", json={
        "email": "adam@mail.com",
        "password": "pass"
    })

    assert response.status_code == 200
    assert response.json()["access_token"]

def test_wrong_input():
    response = client.post("auth/login", json={
        "email": "adam@mail.com",
        "password": "pass12"
    })

    assert response.status_code == 401
