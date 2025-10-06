import pytest
from fastapi.testclient import TestClient
from presentation.api.app import app


@pytest.fixture
def client():
    return TestClient(app)


def test_login_invalid_credentials(client):
    response = client.post(
        "/admin/login", json={"email": "nope@example.com", "secret": "wrong-secret"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"


def test_me_unauthenticated(client):
    response = client.get("/admin/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "unauthorized"


def test_list_tenants_unauthenticated(client):
    response = client.get("/admin/tenants")
    assert response.status_code == 401
    assert response.json()["detail"] == "unauthorized"


def test_create_tenant_unauthenticated(client):
    response = client.post("/admin/tenants", json={"name": "Test Tenant"})
    assert response.status_code == 401
    assert response.json()["detail"] == "unauthorized"
