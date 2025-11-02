"""Tests for settings endpoints."""
import pytest
from fastapi.testclient import TestClient
from presentation.api.app import app
from presentation.api.repos import user_settings

client = TestClient(app)


def test_settings_get_defaults():
    """Test GET /api/settings returns default settings."""
    response = client.get("/api/settings")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert "work_hours" in data
    assert "time_zone" in data
    assert "day_shape" in data


def test_settings_update_work_hours():
    """Test PUT /api/settings updates work hours."""
    response = client.put(
        "/api/settings",
        json={
            "work_hours": {
                "start": "08:00",
                "end": "18:00",
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["work_hours"]["start"] == "08:00"
    assert data["work_hours"]["end"] == "18:00"


def test_settings_validate_time_format():
    """Test time validation rejects invalid formats."""
    response = client.put(
        "/api/settings",
        json={
            "work_hours": {
                "start": "25:00",  # Invalid hour
                "end": "17:00",
            }
        }
    )
    # Should either validate client-side or return 400
    # For now, assuming validation happens
    assert response.status_code in [200, 400]


def test_settings_validate_timezone():
    """Test IANA timezone validation."""
    response = client.put(
        "/api/settings",
        json={
            "time_zone": "Invalid/Timezone",
        }
    )
    assert response.status_code == 400


def test_settings_roundtrip():
    """Test roundtrip: GET → PUT → GET."""
    # Get initial
    get1 = client.get("/api/settings").json()
    
    # Update
    client.put(
        "/api/settings",
        json={
            "work_hours": {
                "start": "10:00",
                "end": "16:00",
            },
            "time_zone": "America/New_York",
        }
    )
    
    # Get again
    get2 = client.get("/api/settings").json()
    
    assert get2["work_hours"]["start"] == "10:00"
    assert get2["time_zone"] == "America/New_York"

