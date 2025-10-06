from dataclasses import dataclass, field
from typing import Dict, Optional, Any

@dataclass
class DbProps:
    db_id: str
    props: Dict[str, str] = field(default_factory=dict)

@dataclass
class Features:
    sessions_value: bool = False
    programs: bool = False
    sales: bool = False

@dataclass
class Currency:
    code: str = "NZD"

@dataclass
class Defaults:
    task_status_new: str = "Inbox"
    session_value_round: int = 0

@dataclass
class NotionCfg:
    tasks: DbProps
    clients: DbProps
    sessions: DbProps

@dataclass
class AppCfg:
    features: Features = field(default_factory=Features)
    currency: Currency = field(default_factory=Currency)
    defaults: Defaults = field(default_factory=Defaults)
    notion: NotionCfg | None = None

def _require(d: Dict[str, Any], key: str) -> Any:
    if key not in d or d[key] in (None, ""):
        raise ValueError(f"missing_required:{key}")
    return d[key]

def normalize(raw: Dict[str, Any]) -> AppCfg:
    # Features
    f = raw.get("features") or {}
    features = Features(
        sessions_value=bool(f.get("sessions_value", False)),
        programs=bool(f.get("programs", False)),
        sales=bool(f.get("sales", False)),
    )
    # Currency
    c = raw.get("currency") or {}
    currency = Currency(code=str(c.get("code", "NZD")).upper())
    # Defaults
    d = raw.get("defaults") or {}
    defaults = Defaults(
        task_status_new=str(d.get("task_status_new", "Inbox")),
        session_value_round=int(d.get("session_value_round", 0)),
    )
    # Notion DBs
    n = _require(raw, "notion")
    def db(dct: Dict[str, Any]) -> DbProps:
        return DbProps(
            db_id=str(_require(dct, "db_id")),
            props={str(k): str(v) for k, v in (dct.get("props") or {}).items()}
        )
    notion = NotionCfg(
        tasks=db(_require(n, "tasks")),
        clients=db(_require(n, "clients")),
        sessions=db(_require(n, "sessions")),
    )
    return AppCfg(features=features, currency=currency, defaults=defaults, notion=notion)
