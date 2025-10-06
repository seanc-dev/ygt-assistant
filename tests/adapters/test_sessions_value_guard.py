import yaml
import pytest
from core.config.model import normalize
from adapters.notion_adapter import _build_props_from_config


def _cfg(yaml_str: str):
    """Helper to create config from YAML string."""
    return normalize(yaml.safe_load(yaml_str))


def test_value_dropped_when_feature_off():
    """Test that sessions value is dropped when feature is disabled."""
    y = """
features:
  sessions_value: false
notion:
  sessions:
    db_id: "test_db"
    props:
      title: "Title"
      value: "Value (optional)"
  tasks:
    db_id: "test_db"
    props: {}
  clients:
    db_id: "test_db"
    props: {}
"""
    cfg = _cfg(y)
    
    details = {"title": "Test Session", "value": "$150"}
    props = _build_props_from_config(details, cfg.notion.sessions.props, cfg.features, cfg.defaults)
    
    # Value should not be included when feature is off
    assert "Value (optional)" not in props
    assert "Title" in props
    assert props["Title"]["title"][0]["text"]["content"] == "Test Session"


def test_value_included_and_rounded():
    """Test that sessions value is included and rounded when feature is enabled."""
    y = """
features:
  sessions_value: true
defaults:
  session_value_round: 0
notion:
  sessions:
    db_id: "test_db"
    props:
      title: "Title"
      value: "Value (optional)"
  tasks:
    db_id: "test_db"
    props: {}
  clients:
    db_id: "test_db"
    props: {}
"""
    cfg = _cfg(y)
    
    details = {"title": "Test Session", "value": "NZD 149.6"}
    props = _build_props_from_config(details, cfg.notion.sessions.props, cfg.features, cfg.defaults)
    
    # Value should be included and rounded
    assert "Value (optional)" in props
    assert props["Value (optional)"]["number"] == 150.0
    assert props["Title"]["title"][0]["text"]["content"] == "Test Session"


def test_value_rounding_with_different_rounding():
    """Test value rounding with different rounding settings."""
    y = """
features:
  sessions_value: true
defaults:
  session_value_round: 2
notion:
  sessions:
    db_id: "test_db"
    props:
      title: "Title"
      value: "Value (optional)"
  tasks:
    db_id: "test_db"
    props: {}
  clients:
    db_id: "test_db"
    props: {}
"""
    cfg = _cfg(y)
    
    details = {"title": "Test Session", "value": "149.567"}
    props = _build_props_from_config(details, cfg.notion.sessions.props, cfg.features, cfg.defaults)
    
    # Value should be rounded to 2 decimal places
    assert props["Value (optional)"]["number"] == 149.57


def test_optional_company_field():
    """Test that company field is optional and only included if present."""
    y = """
notion:
  clients:
    db_id: "test_db"
    props:
      title: "Name"
      company: "Company"
  tasks:
    db_id: "test_db"
    props: {}
  sessions:
    db_id: "test_db"
    props: {}
"""
    cfg = _cfg(y)
    
    # With company
    details_with_company = {"title": "Test Client", "company": "Acme Corp"}
    props_with = _build_props_from_config(details_with_company, cfg.notion.clients.props)
    assert "Company" in props_with
    assert props_with["Company"]["rich_text"][0]["text"]["content"] == "Acme Corp"
    
    # Without company
    details_without_company = {"title": "Test Client"}
    props_without = _build_props_from_config(details_without_company, cfg.notion.clients.props)
    assert "Company" not in props_without


def test_optional_owner_field():
    """Test that owner field is optional and only included if present."""
    y = """
notion:
  clients:
    db_id: "test_db"
    props:
      title: "Name"
      owner: "Owner"
  tasks:
    db_id: "test_db"
    props: {}
  sessions:
    db_id: "test_db"
    props: {}
"""
    cfg = _cfg(y)
    
    # With owner
    details_with_owner = {"title": "Test Client", "owner": "John Doe"}
    props_with = _build_props_from_config(details_with_owner, cfg.notion.clients.props)
    assert "Owner" in props_with
    assert props_with["Owner"]["people"][0]["name"] == "John Doe"
    
    # Without owner
    details_without_owner = {"title": "Test Client"}
    props_without = _build_props_from_config(details_without_owner, cfg.notion.clients.props)
    assert "Owner" not in props_without


def test_unmapped_fields_ignored():
    """Test that unmapped fields are ignored."""
    y = """
notion:
  sessions:
    db_id: "test_db"
    props:
      title: "Title"
      # value not mapped
  tasks:
    db_id: "test_db"
    props: {}
  clients:
    db_id: "test_db"
    props: {}
"""
    cfg = _cfg(y)
    
    details = {"title": "Test Session", "value": "$150", "unmapped_field": "ignored"}
    props = _build_props_from_config(details, cfg.notion.sessions.props, cfg.features)
    
    # Only mapped fields should be included
    assert "Title" in props
    assert "value" not in props
    assert "unmapped_field" not in props


def test_currency_coercion():
    """Test currency value coercion with various formats."""
    y = """
features:
  sessions_value: true
notion:
  sessions:
    db_id: "test_db"
    props:
      title: "Title"
      value: "Value (optional)"
  tasks:
    db_id: "test_db"
    props: {}
  clients:
    db_id: "test_db"
    props: {}
"""
    cfg = _cfg(y)
    
    test_cases = [
        ("$150", 150.0),
        ("NZD 200.50", 200.0),  # Rounded to 0 decimal places
        ("USD 99.99", 100.0),   # Rounded to 0 decimal places
        ("150", 150.0),
        ("150.5", 150.0),       # Rounded to 0 decimal places (rounds down)
        ("invalid", None),      # Should be filtered out
    ]
    
    for input_val, expected in test_cases:
        details = {"title": "Test Session", "value": input_val}
        props = _build_props_from_config(details, cfg.notion.sessions.props, cfg.features, cfg.defaults)
        
        if expected is None:
            assert "Value (optional)" not in props
        else:
            assert "Value (optional)" in props
            assert props["Value (optional)"]["number"] == expected
