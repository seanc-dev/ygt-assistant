import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TEST_ADMIN_SECRET = "test-admin-secret-1234567890"
TEST_ENCRYPTION_KEY = "D_Jhyl9DGCCyOLU_qTzw3CSLinmvglzsXDbNSsmw24w="

os.environ["TESTING"] = "true"
os.environ["ADMIN_EMAIL"] = "admin@example.com"
os.environ["ADMIN_SECRET"] = TEST_ADMIN_SECRET
os.environ["ENCRYPTION_KEY"] = TEST_ENCRYPTION_KEY


@pytest.fixture(autouse=True)
def _reset_env(monkeypatch):
    """Ensure common env defaults exist for tests without pulling in legacy stubs."""

    monkeypatch.setenv("ADMIN_EMAIL", "admin@example.com")
    monkeypatch.setenv("ADMIN_SECRET", TEST_ADMIN_SECRET)
    monkeypatch.setenv("ENCRYPTION_KEY", TEST_ENCRYPTION_KEY)
    monkeypatch.setenv("TESTING", "true")
    yield
