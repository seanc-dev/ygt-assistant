from typing import Dict, Any, Optional
import httpx
from settings import NOTION_API_KEY, NOTION_TASKS_DB_ID, NOTION_CRM_DB_ID
from core.ports.tasks import TasksPort
from core.ports.crm import CRMPort
from infra.repos import settings_factory
from core.config.loader import load_for_tenant
from utils.currency import coerce_amount

NOTION_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"


def _headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def _col(props_map: Dict[str, str], key: str) -> Optional[str]:
    """Get mapped column name, return None if not mapped."""
    return props_map.get(key)


def _build_props_from_config(details: Dict[str, Any], props_map: Dict[str, str], 
                           features: Optional[Any] = None, defaults: Optional[Any] = None) -> Dict[str, Any]:
    """Build Notion properties using config mapping, respecting feature flags."""
    props: Dict[str, Any] = {}
    
    # Title mapping
    if title_col := _col(props_map, "title"):
        title = details.get("title") or details.get("name") or "Untitled"
        props[title_col] = {"title": [{"text": {"content": title}}]}
    
    # Email mapping
    if email_col := _col(props_map, "email"):
        if email := details.get("email"):
            props[email_col] = {"email": email}
    
    # Company mapping (optional)
    if company_col := _col(props_map, "company"):
        if company := details.get("company"):
            props[company_col] = {"rich_text": [{"text": {"content": company}}]}
    
    # Owner mapping (optional)
    if owner_col := _col(props_map, "owner"):
        if owner := details.get("owner"):
            props[owner_col] = {"people": [{"name": owner}]}
    
    # Date mapping
    if date_col := _col(props_map, "date"):
        if date := details.get("date") or details.get("due"):
            props[date_col] = {"date": {"start": date}}
    
    # Value mapping (only if feature enabled)
    if value_col := _col(props_map, "value"):
        if features and features.sessions_value and (value := details.get("value")):
            round_to = defaults.session_value_round if defaults else 0
            rounded = coerce_amount(value, round_to)
            if rounded is not None:
                props[value_col] = {"number": rounded}
    
    # Status mapping
    if status_col := _col(props_map, "status"):
        status = details.get("status") or "Inbox"
        props[status_col] = {"select": {"name": status}}
    
    # Priority mapping
    if priority_col := _col(props_map, "priority"):
        if priority := details.get("priority"):
            props[priority_col] = {"select": {"name": priority}}
    
    # Source mapping
    if source_col := _col(props_map, "source"):
        source = details.get("source") or "Manual"
        props[source_col] = {"select": {"name": source}}
    
    # Source ID mapping
    if source_id_col := _col(props_map, "source_id"):
        if source_id := details.get("source_id"):
            props[source_id_col] = {"rich_text": [{"text": {"content": source_id}}]}
    
    # Email URL mapping
    if email_url_col := _col(props_map, "email_url"):
        if email_url := details.get("email_url"):
            props[email_url_col] = {"url": email_url}
    
    # Notes mapping
    if notes_col := _col(props_map, "notes"):
        if notes := details.get("notes"):
            props[notes_col] = {"rich_text": [{"text": {"content": notes}}]}
    
    # Summary mapping
    if summary_col := _col(props_map, "summary"):
        if summary := details.get("summary"):
            props[summary_col] = {"rich_text": [{"text": {"content": summary}}]}
    
    # Transcript URL mapping
    if transcript_url_col := _col(props_map, "transcript_url"):
        if transcript_url := details.get("transcript_url"):
            props[transcript_url_col] = {"url": transcript_url}
    
    # Duration mapping
    if duration_col := _col(props_map, "duration_min"):
        if duration := details.get("duration_min"):
            props[duration_col] = {"number": int(duration)}
    
    # Tags mapping
    if tags_col := _col(props_map, "tags"):
        if tags := details.get("tags"):
            if isinstance(tags, list):
                props[tags_col] = {"multi_select": [{"name": tag} for tag in tags]}
            else:
                props[tags_col] = {"multi_select": [{"name": str(tags)}]}
    
    # Relations (handle separately as they need IDs)
    if client_rel_col := _col(props_map, "client_rel"):
        if client_id := details.get("client_notion_id"):
            props[client_rel_col] = {"relation": [{"id": client_id}]}
    
    if sessions_rel_col := _col(props_map, "sessions_rel"):
        if session_ids := details.get("session_notion_ids"):
            if isinstance(session_ids, list):
                props[sessions_rel_col] = {"relation": [{"id": sid} for sid in session_ids]}
    
    return props


def _resolve_tasks_db_id(details: Dict[str, Any]) -> str:
    tid = details.get("tenant_id")
    if tid:
        repo = settings_factory.repo()
        v = repo.get(tid, "notion_tasks_db_id")
        if v:
            return v
    return NOTION_TASKS_DB_ID or details.get("database_id") or "TEST_DB"


def _resolve_crm_db_id(details: Dict[str, Any]) -> str:
    tid = details.get("tenant_id")
    if tid:
        repo = settings_factory.repo()
        v = repo.get(tid, "notion_crm_db_id")
        if v:
            return v
    return NOTION_CRM_DB_ID or details.get("database_id") or "TEST_DB"


def _task_payload(details: Dict[str, Any]) -> Dict[str, Any]:
    tenant_id = details.get("tenant_id")
    cfg = load_for_tenant(tenant_id) if tenant_id else None
    
    if cfg and cfg.notion:
        # Use config-driven mapping
        db_id = cfg.notion.tasks.db_id
        props = _build_props_from_config(details, cfg.notion.tasks.props, cfg.features, cfg.defaults)
    else:
        # Fallback to legacy behavior
        title = details.get("title") or "Untitled Task"
        due = (details.get("due") or {}).get("date")
        rel_contact_id = details.get("contact_notion_id")
        db_id = _resolve_tasks_db_id(details)
        props: Dict[str, Any] = {
            "Name": {"title": [{"text": {"content": title}}]},
        }
        if due:
            props["Due"] = {"date": {"start": due}}
        if rel_contact_id:
            props["Contact"] = {"relation": [{"id": rel_contact_id}]}
    
    return {"parent": {"database_id": db_id}, "properties": props}


def _contact_payload(details: Dict[str, Any]) -> Dict[str, Any]:
    tenant_id = details.get("tenant_id")
    cfg = load_for_tenant(tenant_id) if tenant_id else None
    
    if cfg and cfg.notion:
        # Use config-driven mapping
        db_id = cfg.notion.clients.db_id
        props = _build_props_from_config(details, cfg.notion.clients.props, cfg.features, cfg.defaults)
    else:
        # Fallback to legacy behavior
        name = details.get("name") or details.get("email") or "Unknown"
        email = details.get("email")
        company = details.get("company")
        db_id = _resolve_crm_db_id(details)
        props: Dict[str, Any] = {
            "Name": {"title": [{"text": {"content": name}}]},
        }
        if email:
            props["Email"] = {"email": email}
        if company:
            props["Company"] = {"rich_text": [{"text": {"content": company}}]}
    
    return {"parent": {"database_id": db_id}, "properties": props}


def _session_payload(details: Dict[str, Any]) -> Dict[str, Any]:
    """Build session payload using config or fallback to basic mapping."""
    tenant_id = details.get("tenant_id")
    cfg = load_for_tenant(tenant_id) if tenant_id else None
    
    if cfg and cfg.notion:
        # Use config-driven mapping with feature flags
        db_id = cfg.notion.sessions.db_id
        props = _build_props_from_config(details, cfg.notion.sessions.props, cfg.features, cfg.defaults)
    else:
        # Fallback to basic mapping
        title = details.get("title") or "Session"
        db_id = details.get("database_id") or "TEST_SESSIONS_DB"
        props: Dict[str, Any] = {
            "Title": {"title": [{"text": {"content": title}}]},
        }
        if client_id := details.get("client_notion_id"):
            props["Client"] = {"relation": [{"id": client_id}]}
        if date := details.get("date"):
            props["Date"] = {"date": {"start": date}}
        if summary := details.get("summary"):
            props["Summary"] = {"rich_text": [{"text": {"content": summary}}]}
    
    return {"parent": {"database_id": db_id}, "properties": props}


class NotionTasksAdapter(TasksPort):
    def create_task(
        self, details: Dict[str, Any], *, dry_run: bool = True
    ) -> Dict[str, Any]:
        """Create a task in Notion or return a dry-run plan."""

        payload = _task_payload(details)
        if dry_run or not NOTION_API_KEY or not NOTION_TASKS_DB_ID:
            return {
                "dry_run": True,
                "provider": "notion",
                "operation": "create_page",
                "payload": payload,
            }
        with httpx.Client(timeout=10) as client:
            r = client.post(f"{NOTION_BASE}/pages", headers=_headers(), json=payload)
            r.raise_for_status()
            return {"dry_run": False, "provider": "notion", "result": r.json()}


class NotionCRMAdapter(CRMPort):
    def upsert_contact(
        self, details: Dict[str, Any], *, dry_run: bool = True
    ) -> Dict[str, Any]:
        """Upsert a contact in Notion via search->create; returns a dry-run plan by default."""

        def _contact_search_query(details: Dict[str, Any]) -> Dict[str, Any]:
            email = details.get("email")
            if not email:
                return {}
            return {
                "database_id": NOTION_CRM_DB_ID
                or details.get("database_id")
                or "TEST_DB",
                "filter": {"property": "Email", "email": {"equals": email}},
            }

        search = _contact_search_query(details)
        create_payload = _contact_payload(details)
        if dry_run or not NOTION_API_KEY or not NOTION_CRM_DB_ID:
            return {
                "dry_run": True,
                "provider": "notion",
                "operation": "upsert_contact",
                "payload": create_payload,
                "plan": {
                    "search": (
                        {"endpoint": "POST /databases/{db}/query", "body": search}
                        if search
                        else None
                    ),
                    "create_if_absent": {
                        "endpoint": "POST /pages",
                        "body": create_payload,
                    },
                },
            }
        # Live path (not used in tests)
        with httpx.Client(timeout=10) as client:
            sr = client.post(
                f"{NOTION_BASE}/databases/{NOTION_CRM_DB_ID}/query",
                headers=_headers(),
                json=search or {},
            )
            sr.raise_for_status()
            found = sr.json().get("results", [])
            if found:
                return {
                    "dry_run": False,
                    "provider": "notion",
                    "result": {"upsert": "exists", "id": found[0].get("id")},
                }
            cr = client.post(
                f"{NOTION_BASE}/pages", headers=_headers(), json=create_payload
            )
            cr.raise_for_status()
            return {"dry_run": False, "provider": "notion", "result": cr.json()}
