import yaml
import pytest
from core.config.model import normalize, AppCfg, Features, Currency, Defaults, NotionCfg, DbProps


def test_normalize_minimal_config():
    """Test parsing a minimal valid config."""
    raw = {
        "notion": {
            "tasks": {"db_id": "tasks_123", "props": {"title": "Name"}},
            "clients": {"db_id": "clients_123", "props": {"title": "Name"}},
            "sessions": {"db_id": "sessions_123", "props": {"title": "Title"}},
        }
    }
    
    cfg = normalize(raw)
    
    assert isinstance(cfg, AppCfg)
    assert cfg.features.sessions_value is False  # default
    assert cfg.currency.code == "NZD"  # default
    assert cfg.defaults.task_status_new == "Inbox"  # default
    assert cfg.notion.tasks.db_id == "tasks_123"
    assert cfg.notion.tasks.props["title"] == "Name"


def test_normalize_full_config():
    """Test parsing a full config with all features enabled."""
    raw = {
        "features": {
            "sessions_value": True,
            "programs": True,
            "sales": False,
        },
        "currency": {"code": "USD"},
        "defaults": {
            "task_status_new": "Next",
            "session_value_round": 2,
        },
        "notion": {
            "tasks": {
                "db_id": "tasks_123",
                "props": {
                    "title": "Name",
                    "status": "Status",
                    "due": "Due",
                }
            },
            "clients": {
                "db_id": "clients_123", 
                "props": {
                    "title": "Name",
                    "email": "Email",
                    "company": "Company",
                }
            },
            "sessions": {
                "db_id": "sessions_123",
                "props": {
                    "title": "Title",
                    "client_rel": "Client",
                    "value": "Value",
                }
            }
        }
    }
    
    cfg = normalize(raw)
    
    assert cfg.features.sessions_value is True
    assert cfg.features.programs is True
    assert cfg.features.sales is False
    assert cfg.currency.code == "USD"
    assert cfg.defaults.task_status_new == "Next"
    assert cfg.defaults.session_value_round == 2
    assert cfg.notion.tasks.props["status"] == "Status"
    assert cfg.notion.clients.props["company"] == "Company"
    assert cfg.notion.sessions.props["value"] == "Value"


def test_normalize_missing_required_notion():
    """Test that missing required notion section raises ValueError."""
    raw = {"features": {"sessions_value": True}}
    
    with pytest.raises(ValueError, match="missing_required:notion"):
        normalize(raw)


def test_normalize_missing_required_db_id():
    """Test that missing required db_id raises ValueError."""
    raw = {
        "notion": {
            "tasks": {"props": {"title": "Name"}},  # missing db_id
            "clients": {"db_id": "clients_123", "props": {"title": "Name"}},
            "sessions": {"db_id": "sessions_123", "props": {"title": "Title"}},
        }
    }
    
    with pytest.raises(ValueError, match="missing_required:db_id"):
        normalize(raw)


def test_normalize_empty_values():
    """Test that empty/None values are handled correctly."""
    raw = {
        "features": None,
        "currency": None,
        "defaults": None,
        "notion": {
            "tasks": {"db_id": "tasks_123", "props": None},
            "clients": {"db_id": "clients_123", "props": {}},
            "sessions": {"db_id": "sessions_123", "props": {"title": "Title"}},
        }
    }
    
    cfg = normalize(raw)
    
    # Should use defaults for None values
    assert cfg.features.sessions_value is False
    assert cfg.currency.code == "NZD"
    assert cfg.defaults.task_status_new == "Inbox"
    assert cfg.notion.tasks.props == {}  # None becomes empty dict
    assert cfg.notion.clients.props == {}  # empty dict stays empty
    assert cfg.notion.sessions.props["title"] == "Title"


def test_normalize_yaml_template():
    """Test parsing the actual YAML template."""
    template_yaml = """
features:
  sessions_value: true
  programs: false
  sales: false

currency:
  code: "NZD"

notion:
  tasks:
    db_id: "<TASKS_DB_ID>"
    props:
      title: "Name"
      status: "Status"
      due: "Due"
  clients:
    db_id: "<CLIENTS_DB_ID>"
    props:
      title: "Name"
      email: "Email"
      company: "Company"
  sessions:
    db_id: "<SESSIONS_DB_ID>"
    props:
      title: "Title"
      client_rel: "Client"
      value: "Value"

defaults:
  task_status_new: "Inbox"
  session_value_round: 0
"""
    
    raw = yaml.safe_load(template_yaml)
    cfg = normalize(raw)
    
    assert cfg.features.sessions_value is True
    assert cfg.currency.code == "NZD"
    assert cfg.notion.tasks.db_id == "<TASKS_DB_ID>"
    assert cfg.notion.tasks.props["title"] == "Name"
    assert cfg.notion.clients.props["company"] == "Company"
    assert cfg.notion.sessions.props["value"] == "Value"
