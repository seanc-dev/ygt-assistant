"""Tests for Nylas OAuth endpoints."""

import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import json

os.environ["NYLAS_API_URL"] = "https://login.nylas.com"

from presentation.api.app import app
from core.domain.nylas_grant import NylasGrant
from settings import NYLAS_API_URL


client = TestClient(app)


class TestNylasOAuthStart:
    """Test Nylas OAuth start endpoint."""
    
    def test_start_google_oauth(self):
        """Test starting Google OAuth flow."""
        response = client.get("/oauth/nylas/start?provider=google", follow_redirects=False)
        
        assert response.status_code == 302
        assert NYLAS_API_URL in response.headers["location"]
        assert "/connect/auth" in response.headers["location"]
        assert "provider=google" in response.headers["location"]
        assert "client_id=" in response.headers["location"]
        assert "state=" in response.headers["location"]
    
    def test_start_microsoft_oauth(self):
        """Test starting Microsoft OAuth flow."""
        response = client.get("/oauth/nylas/start?provider=microsoft", follow_redirects=False)
        
        assert response.status_code == 302
        assert NYLAS_API_URL in response.headers["location"]
        assert "/connect/auth" in response.headers["location"]
        assert "provider=microsoft" in response.headers["location"]
        assert "client_id=" in response.headers["location"]
        assert "state=" in response.headers["location"]
    
    def test_start_invalid_provider(self):
        """Test starting OAuth with invalid provider."""
        response = client.get("/oauth/nylas/start?provider=invalid")
        
        assert response.status_code == 422  # Validation error


class TestNylasOAuthCallback:
    """Test Nylas OAuth callback endpoint."""
    
    def test_callback_mock_mode(self):
        """Test callback in mock mode."""
        with patch.dict("os.environ", {"MOCK_OAUTH": "true"}):
            response = client.get(
                "/oauth/nylas/callback?provider=google&code=test_code&state=test_state"
            )
            
            assert response.status_code == 400  # Invalid state (not stored)
    
    def test_callback_invalid_state(self):
        """Test callback with invalid state."""
        response = client.get(
            "/oauth/nylas/callback?provider=google&code=test_code&state=invalid_state"
        )
        
        assert response.status_code == 400
        assert "invalid_state" in response.json()["detail"]
    
    def test_callback_invalid_provider(self):
        """Test callback with invalid provider."""
        response = client.get(
            "/oauth/nylas/callback?provider=invalid&code=test_code&state=test_state"
        )
        
        assert response.status_code == 422  # Validation error


class TestNylasWebhook:
    """Test Nylas webhook endpoints."""
    
    def test_webhook_challenge(self):
        """Test webhook challenge verification."""
        response = client.get("/webhooks/nylas?challenge=test_challenge")
        
        assert response.status_code == 200
        assert response.text == "test_challenge"
    
    def test_webhook_challenge_empty(self):
        """Test webhook challenge with empty challenge."""
        response = client.get("/webhooks/nylas")
        
        assert response.status_code == 200
        assert response.text == ""
    
    def test_webhook_post_no_verification(self):
        """Test webhook POST without signature verification."""
        with patch.dict("os.environ", {"VERIFY_NYLAS": "false"}):
            response = client.post(
                "/webhooks/nylas",
                json={"type": "email.created", "data": {"id": "123"}}
            )
            
            assert response.status_code == 200
            assert response.json()["ok"] is True
    
    def test_webhook_post_with_verification(self):
        """Test webhook POST with signature verification."""
        with patch.dict("os.environ", {"VERIFY_NYLAS": "true", "NYLAS_SIGNING_SECRET": "test_secret"}):
            # This will fail signature verification but should not crash
            response = client.post(
                "/webhooks/nylas",
                json={"type": "email.created", "data": {"id": "123"}},
                headers={"X-Nylas-Signature": "invalid_signature"}
            )
            
            assert response.status_code == 401
            assert "invalid_signature" in response.json()["detail"]


class TestNylasGrantModel:
    """Test Nylas grant domain model."""
    
    def test_grant_to_dict(self):
        """Test converting grant to dictionary."""
        grant = NylasGrant(
            grant_id="test_grant",
            provider="google",
            email="test@example.com",
            scopes=["calendar", "email"],
            access_token="access_token",
            refresh_token="refresh_token"
        )
        
        data = grant.to_dict()
        
        assert data["grant_id"] == "test_grant"
        assert data["provider"] == "google"
        assert data["email"] == "test@example.com"
        assert data["scopes"] == ["calendar", "email"]
        assert data["access_token"] == "access_token"
        assert data["refresh_token"] == "refresh_token"
    
    def test_grant_from_dict(self):
        """Test creating grant from dictionary."""
        data = {
            "grant_id": "test_grant",
            "provider": "google",
            "email": "test@example.com",
            "scopes": ["calendar", "email"],
            "access_token": "access_token",
            "refresh_token": "refresh_token",
            "expires_at": None,
            "created_at": None,
            "updated_at": None
        }
        
        grant = NylasGrant.from_dict(data)
        
        assert grant.grant_id == "test_grant"
        assert grant.provider == "google"
        assert grant.email == "test@example.com"
        assert grant.scopes == ["calendar", "email"]
        assert grant.access_token == "access_token"
        assert grant.refresh_token == "refresh_token"
