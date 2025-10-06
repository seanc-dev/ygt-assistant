import pytest
import httpx
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from presentation.api.app import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def authenticated_client():
    """Client with mocked admin authentication"""
    from presentation.api.app import _require_admin

    def mock_admin_auth():
        return "admin@example.com"

    app.dependency_overrides[_require_admin] = mock_admin_auth
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


class TestAdminRulesEndpoints:
    """Test admin rules management endpoints"""

    @pytest.fixture
    def admin_session(self):
        """Mock admin session"""
        return "mock_admin_session_token"

    @pytest.fixture
    def tenant_id(self):
        """Sample tenant ID"""
        return "test-tenant-123"

    @pytest.fixture
    def sample_rules_yaml(self):
        """Sample rules YAML content"""
        return """timezone: "Pacific/Auckland"
email_triage:
  - match:
      from: ["*@client.com"]
      subject_has: ["update", "invoice"]
    action: create_task
    fields:
      title: "Send monthly invoice update"
      status: "Next"
      db: "Tasks"
"""

    def test_get_rules_success(self, authenticated_client, admin_session, tenant_id):
        """Test successful retrieval of tenant rules"""
        with patch("presentation.api.app.tenant_rules_factory") as mock_factory:
            mock_rules_repo = MagicMock()
            mock_rules_repo.get_yaml.return_value = "sample: rules"
            mock_factory.rules_repo.return_value = mock_rules_repo

            response = authenticated_client.get(f"/admin/tenants/{tenant_id}/rules")

            assert response.status_code == 200
            data = response.json()
            assert data["yaml"] == "sample: rules"
            mock_rules_repo.get_yaml.assert_called_once_with(tenant_id)

    def test_get_rules_unauthorized(self, client, tenant_id):
        """Test rules retrieval without admin auth"""
        response = client.get(f"/admin/tenants/{tenant_id}/rules")
        assert response.status_code == 401

    def test_set_rules_success(
        self, authenticated_client, admin_session, tenant_id, sample_rules_yaml
    ):
        """Test successful setting of tenant rules"""
        with patch("presentation.api.app.tenant_rules_factory") as mock_factory:
            mock_tenants_repo = MagicMock()
            mock_tenants_repo.exists.return_value = True
            mock_factory.tenants_repo.return_value = mock_tenants_repo

            mock_rules_repo = MagicMock()
            mock_factory.rules_repo.return_value = mock_rules_repo

            response = authenticated_client.put(
                f"/admin/tenants/{tenant_id}/rules",
                json={"yaml_text": sample_rules_yaml},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["ok"] is True
            mock_tenants_repo.exists.assert_called_once_with(tenant_id)
            mock_rules_repo.set_yaml.assert_called_once_with(
                tenant_id, sample_rules_yaml
            )

    def test_set_rules_tenant_not_found(
        self, authenticated_client, admin_session, tenant_id, sample_rules_yaml
    ):
        """Test setting rules for non-existent tenant"""
        with patch("presentation.api.app.tenant_rules_factory") as mock_factory:
            mock_tenants_repo = MagicMock()
            mock_tenants_repo.exists.return_value = False
            mock_factory.tenants_repo.return_value = mock_tenants_repo

            response = authenticated_client.put(
                f"/admin/tenants/{tenant_id}/rules",
                json={"yaml_text": sample_rules_yaml},
            )

            assert response.status_code == 404
            data = response.json()
            assert data["detail"] == "tenant_not_found"

    def test_set_rules_invalid_yaml(
        self, authenticated_client, admin_session, tenant_id
    ):
        """Test setting rules with invalid YAML"""
        with patch("presentation.api.app.tenant_rules_factory") as mock_factory:
            mock_tenants_repo = MagicMock()
            mock_tenants_repo.exists.return_value = True
            mock_factory.tenants_repo.return_value = mock_tenants_repo

            response = authenticated_client.put(
                f"/admin/tenants/{tenant_id}/rules",
                json={"yaml_text": "invalid: yaml: content: ["},
            )

            assert response.status_code == 400
            data = response.json()
            assert "invalid_yaml" in data["detail"]

    def test_set_rules_non_dict_yaml(
        self, authenticated_client, admin_session, tenant_id
    ):
        """Test setting rules with YAML that's not a dictionary"""
        with patch("presentation.api.app.tenant_rules_factory") as mock_factory:
            mock_tenants_repo = MagicMock()
            mock_tenants_repo.exists.return_value = True
            mock_factory.tenants_repo.return_value = mock_tenants_repo

            response = authenticated_client.put(
                f"/admin/tenants/{tenant_id}/rules", json={"yaml_text": "just a string"}
            )

            assert response.status_code == 400
            data = response.json()
            assert "rules must be a mapping" in data["detail"]

    def test_set_rules_unauthorized(self, client, tenant_id, sample_rules_yaml):
        """Test setting rules without admin auth"""
        response = client.put(
            f"/admin/tenants/{tenant_id}/rules", json={"yaml_text": sample_rules_yaml}
        )
        assert response.status_code == 401

    def test_get_sample_rules_success(self, client):
        """Test successful retrieval of sample rules file"""
        response = client.get("/config/rules.sample.yaml")

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/yaml; charset=utf-8"

        content = response.text
        assert "timezone:" in content
        assert "email_triage:" in content
        assert "Pacific/Auckland" in content

    def test_get_sample_rules_file_not_found(self, client):
        """Test sample rules endpoint when file doesn't exist"""
        with patch("builtins.open", side_effect=FileNotFoundError):
            response = client.get("/config/rules.sample.yaml")
            assert response.status_code == 404
            data = response.json()
            assert data["detail"] == "Sample rules file not found"

    def test_apply_standard_rules_workflow(
        self, client, authenticated_client, admin_session, tenant_id
    ):
        """Test the complete workflow of applying standard rules"""
        # First, get the sample rules
        sample_response = client.get("/config/rules.sample.yaml")
        assert sample_response.status_code == 200
        sample_yaml = sample_response.text

        # Then apply them to a tenant
        with patch("presentation.api.app.tenant_rules_factory") as mock_factory:
            mock_tenants_repo = MagicMock()
            mock_tenants_repo.exists.return_value = True
            mock_factory.tenants_repo.return_value = mock_tenants_repo

            mock_rules_repo = MagicMock()
            mock_factory.rules_repo.return_value = mock_rules_repo

            response = authenticated_client.put(
                f"/admin/tenants/{tenant_id}/rules", json={"yaml_text": sample_yaml}
            )

            assert response.status_code == 200
            mock_rules_repo.set_yaml.assert_called_once_with(tenant_id, sample_yaml)

        # Finally, verify they were set
        with patch("presentation.api.app.tenant_rules_factory") as mock_factory:
            mock_rules_repo = MagicMock()
            mock_rules_repo.get_yaml.return_value = sample_yaml
            mock_factory.rules_repo.return_value = mock_rules_repo

            response = authenticated_client.get(f"/admin/tenants/{tenant_id}/rules")

            assert response.status_code == 200
            data = response.json()
            assert data["yaml"] == sample_yaml
