import os

TEST_ADMIN_SECRET = "test-admin-secret-1234567890"
TEST_ENCRYPTION_KEY = "D_Jhyl9DGCCyOLU_qTzw3CSLinmvglzsXDbNSsmw24w="

os.environ.setdefault("TESTING", "true")
os.environ.setdefault("ADMIN_EMAIL", "admin@example.com")
os.environ.setdefault("ADMIN_SECRET", TEST_ADMIN_SECRET)
os.environ.setdefault("ENCRYPTION_KEY", TEST_ENCRYPTION_KEY)

import pytest
from fastapi.testclient import TestClient
from presentation.api.app import app
from infra.repos import settings_factory, tenant_rules_factory


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_tenant_id():
    return "test-tenant-123"


def _login(client: TestClient):
    """Login as admin for testing."""
    r = client.post(
        "/admin/login",
        json={"email": "admin@example.com", "secret": TEST_ADMIN_SECRET},
    )
    assert r.status_code == 200
    return r


def test_get_config_not_found(client, mock_tenant_id):
    """Test getting config for non-existent tenant returns 404."""
    _login(client)
    response = client.get(f"/admin/tenants/{mock_tenant_id}/config")
    assert response.status_code == 404
    assert response.json()["detail"] == "tenant_not_found"


def test_put_config_not_found(client, mock_tenant_id):
    """Test putting config for non-existent tenant returns 404."""
    _login(client)
    response = client.put(
        f"/admin/tenants/{mock_tenant_id}/config",
        json={"yaml": "test: config"}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "tenant_not_found"


def test_config_round_trip(client):
    """Test config save and retrieve round trip."""
    _login(client)
    
    # Create a tenant first
    tenant_repo = tenant_rules_factory.tenants_repo()
    tenant_id = tenant_repo.create("Test Tenant")
    
    try:
        # Save config
        test_yaml = """
features:
  sessions_value: true
notion:
  tasks:
    db_id: "tasks_123"
    props:
      title: "Name"
  clients:
    db_id: "clients_123"
    props:
      title: "Name"
  sessions:
    db_id: "sessions_123"
    props:
      title: "Title"
"""
        
        response = client.put(
            f"/admin/tenants/{tenant_id}/config",
            json={"yaml": test_yaml}
        )
        assert response.status_code == 200
        assert response.json()["ok"] is True
        
        # Retrieve config
        response = client.get(f"/admin/tenants/{tenant_id}/config")
        assert response.status_code == 200
        assert "yaml" in response.json()
        assert "sessions_value: true" in response.json()["yaml"]
        assert "tasks_123" in response.json()["yaml"]
        
    finally:
        # Cleanup - delete tenant
        pass  # Tenant cleanup handled by test framework


def test_config_invalid_yaml(client):
    """Test that invalid YAML returns 400."""
    _login(client)
    
    # Create a tenant first
    tenant_repo = tenant_rules_factory.tenants_repo()
    tenant_id = tenant_repo.create("Test Tenant")
    
    try:
        # Try to save invalid YAML
        response = client.put(
            f"/admin/tenants/{tenant_id}/config",
            json={"yaml": "invalid: yaml: content: ["}
        )
        assert response.status_code == 400
        assert "invalid_yaml" in response.json()["detail"]
        
    finally:
        # Cleanup
        pass


def test_config_missing_required_fields(client):
    """Test that config missing required fields returns 400."""
    _login(client)
    
    # Create a tenant first
    tenant_repo = tenant_rules_factory.tenants_repo()
    tenant_id = tenant_repo.create("Test Tenant")
    
    try:
        # Try to save config missing required notion section
        response = client.put(
            f"/admin/tenants/{tenant_id}/config",
            json={"yaml": "features:\n  sessions_value: true"}
        )
        assert response.status_code == 400
        assert "missing_required:notion" in response.json()["detail"]
        
    finally:
        # Cleanup
        pass


def test_validate_config_no_config(client):
    """Test validation when no config exists."""
    _login(client)
    
    # Create a tenant first
    tenant_repo = tenant_rules_factory.tenants_repo()
    tenant_id = tenant_repo.create("Test Tenant")
    
    try:
        response = client.post(f"/admin/tenants/{tenant_id}/notion/validate")
        assert response.status_code == 200
        assert response.json()["ok"] is False
        assert response.json()["error"] == "no_config_found"
        
    finally:
        # Cleanup
        pass


def test_validate_config_no_connection(client):
    """Test validation when no Notion connection exists."""
    _login(client)
    
    # Create a tenant first
    tenant_repo = tenant_rules_factory.tenants_repo()
    tenant_id = tenant_repo.create("Test Tenant")
    
    # Save a valid config
    test_yaml = """
features:
  sessions_value: true
notion:
  tasks:
    db_id: "tasks_123"
    props:
      title: "Name"
  clients:
    db_id: "clients_123"
    props:
      title: "Name"
  sessions:
    db_id: "sessions_123"
    props:
      title: "Title"
"""
    
    try:
        # Save config
        client.put(f"/admin/tenants/{tenant_id}/config", json={"yaml": test_yaml})
        
        # Try to validate (should fail due to no connection)
        response = client.post(f"/admin/tenants/{tenant_id}/notion/validate")
        assert response.status_code == 200
        assert response.json()["ok"] is False
        assert response.json()["error"] == "no_notion_connection"
        
    finally:
        # Cleanup
        pass
