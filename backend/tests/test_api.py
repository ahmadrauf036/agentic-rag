from fastapi.testclient import TestClient
from main import app
import pytest
client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "active"}


def test_ingestion_validation_rejects_empty_list():
    response = client.post("/ingestion", json={"file_path": []})
    assert response.status_code == 422  # Pydantic validation error


@pytest.mark.integration
def test_ingestion_endpoint_success():
    response = client.post("/ingestion", json={"file_path": ["data/sample.txt"]})
    assert response.status_code == 201
    assert response.json()["success"] is True