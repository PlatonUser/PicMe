import os

from fastapi.testclient import TestClient


def test_health_check_with_sqlite_database():
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"

    from app.infrastructure.web.app import create_app

    with TestClient(create_app()) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
