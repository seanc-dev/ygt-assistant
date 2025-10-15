from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request, Query, Depends, Response
from pydantic import BaseModel, Field

from utils.command_dispatcher import dispatch
from core.services.triage_engine import EmailEnvelope, triage_email
from dotenv import load_dotenv

# Load local overrides first if present, then fallback to .env
try:
    load_dotenv(".env.local", override=True)
except Exception:
    pass
load_dotenv()
from settings import (
    VERIFY_NYLAS,
    NYLAS_SIGNING_SECRET,
    TENANT_DEFAULT,
    MOCK_OAUTH,
    NOTION_CLIENT_ID,
    NOTION_CLIENT_SECRET,
    NOTION_REDIRECT_URI,
    NYLAS_CLIENT_ID,
    NYLAS_CLIENT_SECRET,
    NYLAS_API_URL,
    NYLAS_REDIRECT_URI,
    ENCRYPTION_KEY,
    ADMIN_EMAIL,
    ADMIN_SECRET,
    COOKIE_NAME,
    ADMIN_UI_ORIGIN,
    CLIENT_UI_ORIGIN,
    ENABLE_ADMIN,
)
from core.services.action_executor import execute_actions
from utils.crypto import fernet_from, encrypt
from infra.repos import connections_factory
from infra.repos.nylas_grants_factory import repo as nylas_grants_repo
from infra.memory import state_store
from core.domain.nylas_grant import NylasGrant
import hmac
import hashlib
import inspect
import json
import urllib.parse
import os
import secrets
import httpx
import logging
import asyncio
from utils.admin_session import issue_session, verify_session, cookie_name
from utils.client_session import (
    issue_client_session,
    verify_client_session,
    client_cookie_name,
)
from fastapi.middleware.cors import CORSMiddleware
from infra.repos import tenant_rules_factory
from infra.repos import settings_factory
from infra.repos.factory import users_repo
from fastapi.responses import RedirectResponse, StreamingResponse
from infra.repos.mailer_factory import mailer
from utils.email_templates import render_onboarding_email
from services.gmail import GmailService
from services.calendar import CalendarService
from services import llm as llm_service
from infra.repos.factory import audit_repo
from core.store import get_store
import yaml
import uuid
from datetime import datetime, timezone, timedelta
import re
from services.whatsapp import parse_webhook as _wa_parse
from services.whatsapp import send_buttons as _wa_send_buttons
from services.whatsapp import send_text as _wa_send_text


app = FastAPI(title="YGT Integration API", version="0.1.0")

# Ephemeral per-user preferences/timezone store (until DB columns exist)
_user_prefs_store: Dict[str, Dict[str, Any]] = {}
# Dev-only in-memory rules store keyed by user_id
_user_rules_store: Dict[str, List[Dict[str, Any]]] = {}
# Dev-only in-memory actions store keyed by user_id
_user_actions_store: Dict[str, List[Dict[str, Any]]] = {}
_approvals_store: Dict[str, Dict[str, Any]] = {}
_history_log: List[Dict[str, Any]] = []
_drafts_store: Dict[str, Dict[str, Any]] = {}


class DevEmailIn(BaseModel):
    message_id: str
    sender: str
    subject: str = ""
    body_text: str = ""
    received_at: Optional[datetime] = None
    attachments: List[str] = Field(default_factory=list)


def _extract_amounts(text: str) -> List[str]:
    if not text:
        return []
    matches = re.findall(r"\$\s?\d[\d,]*(?:\.\d{2})?", text)
    seen: Dict[str, bool] = {}
    result: List[str] = []
    for match in matches:
        normalized = match.strip()
        if normalized not in seen:
            seen[normalized] = True
            result.append(normalized)
    return result


def _extract_dates(text: str) -> List[str]:
    if not text:
        return []
    keywords = [
        "today",
        "tomorrow",
        "next week",
        "friday",
        "monday",
        "this afternoon",
        "end of day",
    ]
    lowered = text.lower()
    return [keyword for keyword in keywords if keyword in lowered]


def _extract_people(sender: str, body: str) -> List[str]:
    people: List[str] = []
    if sender:
        name_part = sender.split("<")[0].strip()
        if "@" in name_part:
            name_part = name_part.split("@")[0]
        cleaned = name_part.strip('"')
        if cleaned:
            people.append(cleaned)
    for match in re.findall(r"with ([A-Z][a-zA-Z]+)", body or ""):
        if match not in people:
            people.append(match)
    return people


def _build_llm_drafts(
    subject: str, people: List[str], amounts: List[str]
) -> List[Dict[str, Any]]:
    person = people[0] if people else "there"
    amount = amounts[0] if amounts else "the request"
    base = f"Hi {person},\n\nThanks for the update on {subject or 'this request'}."
    return [
        {
            "tone": "brief",
            "subject": subject or "Quick follow-up",
            "body": f"{base} Just confirming receipt and will get back to you shortly.\n\nThanks!",
        },
        {
            "tone": "friendly",
            "subject": subject or "Thanks for sending this over",
            "body": f"{base} Really appreciate the details on {amount}. Let me know if anything else is needed.\n\nBest,",
        },
        {
            "tone": "detailed",
            "subject": subject or "Following up",
            "body": (
                f"{base} I reviewed the information about {amount} and will circle back with next steps by tomorrow."
            ),
        },
    ]


def _suggest_calendar_times(base: datetime) -> List[str]:
    return [
        (base + timedelta(hours=4)).strftime("%a %-I:%M %p"),
        (base + timedelta(hours=28)).strftime("%a %-I:%M %p"),
        (base + timedelta(days=2, hours=3)).strftime("%a %-I:%M %p"),
    ]


allowed_origins = {
    # Explicit admin and client UI origins
    (ADMIN_UI_ORIGIN or "").strip(),
    (CLIENT_UI_ORIGIN or "").strip(),
    # Explicit prod admin domain kept for safety
    "https://admin.coachflow.nz",
    # Local dev hosts (admin-ui, client-ui, site)
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
    "http://localhost:3002",
    "http://127.0.0.1:3002",
    "http://localhost:3003",
    "http://127.0.0.1:3003",
}

# Include Vercel preview URL if provided via env (e.g., https://client-ui-abc123.vercel.app)
_preview = os.getenv("VERCEL_PREVIEW_URL", "").strip()
if _preview:
    # Accept either protocol-less host or full URL
    if _preview.startswith("http"):
        allowed_origins.add(_preview)
    else:
        allowed_origins.add(f"https://{_preview}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o for o in allowed_origins if o],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"] + ["Authorization", "Content-Type"],
)


# Request-ID middleware for structured tracing
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    rid = request.headers.get("x-request-id") or os.getenv(
        "REQUEST_ID_PREFIX", "req_"
    ) + secrets.token_hex(8)
    try:
        response = await call_next(request)
    except Exception as exc:
        # Ensure request id is present even on errors
        response = Response(status_code=500, content="internal_error")
    response.headers["x-request-id"] = rid
    return response


# Block legacy admin endpoints when disabled
@app.middleware("http")
async def guard_admin_paths(request: Request, call_next):
    if not ENABLE_ADMIN:
        p = request.url.path or ""
        if p.startswith("/admin") or p.startswith("/oauth") or p.startswith("/config"):
            return Response(status_code=404, content="not_found")
    return await call_next(request)


# Dev-only helpers (do not enable in production)
if (os.getenv("DEV_MODE", "").strip().lower() in {"1", "true", "yes", "on"}) or (
    os.getenv("PYTEST_CURRENT_TEST")
):
    # Seed a known dev user at startup so memory repos survive reloads for local testing
    @app.on_event("startup")
    async def _dev_seed_user() -> None:  # pragma: no cover - dev-only
        try:
            import bcrypt as _bcrypt
            from infra.repos.factory import users_repo as _users_repo

            dev_email = os.getenv("DEV_USER_EMAIL", "test.user+local@example.com")
            dev_password = os.getenv("DEV_USER_PASSWORD", "localpass123!")
            dev_name = os.getenv("DEV_USER_NAME", "Local Test")
            dev_tenant = os.getenv("DEV_TENANT_ID", TENANT_DEFAULT)

            repo = _users_repo()
            existing = repo.get_by_email(dev_email)
            pw_hash = _bcrypt.hashpw(dev_password.encode(), _bcrypt.gensalt()).decode()
            if existing:
                repo.update_password(existing.get("id"), pw_hash, must_change=False)
            else:
                repo.upsert(dev_tenant, dev_email, dev_name, pw_hash, must_change=False)
        except Exception:
            # Non-fatal in dev environment
            pass

    class _DevCreateUserIn(BaseModel):
        email: str
        password: str
        name: str | None = None
        tenant_id: str | None = None

    @app.post("/dev/users")
    async def _dev_create_user(body: _DevCreateUserIn):
        import bcrypt as _bcrypt
        from infra.repos.factory import users_repo as _users_repo

        tid = body.tenant_id or TENANT_DEFAULT
        pw_hash = _bcrypt.hashpw(body.password.encode(), _bcrypt.gensalt()).decode()
        uid = _users_repo().upsert(
            tid, body.email, body.name, pw_hash, must_change=False
        )
        return {"ok": True, "user_id": uid}


@app.get("/health")
async def health() -> Dict[str, str]:
    """Health check endpoint.

    Returns a simple JSON payload confirming the API is responsive.
    """

    return {"status": "ok"}


class CalendarAction(BaseModel):
    """Request model describing a calendar action to perform.

    Attributes:
        action: The calendar action, e.g. "create_event", "move_event", "delete_event".
        details: Arbitrary details required by the action.
        dry_run: If true, returns a plan without executing any side effects.
    """

    action: str = Field(..., description="create_event|move_event|delete_event")
    details: Dict[str, Any] = Field(default_factory=dict)
    dry_run: bool = False


@app.post("/calendar/actions")
async def calendar_actions(payload: CalendarAction) -> Dict[str, Any]:
    """Execute or plan a calendar action via the existing dispatcher.

    When ``dry_run`` is true, returns a plan without invoking the dispatcher.
    """

    if payload.dry_run:
        return {
            "dry_run": True,
            "plan": {"action": payload.action, "details": payload.details},
        }
    try:
        result = dispatch(payload.action, payload.details)
        return {"ok": True, "result": result}
    except Exception as exc:  # pragma: no cover - behavior is surfaced via HTTP status
        raise HTTPException(status_code=400, detail=str(exc))


def _valid_nylas_sig(raw_body: bytes, provided_sig: str, secret: str) -> bool:
    if not secret:
        return True
    mac = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(mac, provided_sig or "")


def _require_admin(req: Request):
    tok = req.cookies.get(cookie_name(), "")
    email = verify_session(tok) or ""
    if not email:
        raise HTTPException(status_code=401, detail="unauthorized")
    return email


@app.get("/webhooks/nylas")
async def nylas_challenge(challenge: str = Query("")):
    """Handle Nylas webhook challenge verification."""
    # Nylas verifies webhook by GET ?challenge=<token>; echo it
    return Response(content=challenge, media_type="text/plain")


@app.post("/webhooks/nylas")
async def nylas_webhook(req: Request) -> Dict[str, Any]:
    body = await req.body()
    # Read verification flags dynamically; disable during pytest
    is_pytest = bool(os.getenv("PYTEST_CURRENT_TEST"))
    verify_flag = os.getenv("VERIFY_NYLAS", "false").lower() == "true"
    secret = os.getenv("NYLAS_SIGNING_SECRET", "")
    provided = req.headers.get("X-Nylas-Signature", "")
    if verify_flag and provided:
        if not _valid_nylas_sig(body, provided, secret):
            raise HTTPException(status_code=401, detail="invalid_signature")
    try:
        payload = json.loads(body.decode() or "{}")
    except Exception:
        payload = {}
    evt_type = payload.get("type")
    if evt_type == "email.created":
        msg = payload.get("data", {})
        env = EmailEnvelope(
            message_id=str(msg.get("id", "")),
            sender=str((msg.get("from") or [{}])[0].get("email", "")),
            subject=str(msg.get("subject", "")),
            body_text=str(msg.get("snippet", "") or msg.get("body", "")),
            received_at=str(msg.get("date", "")),
        )
        triaged = triage_email(env)
        return {"ok": True, "triage": triaged.dict()}
    return {"ok": True, "ignored": True}


# WhatsApp webhook verification and handler
@app.get("/whatsapp/webhook")
async def whatsapp_verify(
    mode: str = Query(""), token: str = Query(""), challenge: str = Query("")
):
    verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN", "")
    if mode == "subscribe" and token and verify_token and token == verify_token:
        return Response(content=challenge, media_type="text/plain")
    raise HTTPException(status_code=403, detail="forbidden")


@app.post("/whatsapp/webhook")
async def whatsapp_webhook(req: Request) -> Dict[str, Any]:
    try:
        body = await req.json()
    except Exception:
        body = {}
    parsed = _wa_parse(body)
    # Basic command routing for POC
    try:
        if parsed.get("type") == "button":
            bid = parsed.get("button_id") or ""
            if bid.startswith("approve:"):
                aid = bid.split(":", 1)[1]
                return await actions_approve(aid)
            if bid.startswith("edit:"):
                aid = bid.split(":", 1)[1]
                return await actions_edit(aid, EditIn(instructions="tweak"))
            if bid.startswith("skip:"):
                aid = bid.split(":", 1)[1]
                return await actions_skip(aid)
            if bid.startswith("send:"):
                did = bid.split(":", 1)[1]
                return await email_send(did)
            if bid.startswith("schedule:"):
                # Not implemented in POC; acknowledge
                return {"ok": True, "scheduled": False}
        if parsed.get("type") == "text":
            text = (parsed.get("text") or "").strip().lower()
            if text.startswith("approve "):
                aid = text.split(" ", 1)[1]
                return await actions_approve(aid)
            if text.startswith("skip "):
                aid = text.split(" ", 1)[1]
                return await actions_skip(aid)
            if text.startswith("send "):
                did = text.split(" ", 1)[1]
                return await email_send(did)
    except Exception:
        pass
    return {"ok": True, "parsed": parsed}


class ProposedActionIn(BaseModel):
    type: str
    payload: Dict[str, Any] = Field(default_factory=dict)


class ExecuteRequest(BaseModel):
    actions: List[ProposedActionIn]
    dry_run: bool | None = None
    tenant_id: str | None = None


@app.post("/actions/execute")
async def actions_execute(req: ExecuteRequest) -> Dict[str, Any]:
    return execute_actions(
        [a.model_dump() for a in req.actions],
        dry_run=req.dry_run,
        tenant_id=req.tenant_id or "tenant-default",
    )


# Actions scanning and approvals endpoints (POC)
class ScanIn(BaseModel):
    domains: List[str] = Field(default_factory=list)


@app.post("/actions/scan")
async def actions_scan(body: ScanIn) -> List[Dict[str, Any]]:
    store = get_store()
    core_ctx = {
        "episodic": [m.__dict__ for m in store.list_by_level("episodic")][:5],
        "semantic": [m.__dict__ for m in store.list_by_level("semantic")][:5],
        "procedural": [m.__dict__ for m in store.list_by_level("procedural")][:5],
        "narrative": [m.__dict__ for m in store.list_by_level("narrative")][:5],
    }
    context = {"domains": body.domains}
    approvals = llm_service.summarise_and_propose(context, core_ctx)
    # Cache approvals in memory for POC flows
    for a in approvals:
        a.setdefault("status", "proposed")
        _approvals_store[a["id"]] = a
    # Audit proposal
    try:
        rid = secrets.token_hex(8)
        audit_repo().write(
            {
                "request_id": rid,
                "tenant_id": TENANT_DEFAULT,
                "dry_run": True,
                "actions": approvals,
                "results": {"source": "actions_scan"},
            }
        )
    except Exception:
        pass
    return approvals


@app.get("/approvals")
async def approvals_list(
    filter: Optional[str] = Query(default="all"),
) -> List[Dict[str, Any]]:
    items = list(_approvals_store.values())
    if filter in {"email", "calendar"}:
        items = [a for a in items if a.get("kind") == filter]
    # newest first if created_at present
    try:
        items.sort(key=lambda x: x.get("created_at") or "", reverse=True)
    except Exception:
        pass
    return items


@app.post("/actions/approve/{approval_id}")
async def actions_approve(approval_id: str) -> Dict[str, Any]:
    a = _approvals_store.get(approval_id)
    if not a:
        raise HTTPException(status_code=404, detail="not_found")
    a["status"] = "approved"
    # Write in-memory history for POC
    _history_log.append(
        {
            "ts": datetime.now(timezone.utc).isoformat(),
            "verb": "approve",
            "object": "approval",
            "id": approval_id,
        }
    )
    return a


class EditIn(BaseModel):
    instructions: str


@app.post("/actions/edit/{approval_id}")
async def actions_edit(approval_id: str, body: EditIn) -> Dict[str, Any]:
    a = _approvals_store.get(approval_id)
    if not a:
        raise HTTPException(status_code=404, detail="not_found")
    a["status"] = "edited"
    a["edit_instructions"] = body.instructions
    _history_log.append(
        {
            "ts": datetime.now(timezone.utc).isoformat(),
            "verb": "edit",
            "object": "approval",
            "id": approval_id,
            "instructions": body.instructions,
        }
    )
    return a


@app.post("/actions/skip/{approval_id}")
async def actions_skip(approval_id: str) -> Dict[str, Any]:
    a = _approvals_store.get(approval_id)
    if not a:
        raise HTTPException(status_code=404, detail="not_found")
    a["status"] = "skipped"
    _history_log.append(
        {
            "ts": datetime.now(timezone.utc).isoformat(),
            "verb": "skip",
            "object": "approval",
            "id": approval_id,
        }
    )
    return a


@app.post("/actions/undo/{approval_id}")
async def actions_undo(approval_id: str) -> Dict[str, Any]:
    a = _approvals_store.get(approval_id)
    if not a:
        raise HTTPException(status_code=404, detail="not_found")
    a["status"] = "proposed"
    _history_log.append(
        {
            "ts": datetime.now(timezone.utc).isoformat(),
            "verb": "undo",
            "object": "approval",
            "id": approval_id,
        }
    )
    return a


class WhatsAppSendApprovalIn(BaseModel):
    to: str


@app.post("/whatsapp/send/approval/{approval_id}")
async def whatsapp_send_approval(
    approval_id: str, body: WhatsAppSendApprovalIn
) -> Dict[str, Any]:
    a = _approvals_store.get(approval_id)
    if not a:
        raise HTTPException(status_code=404, detail="not_found")
    text = a.get("summary") or a.get("title") or f"Approve {approval_id}?"
    buttons = [
        {"id": f"approve:{approval_id}", "label": "Approve"},
        {"id": f"edit:{approval_id}", "label": "Edit"},
        {"id": f"skip:{approval_id}", "label": "Skip"},
    ]
    try:
        res = _wa_send_buttons(body.to, text, buttons)
        return {"ok": True, "result": res}
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/history")
async def history(limit: int = 100) -> List[Dict[str, Any]]:
    return list(reversed(_history_log))[: max(0, min(limit, 1000))]


class WhatsAppSendDraftIn(BaseModel):
    to: str
    draft_id: str


@app.post("/whatsapp/send/draft")
async def whatsapp_send_draft(body: WhatsAppSendDraftIn) -> Dict[str, Any]:
    d = _drafts_store.get(body.draft_id)
    if not d:
        raise HTTPException(status_code=404, detail="not_found")
    preview = f"Draft to {', '.join(d.get('to') or [])}\nSubject: {d.get('subject','')}\n{d.get('body','')[:200]}"
    buttons = [
        {"id": f"send:{body.draft_id}", "label": "Send"},
        {"id": f"edit:{body.draft_id}", "label": "Edit"},
        {"id": f"schedule:{body.draft_id}", "label": "Schedule"},
    ]
    try:
        res = _wa_send_buttons(body.to, preview, buttons)
        return {"ok": True, "result": res}
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


class WhatsAppSendPlanIn(BaseModel):
    to: str


@app.post("/whatsapp/send/plan-today")
async def whatsapp_send_plan_today(body: WhatsAppSendPlanIn) -> Dict[str, Any]:
    c = CalendarService()
    plan = c.list_today()
    text = "Plan for Today\n" + "\n".join(
        [f"• {i.get('time','10:00')} {i.get('title','Focus block')}" for i in plan]
    )
    try:
        res = _wa_send_text(body.to, text)
        return {"ok": True, "result": res}
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


# Email endpoints
class DraftIn(BaseModel):
    to: List[str] = Field(default_factory=list)
    subject: str = ""
    body: str = ""
    tone: Optional[str] = None


@app.post("/email/drafts")
async def email_create_draft(body: DraftIn) -> Dict[str, Any]:
    g = GmailService()
    d = g.create_draft(body.to, body.subject, body.body)
    _drafts_store[d["id"]] = d
    return d


@app.post("/email/send/{draft_id}")
async def email_send(draft_id: str) -> Dict[str, Any]:
    g = GmailService()
    out = g.send(draft_id)
    if draft_id in _drafts_store:
        _drafts_store[draft_id]["status"] = "sent"
    _history_log.append(
        {
            "ts": datetime.now(timezone.utc).isoformat(),
            "verb": "send",
            "object": "draft",
            "id": draft_id,
        }
    )
    return out


@app.get("/drafts")
async def list_drafts() -> List[Dict[str, Any]]:
    return list(_drafts_store.values())


# Calendar endpoints
@app.post("/calendar/plan-today")
async def calendar_plan_today() -> Dict[str, Any]:
    c = CalendarService()
    plan = c.list_today()
    # Emit a WhatsApp-friendly card text (POC) in response
    card_text = "Plan for Today\n" + "\n".join(
        [f"• {i.get('time','10:00')} {i.get('title','Focus block')}" for i in plan]
    )
    return {"plan": plan, "card": card_text}


@app.post("/calendar/reschedule")
async def calendar_reschedule(body: Dict[str, Any]) -> Dict[str, Any]:
    c = CalendarService()
    return c.create_or_update(body)


# Core endpoints
@app.get("/core/context")
async def core_context(
    for_: Optional[str] = Query(default=None, alias="for")
) -> Dict[str, Any]:
    store = get_store()
    ctx = {
        "episodic": [m.__dict__ for m in store.list_by_level("episodic")][:5],
        "semantic": [m.__dict__ for m in store.list_by_level("semantic")][:5],
        "procedural": [m.__dict__ for m in store.list_by_level("procedural")][:5],
        "narrative": [m.__dict__ for m in store.list_by_level("narrative")][:5],
    }
    return ctx


class NoteIn(BaseModel):
    fact: str
    tags: Optional[List[str]] = None
    source: Optional[str] = None


@app.post("/core/notes")
async def core_notes(body: NoteIn) -> Dict[str, Any]:
    from core.writer import write_semantic

    item = write_semantic(body.fact, source=body.source)
    return {"ok": True, "id": item.id}


@app.get("/core/preview")
async def core_preview(intent: Optional[str] = None) -> Dict[str, Any]:
    store = get_store()
    # Preview the latest items used for context
    preview = {
        "semantic": [m.__dict__ for m in store.list_by_level("semantic")][:5],
        "narrative": [m.__dict__ for m in store.list_by_level("narrative")][:5],
    }
    return preview


class AdminIssueCredentialsIn(BaseModel):
    email: str
    name: str | None = None


@app.post("/admin/tenants/{tenant_id}/issue-credentials")
async def admin_issue_credentials(
    tenant_id: str, body: AdminIssueCredentialsIn, _: str = Depends(_require_admin)
):
    import bcrypt
    import secrets as _secrets

    pw_plain = _secrets.token_urlsafe(12)
    pw_hash = bcrypt.hashpw(pw_plain.encode(), bcrypt.gensalt()).decode()

    uid = users_repo().upsert(
        tenant_id, body.email, body.name, pw_hash, must_change=True
    )

    # Email the credentials
    html = f"""
    <p>You've been invited to CoachFlow.</p>
    <p>Login URL: <a href=\"{os.getenv('CLIENT_UI_ORIGIN', 'https://app.coachflow.nz')}/login\">{os.getenv('CLIENT_UI_ORIGIN', 'https://app.coachflow.nz')}/login</a></p>
    <p>Email: {body.email}<br/>Temporary password: <code>{pw_plain}</code></p>
    <p>You'll be asked to set a new password on first login.</p>
    """
    try:
        mailer().send(
            to=body.email,
            subject="Your CoachFlow login",
            html=html,
            text=f"Login: {os.getenv('CLIENT_UI_ORIGIN', 'https://app.coachflow.nz')}/login\nEmail: {body.email}\nPassword: {pw_plain}",
        )
    except Exception:
        pass
    # In development, optionally include the plaintext password in the response
    try:
        allow_pw = os.getenv("DEV_ALLOW_PW_RETURN", "").strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
    except Exception:
        allow_pw = False
    payload = {"ok": True, "user_id": uid}
    if allow_pw:
        payload["password"] = pw_plain
    return payload


class LoginIn(BaseModel):
    email: str
    password: str


@app.post("/api/auth/login")
async def client_login(resp: Response, body: LoginIn):
    import bcrypt

    u = users_repo().get_by_email(body.email)
    if not u or not bcrypt.checkpw(
        body.password.encode(), (u.get("password_hash") or "").encode()
    ):
        raise HTTPException(status_code=401, detail="invalid_credentials")
    tok = issue_client_session(u.get("id"))
    is_https = os.getenv("CLIENT_UI_ORIGIN", "").startswith("https://")
    dev_mode = (
        os.getenv("DEV_MODE", "").strip().lower() in {"1", "true", "yes", "on"}
    ) or bool(os.getenv("PYTEST_CURRENT_TEST"))
    # In dev, prefer SameSite=None to allow cross-origin cookies from client-ui (localhost:3002)
    same_site = "none" if (is_https or dev_mode) else "lax"
    resp.set_cookie(
        client_cookie_name(),
        tok,
        httponly=True,
        samesite=same_site,
        secure=False if dev_mode else is_https,
    )
    body_out = {
        "user": {"id": u.get("id"), "name": u.get("name"), "email": u.get("email")},
        "must_change_password": bool(u.get("must_change_password")),
    }
    # Dev helper: include session token so frontend can send Authorization header when cookies are blocked
    if dev_mode:
        body_out["session_token"] = tok
    return body_out


class ChangePasswordIn(BaseModel):
    new_password: str
    current_password: str | None = None


def _require_client(req: Request) -> Dict[str, Any]:
    # 1) Try cookie
    tok = req.cookies.get(client_cookie_name(), "")
    uid = verify_client_session(tok) or ""
    # 2) Dev fallback: Authorization header (Bearer|Client <token>)
    if not uid:
        try:
            auth = req.headers.get("authorization", "")
            if auth:
                scheme, _, token_val = auth.partition(" ")
                if scheme.lower() in {"bearer", "client"}:
                    uid = verify_client_session(token_val.strip()) or ""
        except Exception:
            pass
    # 3) Dev fallback: token query param (e.g., for EventSource which cannot set headers)
    if not uid:
        try:
            qp_tok = req.query_params.get("token") or ""
            uid = verify_client_session(qp_tok) or ""
        except Exception:
            pass
    if not uid:
        raise HTTPException(status_code=401, detail="unauthorized")
    return {"user_id": uid}


@app.post("/api/auth/dev-token")
async def issue_dev_token(ctx: Dict[str, Any] = Depends(_require_client)):
    """Dev-only helper to obtain a session token via existing cookie auth.

    Allows the frontend to populate localStorage with a token when cookies exist
    but Authorization headers are not yet configured.
    """
    dev_mode = (
        os.getenv("DEV_MODE", "").strip().lower() in {"1", "true", "yes", "on"}
    ) or bool(os.getenv("PYTEST_CURRENT_TEST"))
    if not dev_mode:
        raise HTTPException(status_code=404, detail="not_found")
    tok = issue_client_session(ctx["user_id"])
    return {"session_token": tok}


@app.post("/api/auth/change-password")
async def change_password(
    data: ChangePasswordIn, ctx: Dict[str, Any] = Depends(_require_client)
):
    import bcrypt

    u = users_repo().get_by_id(ctx["user_id"]) or {}
    if not u:
        raise HTTPException(status_code=401, detail="unauthorized")
    must_change = bool(u.get("must_change_password"))
    if not must_change:
        # require current password
        if not data.current_password:
            raise HTTPException(status_code=400, detail="current_password_required")
        if not bcrypt.checkpw(
            data.current_password.encode(), (u.get("password_hash") or "").encode()
        ):
            raise HTTPException(status_code=401, detail="invalid_credentials")
    new_hash = bcrypt.hashpw(data.new_password.encode(), bcrypt.gensalt()).decode()
    users_repo().update_password(u.get("id"), new_hash, must_change=False)
    return {"ok": True}


@app.get("/api/profile")
async def get_profile(ctx: Dict[str, Any] = Depends(_require_client)):
    u = users_repo().get_by_id(ctx["user_id"]) or {}
    stored = _user_prefs_store.get(ctx["user_id"], {})
    timezone = stored.get("timezone") or os.getenv("DEFAULT_TZ", "UTC")
    prefs = stored.get("preferences") or {
        "notificationsEmail": True,
        "global": {"askFirst": True, "proactiveness": "medium"},
        "domains": {},
    }
    # Derive legacy fields for compatibility
    try:
        risk = (prefs.get("global") or {}).get("proactiveness") or "medium"
        email_ask = ((prefs.get("domains") or {}).get("email") or {}).get("askFirst")
        never_auto = True if email_ask is True else False
        if isinstance(prefs, dict):
            prefs.setdefault("riskLevel", risk)
            prefs.setdefault("neverAutoSendEmails", never_auto)
    except Exception:
        pass
    return {
        "id": u.get("id"),
        "name": u.get("name") or "",
        "email": u.get("email") or "",
        "timezone": timezone,
        "preferences": prefs,
        "must_change_password": bool(u.get("must_change_password")),
    }


class AutomationSettingsIn(BaseModel):
    askFirst: Optional[bool] = None
    proactiveness: Optional[str] = Field(default=None, pattern="^(low|medium|high)$")


class PreferencesIn(BaseModel):
    notificationsEmail: Optional[bool] = None
    notificationsPush: Optional[bool] = None
    global_: Optional[AutomationSettingsIn] = Field(default=None, alias="global")
    domains: Optional[Dict[str, AutomationSettingsIn]] = None
    # legacy accepts
    riskLevel: Optional[str] = Field(default=None, pattern="^(low|medium|high)$")
    neverAutoSendEmails: Optional[bool] = None


class ProfilePatchIn(BaseModel):
    name: str | None = None
    timezone: Optional[str] = None
    preferences: Optional[PreferencesIn] = None


@app.patch("/api/profile")
async def patch_profile(
    body: ProfilePatchIn, ctx: Dict[str, Any] = Depends(_require_client)
):
    updated = users_repo().update_profile(
        ctx["user_id"], {k: v for k, v in body.model_dump().items() if v is not None}
    )
    # Merge and persist ephemeral prefs/timezone
    st = _user_prefs_store.get(ctx["user_id"], {})
    # timezone
    if body.timezone is not None:
        st["timezone"] = body.timezone
    # preferences
    if body.preferences is not None:
        prefs_in = body.preferences.model_dump(by_alias=True, exclude_none=True)
        cur = st.get("preferences") or {
            "notificationsEmail": True,
            "global": {"askFirst": True, "proactiveness": "medium"},
            "domains": {},
        }
        # Apply legacy mapping first if provided
        if "riskLevel" in prefs_in:
            cur.setdefault("global", {})
            cur["global"]["proactiveness"] = prefs_in["riskLevel"]
        if "neverAutoSendEmails" in prefs_in:
            cur.setdefault("domains", {})
            cur["domains"].setdefault("email", {})
            cur["domains"]["email"]["askFirst"] = bool(prefs_in["neverAutoSendEmails"])
        # Apply v2 fields
        if "notificationsEmail" in prefs_in:
            cur["notificationsEmail"] = prefs_in["notificationsEmail"]
        if "notificationsPush" in prefs_in:
            cur["notificationsPush"] = prefs_in["notificationsPush"]
        if "global" in prefs_in:
            cur.setdefault("global", {}).update(prefs_in["global"])  # type: ignore[arg-type]
        if "domains" in prefs_in:
            cur.setdefault("domains", {})
            for k, v in (prefs_in["domains"] or {}).items():
                cur["domains"].setdefault(k, {}).update(v)  # type: ignore[index]
        st["preferences"] = cur
    _user_prefs_store[ctx["user_id"]] = st

    # Build response using get_profile logic
    stored = _user_prefs_store.get(ctx["user_id"], {})
    timezone = stored.get("timezone") or os.getenv("DEFAULT_TZ", "UTC")
    prefs = stored.get("preferences") or {
        "notificationsEmail": True,
        "global": {"askFirst": True, "proactiveness": "medium"},
        "domains": {},
    }
    try:
        risk = (prefs.get("global") or {}).get("proactiveness") or "medium"
        email_ask = ((prefs.get("domains") or {}).get("email") or {}).get("askFirst")
        never_auto = True if email_ask is True else False
        if isinstance(prefs, dict):
            prefs.setdefault("riskLevel", risk)
            prefs.setdefault("neverAutoSendEmails", never_auto)
    except Exception:
        pass
    return {
        "id": updated.get("id", ctx["user_id"]),
        "name": updated.get("name") or "",
        "email": updated.get("email") or "",
        "timezone": timezone,
        "preferences": prefs,
        "must_change_password": bool(updated.get("must_change_password")),
    }


# Minimal stubs for client-ui Actions & Rules APIs
@app.get("/api/actions")
async def list_actions(
    status: Optional[str] = Query(default=None),
    ctx: Dict[str, Any] = Depends(_require_client),
):
    items = list(_user_actions_store.get(ctx["user_id"], []))
    if status:
        items = [a for a in items if str(a.get("status")) == status]
    return items


_user_event_queues: Dict[str, asyncio.Queue] = {}


def _get_event_queue(user_id: str) -> asyncio.Queue:
    q = _user_event_queues.get(user_id)
    if q is None:
        q = asyncio.Queue()
        _user_event_queues[user_id] = q
    return q


async def _publish_action_event(user_id: str, payload: Dict[str, Any]) -> None:
    try:
        q = _get_event_queue(user_id)
        await q.put(json.dumps(payload))
    except Exception:
        pass


@app.get("/api/actions/stream")
async def actions_stream(ctx: Dict[str, Any] = Depends(_require_client)):
    async def event_gen(user_id: str):
        q = _get_event_queue(user_id)
        while True:
            try:
                data = await asyncio.wait_for(q.get(), timeout=20)
                yield f"data: {data}\n\n"
            except asyncio.TimeoutError:
                yield ": keep-alive\n\n"

    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Content-Type": "text/event-stream",
    }
    return StreamingResponse(event_gen(ctx["user_id"]), headers=headers)


@app.get("/api/actions/{action_id}")
async def get_action(action_id: str, ctx: Dict[str, Any] = Depends(_require_client)):
    items = _user_actions_store.get(ctx["user_id"], [])
    it = next((a for a in items if a.get("id") == action_id), None)
    if not it:
        raise HTTPException(status_code=404, detail="not_found")
    return it


@app.post("/api/actions/{action_id}/accept")
async def accept_action(action_id: str, ctx: Dict[str, Any] = Depends(_require_client)):
    items = _user_actions_store.get(ctx["user_id"], [])
    for a in items:
        if a.get("id") == action_id:
            a["status"] = "accepted"
            await _publish_action_event(
                ctx["user_id"], {"event": "deleted", "action": {"id": action_id}}
            )
            return a
    raise HTTPException(status_code=404, detail="not_found")


@app.post("/api/actions/{action_id}/decline")
async def decline_action(
    action_id: str,
    reason: str | None = None,
    ctx: Dict[str, Any] = Depends(_require_client),
):
    items = _user_actions_store.get(ctx["user_id"], [])
    for a in items:
        if a.get("id") == action_id:
            a["status"] = "declined"
            if reason:
                a["metadata"] = {**(a.get("metadata") or {}), "reason": reason}
            await _publish_action_event(
                ctx["user_id"], {"event": "deleted", "action": {"id": action_id}}
            )
            return a
    raise HTTPException(status_code=404, detail="not_found")


@app.get("/api/rules")
async def list_rules(ctx: Dict[str, Any] = Depends(_require_client)):
    # Seed sensible defaults for the user in dev mode
    dev_mode = (
        os.getenv("DEV_MODE", "").strip().lower() in {"1", "true", "yes", "on"}
    ) or bool(os.getenv("PYTEST_CURRENT_TEST"))
    rules = _user_rules_store.get(ctx["user_id"]) or []
    if dev_mode and not rules:
        seeded = [
            {
                "id": str(uuid.uuid4()),
                "enabled": True,
                "priority": 1,
                "actionType": "email",
                "conditions": [
                    {"field": "subject", "op": "includes", "value": "follow up"}
                ],
                "outcome": "hold",
            },
            {
                "id": str(uuid.uuid4()),
                "enabled": True,
                "priority": 2,
                "actionType": "calendar",
                "conditions": [{"field": "duration", "op": "gt", "value": "45"}],
                "outcome": "accept",
            },
            {
                "id": str(uuid.uuid4()),
                "enabled": True,
                "priority": 3,
                "actionType": "task",
                "conditions": [
                    {"field": "title", "op": "regex", "value": "(?i)invoice|payment"}
                ],
                "outcome": "hold",
            },
        ]
        _user_rules_store[ctx["user_id"]] = seeded
        rules = seeded
    return rules


class RuleConditionIn(BaseModel):
    field: str
    op: str
    value: str


class RuleIn(BaseModel):
    enabled: bool = True
    actionType: str
    conditions: List[RuleConditionIn] = Field(default_factory=list)
    outcome: str
    priority: Optional[int] = None


class RulePatchIn(BaseModel):
    enabled: Optional[bool] = None
    actionType: Optional[str] = None
    conditions: Optional[List[RuleConditionIn]] = None
    outcome: Optional[str] = None
    priority: Optional[int] = None


class RulesReorderIn(BaseModel):
    order: List[str]


class RuleSuggestIn(BaseModel):
    description: Optional[str] = None
    sample: Optional[str] = None
    fields: Optional[Dict[str, str]] = None


@app.post("/api/rules")
async def create_rule(body: RuleIn, ctx: Dict[str, Any] = Depends(_require_client)):
    uid = ctx["user_id"]
    cur = _user_rules_store.get(uid) or []
    # Determine priority (1-based)
    new_priority = body.priority if (body.priority or 0) > 0 else (len(cur) + 1)
    rule = {
        "id": str(uuid.uuid4()),
        "enabled": bool(body.enabled),
        "priority": int(new_priority),
        "actionType": body.actionType,
        "conditions": [c.model_dump() for c in (body.conditions or [])],
        "outcome": body.outcome,
    }
    insert_index = max(0, min(len(cur), new_priority - 1))
    cur.insert(insert_index, rule)
    # Re-number priorities
    for i, r in enumerate(cur, start=1):
        r["priority"] = i
    _user_rules_store[uid] = cur
    return rule


@app.patch("/api/rules/{rule_id}")
async def update_rule(
    rule_id: str, body: RulePatchIn, ctx: Dict[str, Any] = Depends(_require_client)
):
    uid = ctx["user_id"]
    cur = _user_rules_store.get(uid) or []
    idx = next((i for i, r in enumerate(cur) if r.get("id") == rule_id), -1)
    if idx < 0:
        raise HTTPException(status_code=404, detail="not_found")
    rule = cur[idx]
    if body.enabled is not None:
        rule["enabled"] = bool(body.enabled)
    if body.actionType is not None:
        rule["actionType"] = body.actionType
    if body.conditions is not None:
        rule["conditions"] = [c.model_dump() for c in (body.conditions or [])]
    if body.outcome is not None:
        rule["outcome"] = body.outcome
    # Priority move
    if body.priority is not None and body.priority > 0:
        cur.pop(idx)
        insert_index = max(0, min(len(cur), body.priority - 1))
        cur.insert(insert_index, rule)
        for i, r in enumerate(cur, start=1):
            r["priority"] = i
    _user_rules_store[uid] = cur
    return rule


@app.post("/api/rules/reorder")
async def reorder_rules(
    body: RulesReorderIn, ctx: Dict[str, Any] = Depends(_require_client)
):
    uid = ctx["user_id"]
    cur = _user_rules_store.get(uid) or []
    id_to_rule = {r["id"]: r for r in cur}
    new_list: List[Dict[str, Any]] = []
    # Add specified order
    for rid in body.order:
        r = id_to_rule.pop(rid, None)
        if r is not None:
            new_list.append(r)
    # Append remaining in original relative order
    for r in cur:
        if r["id"] in id_to_rule:
            new_list.append(r)
            id_to_rule.pop(r["id"], None)
    for i, r in enumerate(new_list, start=1):
        r["priority"] = i
    _user_rules_store[uid] = new_list
    return {"success": True}


@app.post("/api/rules/suggest")
async def suggest_rules(
    body: RuleSuggestIn,
    _: Dict[str, Any] = Depends(_require_client),
):
    text_parts: List[str] = []
    if body.description:
        text_parts.append(body.description)
    if body.sample:
        text_parts.append(body.sample)
    if body.fields:
        text_parts.extend(str(value) for value in body.fields.values())
    haystack = " ".join(text_parts).lower()

    suggestions: List[Dict[str, Any]] = []

    if "invoice" in haystack or "payment" in haystack:
        suggestions.append(
            {
                "id": "suggest-hold-invoices",
                "title": "Hold invoices for review",
                "summary": "Pause any invoice-related emails so finance can double-check before sending.",
                "confidence": 0.85,
                "rule": {
                    "actionType": "email",
                    "outcome": "hold",
                    "conditions": [
                        {"field": "subject", "op": "includes", "value": "invoice"},
                        {"field": "body", "op": "includes", "value": "due"},
                    ],
                    "enabled": True,
                },
                "hints": [
                    "Add amount thresholds if you only want high-value invoices.",
                    "Include sender domains (e.g. @vendor.com) to reduce noise.",
                ],
            }
        )

    if "meeting" in haystack or "schedule" in haystack:
        suggestions.append(
            {
                "id": "suggest-schedule-meetings",
                "title": "Auto-suggest meeting slots",
                "summary": "Flag emails asking to schedule time and queue them for quick calendar suggestions.",
                "confidence": 0.72,
                "rule": {
                    "actionType": "email",
                    "outcome": "hold",
                    "conditions": [
                        {"field": "subject", "op": "includes", "value": "meeting"},
                        {"field": "body", "op": "includes", "value": "schedule"},
                    ],
                    "enabled": True,
                },
                "hints": [
                    "Layer on attendee keywords like 'availability' or 'reschedule'.",
                    "Route internal senders directly to auto-accept if low risk.",
                ],
            }
        )

    if "follow up" in haystack or "client" in haystack:
        suggestions.append(
            {
                "id": "suggest-client-follow-up",
                "title": "Prioritise client follow-ups",
                "summary": "Make sure anything mentioning client follow-ups gets surfaced quickly.",
                "confidence": 0.64,
                "rule": {
                    "actionType": "email",
                    "outcome": "hold",
                    "conditions": [
                        {"field": "subject", "op": "includes", "value": "follow up"},
                        {"field": "body", "op": "includes", "value": "client"},
                    ],
                    "enabled": True,
                },
                "hints": [
                    "Add account tier tags to fast-track VIP customers.",
                    "Combine with SLA metadata to enforce response times.",
                ],
            }
        )

    if not suggestions:
        suggestions.append(
            {
                "id": "suggest-default-priority",
                "title": "Escalate time-sensitive requests",
                "summary": "Catch emails that mention urgency so they surface above the noise.",
                "confidence": 0.5,
                "rule": {
                    "actionType": "email",
                    "outcome": "hold",
                    "conditions": [
                        {"field": "body", "op": "includes", "value": "urgent"},
                        {"field": "body", "op": "includes", "value": "asap"},
                    ],
                    "enabled": True,
                },
                "hints": [
                    "Swap in your preferred urgency keywords.",
                    "Add sender filters to ignore auto-generated alerts.",
                ],
            }
        )

    return suggestions


# Dev: push an email and create a pending action for the current user
@app.post("/dev/emails")
async def dev_push_email(
    email: DevEmailIn,  # accept body as DevEmailIn
    ctx: Dict[str, Any] = Depends(_require_client),
):
    uid = ctx["user_id"]
    items = _user_actions_store.get(uid) or []
    now = datetime.now(timezone.utc)
    received_at = email.received_at or now
    body_text = email.body_text or ""
    subject = email.subject or ""
    lower_body = body_text.lower()
    lower_subject = subject.lower()

    amounts = _extract_amounts(body_text)
    key_dates = _extract_dates(body_text)
    people = _extract_people(email.sender, body_text)

    attachments_info: Dict[str, Any] = {
        "count": len(email.attachments),
        "types": email.attachments,
    }
    if "attach" in lower_body and not email.attachments:
        attachments_info["missing"] = True

    matched_rule: Optional[Dict[str, Any]] = None
    matched_fields: List[Dict[str, Any]] = []
    risk_level = "low"
    risk_reason = "Routine triage"
    priority_score = 0.45
    sla = "Respond within 48h"
    saved_tags: List[str] = []

    if "invoice" in lower_subject or "invoice" in lower_body:
        matched_rule = {
            "id": "rule-invoice-follow-up",
            "name": "Invoice follow-up",
            "outcome": "hold",
            "fields": [
                {"field": "subject", "op": "includes", "value": "invoice"},
                {"field": "body", "op": "includes", "value": "due"},
            ],
            "confidence": 0.82,
            "reason": "Subject references invoice",
        }
        matched_fields = matched_rule["fields"]
        risk_level = "medium"
        risk_reason = "Contains an outstanding invoice"
        priority_score = 0.78
        sla = "Respond within 24h"
        saved_tags.extend(["finance", "overdue"])
    elif "meeting" in lower_subject or "schedule" in lower_body:
        matched_rule = {
            "id": "rule-meeting-scheduling",
            "name": "Scheduling request",
            "outcome": "hold",
            "fields": [
                {"field": "subject", "op": "includes", "value": "meeting"},
                {"field": "body", "op": "includes", "value": "schedule"},
            ],
            "confidence": 0.7,
            "reason": "Mentions scheduling",
        }
        matched_fields = matched_rule["fields"]
        risk_level = "low"
        risk_reason = "Scheduling request"
        priority_score = 0.6
        sla = "Offer times today"
        saved_tags.append("meetings")
    elif "follow up" in lower_subject or "client" in lower_body:
        matched_rule = {
            "id": "rule-client-follow-up",
            "name": "Client follow-up",
            "outcome": "hold",
            "fields": [
                {"field": "subject", "op": "includes", "value": "follow up"},
                {"field": "body", "op": "includes", "value": "client"},
            ],
            "confidence": 0.68,
            "reason": "Likely client follow-up",
        }
        matched_fields = matched_rule["fields"]
        risk_level = "medium"
        risk_reason = "Client-related follow-up"
        priority_score = 0.58
        sla = "Respond within 24h"
        saved_tags.append("client")

    confidence = matched_rule.get("confidence") if matched_rule else 0.6
    context_labels: List[str] = []
    if matched_rule and matched_rule.get("name"):
        context_labels.append(matched_rule["name"])
    if amounts:
        context_labels.append(f"Amount {amounts[0]}")

    proposed_label = (
        f"Follow up with {people[0]} about {subject}"
        if people
        else f"Follow up on {subject or 'this email'}"
    )
    proposed_next_step = {
        "label": proposed_label.strip(),
        "type": "reply",
        "dueWithin": "within 24h" if priority_score >= 0.7 else "this week",
        "reason": (matched_rule or {}).get("reason")
        or "Subject indicates a pending response",
        "draft": {
            "subject": subject or "Follow up",
            "body": (
                f"Hi {people[0] if people else 'there'},\n\nThanks for the update. "
                "I wanted to close the loop and confirm next steps."
            ),
        },
    }

    calendar_times = (
        _suggest_calendar_times(received_at) if "meetings" in saved_tags else []
    )

    summary_entities = {
        key: values
        for key, values in {
            "people": people,
            "amounts": amounts,
            "dates": key_dates,
        }.items()
        if values
    }

    due_at: Optional[str] = None
    if priority_score >= 0.75:
        due_at = (received_at + timedelta(hours=24)).isoformat()
    elif "meetings" in saved_tags:
        due_at = (received_at + timedelta(hours=6)).isoformat()

    saved_view_tags = sorted(set(saved_tags))

    metadata = {
        "sender": email.sender,
        "message_id": email.message_id,
        "subject": subject,
        "matchedRule": matched_rule,
        "matchedFields": (
            [field["field"] for field in matched_fields] if matched_fields else None
        ),
        "confidence": confidence,
        "contextLabels": context_labels,
        "inlinePreview": {
            "snippet": body_text[:160],
            "firstLine": (
                body_text.strip().splitlines()[0] if body_text.strip() else None
            ),
            "keyDates": key_dates,
            "attachmentsCount": attachments_info.get("count"),
        },
        "preview": {
            "text": body_text,
            "attachments": attachments_info,
            "keyDates": key_dates,
        },
        "summaryEntities": summary_entities,
        "attachments": attachments_info,
        "risk": {"level": risk_level, "reason": risk_reason, "score": priority_score},
        "priority": {"score": priority_score, "sla": sla},
        "statusAgeMinutes": max(1, int((now - received_at).total_seconds() / 60)),
        "proposedNextStep": proposed_next_step,
        "thread": {
            "id": email.message_id,
            "link": (
                f"mailto:{email.sender}?subject={urllib.parse.quote(subject)}"
                if email.sender
                else None
            ),
            "lastMessageSnippet": body_text[:200].strip() or None,
        },
        "calendarSuggestions": {
            "timezone": "UTC",
            "times": calendar_times,
        },
        "llmDrafts": _build_llm_drafts(subject, people, amounts),
        "whyThis": {
            "rule": matched_rule.get("name") if matched_rule else None,
            "fields": (
                [field["field"] for field in matched_fields] if matched_fields else None
            ),
            "confidence": confidence,
            "examples": [
                "Adjust keyword triggers or add sender exceptions if this was incorrect.",
                "Lower the confidence threshold for this rule to reduce noise.",
            ],
        },
        "quickNotes": [],
        "autoGroupKey": lower_subject or email.sender,
        "savedViewTags": saved_view_tags,
    }

    # Also compute simple rules outcome for status to retain compatibility
    def _field(field: str) -> str:
        src = {
            "subject": email.subject,
            "body": email.body_text,
            "body_text": email.body_text,
            "sender": email.sender,
        }
        return str(src.get(field, ""))

    def _passes(conds: List[Dict[str, Any]]) -> bool:
        for c in matched_fields or []:
            # Already matched above; treat as pass-through
            return True
        return False

    rules = sorted(
        list(_user_rules_store.get(uid) or []), key=lambda r: int(r.get("priority", 0))
    )
    matched = next(
        (
            r
            for r in rules
            if (r.get("actionType") in ("email", "any"))
            and _passes(r.get("conditions") or [])
        ),
        None,
    )
    outcome = (matched or {}).get("outcome") or "hold"

    action = {
        "id": str(uuid.uuid4()),
        "createdAt": now.isoformat(),
        "type": "email",
        "title": email.subject
        or (f"Email from {email.sender}" if email.sender else "New email"),
        "summary": body_text.strip()[:240],
        "metadata": metadata,
        "dueAt": due_at,
        "status": (
            "pending"
            if outcome == "hold"
            else ("accepted" if outcome == "accept" else "declined")
        ),
    }
    # Prepend newest
    items = [action] + items
    _user_actions_store[uid] = items
    if action["status"] == "pending":
        await _publish_action_event(uid, {"event": "pending", "action": action})
    return {
        "ok": True,
        "id": action["id"],
        "status": action["status"],
        "outcome": outcome,
    }


@app.get("/audit/{request_id}")
async def audit_get(request_id: str, _: str = Depends(_require_admin)):
    from infra.repos import factory

    repo = factory.audit_repo()
    return repo.get(request_id) or {"error": "not_found"}


@app.get("/oauth/start")
async def oauth_start(
    provider: str = Query(..., pattern="^(notion|nylas)$"),
    tenant_id: str = Query(TENANT_DEFAULT),
) -> Dict[str, Any]:
    state = state_store.new(provider, tenant_id)
    if provider == "notion":
        base = "https://api.notion.com/v1/oauth/authorize"
        dynamic_client_id = (
            os.getenv("NOTION_CLIENT_ID") or NOTION_CLIENT_ID or "test_client_id"
        )
        query = {
            "client_id": dynamic_client_id,
            "response_type": "code",
            "redirect_uri": NOTION_REDIRECT_URI,
            "owner": "user",
            "state": state,
        }
    else:
        base = f"{NYLAS_API_URL}/v3/connect/auth"
        query = {
            "client_id": NYLAS_CLIENT_ID or "test_client_id",
            "response_type": "code",
            "redirect_uri": NYLAS_REDIRECT_URI,
            "scope": "email.read_only calendar",
            "state": state,
        }
    return {"state": state, "authorize_url": f"{base}?{urllib.parse.urlencode(query)}"}


class OAuthCallbackIn(BaseModel):
    code: str
    state: str
    provider: str


@app.post("/oauth/callback")
async def oauth_callback(data: OAuthCallbackIn) -> Dict[str, Any]:
    ctx = state_store.pop(data.state)
    if not ctx or ctx.get("provider") != data.provider:
        raise HTTPException(status_code=401, detail="invalid_state")
    tenant_id = ctx["tenant_id"]
    if MOCK_OAUTH or data.provider not in ("notion", "nylas"):
        access_token = f"mock_access_token_for_{data.provider}"
        refresh_token = f"mock_refresh_token_for_{data.provider}"
    else:
        access_token = f"access_{data.provider}"
        refresh_token = f"refresh_{data.provider}"
    f, _key_used = fernet_from(ENCRYPTION_KEY)
    repo = connections_factory.repo()
    repo.upsert(
        tenant_id=tenant_id,
        provider=data.provider,
        access_token_encrypted=encrypt(f, access_token),
        refresh_token_encrypted=encrypt(f, refresh_token),
        meta={
            "obtained_via": "mock" if MOCK_OAUTH else "oauth",
            "code_len": len(data.code),
        },
    )
    return {"ok": True, "tenant_id": tenant_id, "provider": data.provider}


# Nylas Hosted Auth endpoints
@app.get("/oauth/nylas/start")
async def nylas_oauth_start(
    provider: str = Query(..., pattern="^(google|microsoft)$"),
    tenant_id: str = Query(TENANT_DEFAULT),
) -> RedirectResponse:
    """Start Nylas OAuth flow for Google or Microsoft."""

    # Generate CSRF state and store it
    state = state_store.new(
        f"nylas_{provider}", tenant_id, extra={"provider": provider}
    )

    # Provider-specific scopes
    scopes = {
        "google": "https://www.googleapis.com/auth/calendar https://www.googleapis.com/auth/gmail.readonly",
        "microsoft": "https://graph.microsoft.com/calendars.readwrite https://graph.microsoft.com/mail.read",
    }

    # Build Nylas OAuth URL
    params = {
        "client_id": NYLAS_CLIENT_ID,
        "provider": provider,
        "redirect_uri": NYLAS_REDIRECT_URI,
        "response_type": "code",
        "state": state,
        "scope": scopes[provider],
    }

    auth_url = f"{NYLAS_API_URL}/v3/connect/auth?{urllib.parse.urlencode(params)}"

    return RedirectResponse(url=auth_url, status_code=302)


@app.get("/oauth/nylas/callback")
async def nylas_oauth_callback(
    code: Optional[str] = Query(default=None),
    state: Optional[str] = Query(default=None),
    provider: Optional[str] = Query(default=None, pattern="^(google|microsoft)$"),
) -> RedirectResponse:
    """Handle Nylas OAuth callback and exchange code for tokens."""

    # Validate presence (provider may be omitted by Nylas; infer from state)
    if not code or not state:
        return RedirectResponse(
            url=f"{ADMIN_UI_ORIGIN}/oauth/error?reason=missing_code_or_state",
            status_code=302,
        )

    # Validate state and infer provider when not provided
    stored_state = state_store.pop(state)
    if not stored_state:
        raise HTTPException(status_code=400, detail="invalid_state")
    effective_provider = stored_state.get("provider")
    if provider and provider != effective_provider:
        raise HTTPException(status_code=400, detail="invalid_state")
    provider = provider or effective_provider

    tenant_id = stored_state.get("tenant_id", TENANT_DEFAULT)

    if MOCK_OAUTH:
        # Mock mode for testing
        grant_id = f"mock_grant_{secrets.token_hex(8)}"
        email = f"test@{provider}.com"
        scopes = ["calendar", "email"]

        access_token = f"mock_access_{secrets.token_hex(16)}"
        refresh_token = f"mock_refresh_{secrets.token_hex(16)}"
        grant = NylasGrant(
            grant_id=grant_id,
            provider=provider,
            email=email,
            scopes=scopes,
            access_token=access_token,
            refresh_token=refresh_token,
        )
    else:
        # Real Nylas token exchange
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{NYLAS_API_URL}/v3/connect/token",
                    data={
                        "client_id": NYLAS_CLIENT_ID,
                        "client_secret": NYLAS_CLIENT_SECRET,
                        "code": code,
                        "grant_type": "authorization_code",
                        "redirect_uri": NYLAS_REDIRECT_URI,
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
                response.raise_for_status()
                token_data = response.json()
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=400, detail=f"token_exchange_failed: {str(e)}"
            )

        # Extract grant info from Nylas response
        grant_id = token_data.get("grant_id")
        email = token_data.get("email")
        scopes = token_data.get("scope", "").split()
        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")

        if not grant_id or not email:
            raise HTTPException(status_code=400, detail="invalid_token_response")

        grant = NylasGrant(
            grant_id=grant_id,
            provider=provider,
            email=email,
            scopes=scopes,
            access_token=access_token,
            refresh_token=refresh_token,
        )

    # Persist grant
    grants_repo = nylas_grants_repo()
    grants_repo.create(grant)

    # Also persist connection for glanceable UI status and future API usage
    try:
        f, _ = fernet_from(ENCRYPTION_KEY)
        conn_repo = connections_factory.repo()
        conn_repo.upsert(
            tenant_id=tenant_id,
            provider="nylas",
            access_token_encrypted=encrypt(f, access_token),
            refresh_token_encrypted=(
                encrypt(f, refresh_token) if refresh_token else None
            ),
            meta={
                "grant_id": grant.grant_id,
                "email": grant.email,
                "scopes": grant.scopes,
            },
        )
    except Exception:
        # Non-fatal; connection presence affects badges but should not break OAuth
        pass

    # State already cleaned up by pop() above

    # Redirect to client-ui success page for end-user UX
    success_url = f"{CLIENT_UI_ORIGIN}/oauth/success?provider={provider}&email={urllib.parse.quote(grant.email)}&tenant_id={urllib.parse.quote(tenant_id)}"
    return RedirectResponse(url=success_url, status_code=302)


class AdminLoginIn(BaseModel):
    email: str
    secret: str


@app.post("/admin/login")
async def admin_login(
    resp: Response,
    email: str | None = None,
    secret: str | None = None,
    body: AdminLoginIn | None = None,
):
    import hmac as _h

    em = (body.email if body else email) or ""
    sc = (body.secret if body else secret) or ""
    # Treat empty env vars as unset and fall back to defaults
    expected_email = os.getenv("ADMIN_EMAIL") or ADMIN_EMAIL
    expected_secret = os.getenv("ADMIN_SECRET") or ADMIN_SECRET
    if os.getenv("PYTEST_CURRENT_TEST"):
        if (
            em
            and sc
            and em == expected_email
            and _h.compare_digest(sc, expected_secret)
        ):
            tok = issue_session(em)
            resp.set_cookie(cookie_name(), tok, httponly=True, samesite="lax")
            return {"ok": True, "email": em}
    # Reject missing inputs explicitly
    if not em or not sc:
        raise HTTPException(status_code=401, detail="invalid_credentials")
    if em != expected_email or not _h.compare_digest(sc, expected_secret):
        raise HTTPException(status_code=401, detail="invalid_credentials")
    tok = issue_session(em)
    # Use SameSite=None; Secure for production (HTTPS), SameSite=Lax for development (HTTP)
    is_https = os.getenv("ADMIN_UI_ORIGIN", "").startswith("https://")
    resp.set_cookie(
        cookie_name(),
        tok,
        httponly=True,
        samesite="none" if is_https else "lax",
        secure=is_https,
    )
    return {"ok": True, "email": em}


@app.post("/admin/logout")
async def admin_logout(resp: Response):
    resp.delete_cookie(cookie_name())
    return {"ok": True}


@app.get("/admin/me")
async def admin_me(_: str = Depends(_require_admin)):
    return {"email": ADMIN_EMAIL}


@app.post("/admin/tenants")
async def admin_create_tenant(name: str, _: str = Depends(_require_admin)):
    trepo = tenant_rules_factory.tenants_repo()
    try:
        tid = trepo.create(name)
        return {"id": tid, "name": name}
    except httpx.HTTPStatusError as e:  # type: ignore[name-defined]
        body = getattr(getattr(e, "response", None), "text", "") or str(e)
        raise HTTPException(
            status_code=400,
            detail=f"tenant_create_failed: {getattr(e, 'response', None).status_code if getattr(e, 'response', None) else ''} {body}",
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"tenant_create_failed: {e}")


@app.get("/admin/tenants")
async def admin_list_tenants(_: str = Depends(_require_admin)):
    trepo = tenant_rules_factory.tenants_repo()
    tenants = trepo.list()
    # Compute minimal status for glanceable UI
    from infra.repos import settings_factory as _sf
    from infra.repos import connections_factory as _cf

    srep = _sf.repo()
    crep = _cf.repo()
    enriched = []
    # Batch-fetch settings to reduce N round-trips
    try:
        ids = [t.get("id") for t in tenants]
        # Use batch settings fetch when available
        if hasattr(srep, "get_all_for_tenants"):
            settings_cache = srep.get_all_for_tenants(ids)  # type: ignore[attr-defined]
        else:
            settings_cache = {t.get("id"): srep.get_all(t.get("id")) for t in tenants}
    except Exception:
        settings_cache = {t.get("id"): srep.get_all(t.get("id")) for t in tenants}
    # Batch-fetch connections existence
    try:
        conn_flags = crep.list_exists_for_tenants(ids)  # type: ignore[attr-defined]
    except Exception:
        conn_flags = {}

    for t in tenants:
        tid = t.get("id")
        st = settings_cache.get(tid) or {}
        has_db_ids = bool(
            st.get("notion_tasks_db_id")
            and st.get("notion_crm_db_id")
            and st.get("notion_sessions_db_id")
        )
        has_client_email = bool(st.get("client_email"))
        flags = conn_flags.get(tid) or {}
        has_notion = bool(flags.get("notion"))
        has_nylas = bool(flags.get("nylas"))
        complete = has_client_email and has_db_ids and has_notion and has_nylas
        overall = (
            "complete"
            if complete
            else (
                "partial"
                if any([has_client_email, has_db_ids, has_notion, has_nylas])
                else "blocked"
            )
        )
        enriched.append(
            {
                **t,
                "status": {
                    "has_client_email": has_client_email,
                    "has_db_ids": has_db_ids,
                    "has_notion_connection": has_notion,
                    "has_nylas_connection": has_nylas,
                    "overall_status": overall,
                },
            }
        )
    return {"tenants": enriched}


@app.delete("/admin/tenants/purge-test")
async def admin_purge_test_tenants(_: str = Depends(_require_admin)):
    """Dangerous: remove tenants with name containing 'Acme'. For test cleanup only."""
    trepo = tenant_rules_factory.tenants_repo()
    # Only supported by SupabaseTenantsRepo via direct REST delete; fallback is no-op
    try:
        from infra.supabase.tenants_repo import SupabaseTenantsRepo

        if isinstance(trepo, SupabaseTenantsRepo):  # type: ignore
            import httpx

            r = httpx.delete(
                f"{trepo._base}/tenants",  # type: ignore[attr-defined]
                headers=trepo._headers,  # type: ignore[attr-defined]
                params={"name": "ilike.%Acme%"},
                timeout=10,
            )
            r.raise_for_status()
            return {"ok": True, "deleted": True}
    except Exception:
        pass
    return {"ok": False, "deleted": False}


@app.get("/admin/tenants/{tenant_id}/rules")
async def admin_get_rules(tenant_id: str, _: str = Depends(_require_admin)):
    rrepo = tenant_rules_factory.rules_repo()
    return {"yaml": rrepo.get_yaml(tenant_id)}


@app.get("/config/rules.sample.yaml")
async def get_sample_rules():
    """Serve the sample rules file for admin UI"""
    import os

    sample_path = os.path.join(
        os.path.dirname(__file__), "../../config/rules.sample.yaml"
    )
    try:
        with open(sample_path, "r") as f:
            content = f.read()
        return Response(content=content, media_type="text/yaml")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Sample rules file not found")


class RulesIn(BaseModel):
    yaml_text: str


@app.put("/admin/tenants/{tenant_id}/rules")
async def admin_set_rules(
    tenant_id: str, body: RulesIn, _: str = Depends(_require_admin)
):
    trepo = tenant_rules_factory.tenants_repo()
    if not trepo.exists(tenant_id):
        raise HTTPException(status_code=404, detail="tenant_not_found")
    try:
        cfg = yaml.safe_load(body.yaml_text) or {}
        if not isinstance(cfg, dict):
            raise ValueError("rules must be a mapping")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"invalid_yaml: {e}")
    rrepo = tenant_rules_factory.rules_repo()
    rrepo.set_yaml(tenant_id, body.yaml_text)
    return {"ok": True}


@app.get("/admin/tenants/{tenant_id}/config")
async def admin_get_config(tenant_id: str, _: str = Depends(_require_admin)):
    """Get tenant Notion configuration YAML."""
    trepo = tenant_rules_factory.tenants_repo()
    if not trepo.exists(tenant_id):
        raise HTTPException(status_code=404, detail="tenant_not_found")

    from infra.repos import settings_factory

    settings_repo = settings_factory.repo()
    yaml_content = settings_repo.get(tenant_id, "notion_config_yaml") or ""
    # Also include glanceable status for setup screen
    from infra.repos import connections_factory as _cf

    s = settings_repo.get_all(tenant_id)
    crep = _cf.repo()
    has_db_ids = bool(
        (s or {}).get("notion_tasks_db_id")
        and (s or {}).get("notion_crm_db_id")
        and (s or {}).get("notion_sessions_db_id")
    )
    has_client_email = bool((s or {}).get("client_email"))
    has_notion = bool(crep.list_for_tenant(tenant_id, "notion"))
    has_nylas = bool(crep.list_for_tenant(tenant_id, "nylas"))
    complete = has_client_email and has_db_ids and has_notion and has_nylas
    overall = (
        "complete"
        if complete
        else (
            "partial"
            if any([has_client_email, has_db_ids, has_notion, has_nylas])
            else "blocked"
        )
    )
    # Resolve tenant name for UI convenience
    try:
        _trepo = tenant_rules_factory.tenants_repo()
        # Prefer repo.exists + list to avoid fetching all tenants when cheap exists is available
        # Fallback gracefully to tenant_id when not found
        _tname = None
        try:
            # Attempt to find by scanning list (small cardinality expected)
            _tname = next(
                (
                    t.get("name")
                    for t in _trepo.list()
                    if t.get("id") == tenant_id and t.get("name")
                ),
                None,
            )
        except Exception:
            _tname = None
        _tname = _tname or tenant_id
    except Exception:
        _tname = tenant_id
    return {
        "yaml": yaml_content,
        "name": _tname,
        "status": {
            "has_client_email": has_client_email,
            "has_db_ids": has_db_ids,
            "has_notion_connection": has_notion,
            "has_nylas_connection": has_nylas,
            "overall_status": overall,
        },
    }


class ConfigIn(BaseModel):
    yaml: str


@app.put("/admin/tenants/{tenant_id}/config")
async def admin_put_config(
    tenant_id: str, body: ConfigIn, _: str = Depends(_require_admin)
):
    """Save tenant Notion configuration YAML."""
    trepo = tenant_rules_factory.tenants_repo()
    if not trepo.exists(tenant_id):
        raise HTTPException(status_code=404, detail="tenant_not_found")

    try:
        from core.config.loader import save_for_tenant

        save_for_tenant(tenant_id, body.yaml or "")
        return {"ok": True}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/admin/tenants/{tenant_id}/notion/validate")
async def admin_validate_notion_config(
    tenant_id: str, _: str = Depends(_require_admin)
):
    """Validate Notion configuration against actual Notion database schemas."""
    trepo = tenant_rules_factory.tenants_repo()
    if not trepo.exists(tenant_id):
        raise HTTPException(status_code=404, detail="tenant_not_found")

    from core.config.loader import load_for_tenant
    from infra.repos import connections_factory
    import httpx

    cfg = load_for_tenant(tenant_id)
    if not cfg or not cfg.notion:
        return {"ok": False, "error": "no_config_found"}

    # Get Notion token from connections
    conn_repo = connections_factory.repo()
    connections = conn_repo.list_for_tenant(tenant_id, "notion")
    if not connections:
        return {"ok": False, "error": "no_notion_connection"}

    # Use the first Notion connection
    conn = connections[0]
    from utils.crypto import decrypt
    from settings import ENCRYPTION_KEY
    from cryptography.fernet import Fernet

    f = Fernet(ENCRYPTION_KEY.encode())
    access_token = decrypt(f, conn.access_token_encrypted)

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }

    results = {"ok": True, "databases": {}}

    try:
        with httpx.Client(timeout=10) as client:
            # Validate each database
            for db_name, db_cfg in [
                ("tasks", cfg.notion.tasks),
                ("clients", cfg.notion.clients),
                ("sessions", cfg.notion.sessions),
            ]:
                try:
                    # Get database schema
                    r = client.get(
                        f"https://api.notion.com/v1/databases/{db_cfg.db_id}",
                        headers=headers,
                    )
                    r.raise_for_status()
                    db_info = r.json()

                    # Check which properties exist
                    existing_props = set(db_info.get("properties", {}).keys())
                    configured_props = set(db_cfg.props.values())

                    missing = configured_props - existing_props
                    extra = existing_props - configured_props

                    results["databases"][db_name] = {
                        "db_id": db_cfg.db_id,
                        "title": db_info.get("title", [{}])[0].get(
                            "plain_text", "Unknown"
                        ),
                        "configured_props": list(configured_props),
                        "missing_props": list(missing),
                        "extra_props": list(extra),
                        "ok": len(missing) == 0,
                    }

                except httpx.HTTPStatusError as e:
                    results["databases"][db_name] = {
                        "db_id": db_cfg.db_id,
                        "error": f"HTTP {e.response.status_code}: {e.response.text}",
                        "ok": False,
                    }
                except Exception as e:
                    results["databases"][db_name] = {
                        "db_id": db_cfg.db_id,
                        "error": str(e),
                        "ok": False,
                    }

        # Overall status
        results["ok"] = all(db.get("ok", False) for db in results["databases"].values())

    except Exception as e:
        results = {"ok": False, "error": str(e)}

    return results


class EmailIn(BaseModel):
    message_id: str
    sender: str
    subject: str = ""
    body_text: str = ""
    received_at: str = ""


@app.post("/admin/tenants/{tenant_id}/triage/dry-run")
async def admin_triage_dry_run(
    tenant_id: str, email: EmailIn, _: str = Depends(_require_admin)
):
    trepo = tenant_rules_factory.tenants_repo()
    if not trepo.exists(tenant_id):
        raise HTTPException(status_code=404, detail="tenant_not_found")
    rrepo = tenant_rules_factory.rules_repo()
    yaml_text = rrepo.get_yaml(tenant_id)
    cfg = {}
    if yaml_text:
        import yaml as _yaml

        cfg = _yaml.safe_load(yaml_text) or {}
    env = EmailEnvelope(**email.model_dump())
    res = triage_email(env, cfg=cfg)
    return {"triage": res.dict()}


@app.get("/connect")
async def connect(provider: str, tenant_id: str = TENANT_DEFAULT):
    if provider not in ("notion", "nylas"):
        raise HTTPException(status_code=400, detail="unsupported_provider")
    state = state_store.new(provider, tenant_id)
    if provider == "notion":
        base = "https://api.notion.com/v1/oauth/authorize"
        query = {
            "client_id": NOTION_CLIENT_ID or "test_client_id",
            "response_type": "code",
            "redirect_uri": NOTION_REDIRECT_URI,
            "owner": "user",
            "state": state,
        }
    else:
        base = f"{NYLAS_API_URL}/v3/connect/auth"
        query = {
            "client_id": NYLAS_CLIENT_ID or "test_client_id",
            "response_type": "code",
            "redirect_uri": NYLAS_REDIRECT_URI,
            "scope": "email.read_only calendar",
            "state": state,
        }
    url = f"{base}?{urllib.parse.urlencode(query)}"
    return RedirectResponse(url=url, status_code=307)


@app.get("/admin/tenants/{tenant_id}/settings")
async def admin_get_settings(tenant_id: str, _: str = Depends(_require_admin)):
    repo = settings_factory.repo()
    return {"settings": repo.get_all(tenant_id)}


class SettingsIn(BaseModel):
    data: Dict[str, str]


@app.put("/admin/tenants/{tenant_id}/settings")
async def admin_set_settings(
    tenant_id: str, body: SettingsIn, _: str = Depends(_require_admin)
):
    trepo = tenant_rules_factory.tenants_repo()
    if not trepo.exists(tenant_id):
        raise HTTPException(status_code=404, detail="tenant_not_found")
    allowed = {
        "client_email",
        "notion_tasks_db_id",
        "notion_crm_db_id",
        "notion_sessions_db_id",
    }
    data = {k: v for k, v in (body.data or {}).items() if k in allowed}
    repo = settings_factory.repo()
    try:
        repo.set_many(tenant_id, data)
        return {"ok": True}
    except Exception as e:
        # Surface persistence errors to client with 400 to keep CORS headers present
        raise HTTPException(status_code=400, detail=str(e))


class InviteIn(BaseModel):
    to_email: str
    message: str | None = None


@app.post("/admin/tenants/{tenant_id}/invite")
async def admin_send_invite(
    tenant_id: str, body: InviteIn, req: Request, _: str = Depends(_require_admin)
):
    base = str(req.base_url).rstrip("/")
    links = {
        "notion": f"{base}/connect?provider=notion&tenant_id={tenant_id}",
        # Prefer hosted Nylas start which issues state and redirects to login.nylas.com
        "nylas": f"{base}/oauth/nylas/start?provider=google&tenant_id={tenant_id}",
    }
    # Resolve tenant name for friendlier email greeting
    try:
        trepo = tenant_rules_factory.tenants_repo()
        tenant_name = None
        try:
            tenant_name = next(
                (
                    t.get("name")
                    for t in trepo.list()
                    if t.get("id") == tenant_id and t.get("name")
                ),
                None,
            )
        except Exception:
            tenant_name = None
        tenant_name = tenant_name or tenant_id
    except Exception:
        tenant_name = tenant_id
    html, text, subject = render_onboarding_email(
        tenant_name, links, body.message or ""
    )
    m = mailer()
    send_kwargs = {"to": body.to_email, "subject": subject, "html": html, "text": text}
    token = os.getenv("POSTMARK_SERVER_TOKEN")
    # Include MessageStream when using Postmark and the mailer supports it
    if token:
        sig = inspect.signature(m.send)
        if "message_stream" in sig.parameters:
            send_kwargs["message_stream"] = os.getenv(
                "POSTMARK_MESSAGE_STREAM", "outbound"
            )
    # Log which mailer is being used (and whether Postmark token is present)
    try:
        logging.getLogger(__name__).info(
            "invite: using mailer=%s postmark_token=%s",
            type(m).__name__,
            "present" if token else "absent",
        )
    except Exception:
        pass
    # Always surface failures so they don't fail silently
    try:
        m.send(**send_kwargs)
    except httpx.HTTPStatusError as exc:  # type: ignore[attr-defined]
        # Log details but avoid leaking provider responses in API errors
        body = getattr(getattr(exc, "response", None), "text", "") or str(exc)
        logging.getLogger(__name__).exception("invite: postmark error %s", body)
        raise HTTPException(status_code=502, detail="invite_send_failed") from exc
    except Exception as exc:
        logging.getLogger(__name__).exception("invite: mailer send failed")
        raise HTTPException(status_code=502, detail="invite_send_failed") from exc
    # Do not let persistence errors bubble up as 500s (which hide CORS headers)
    try:
        settings_factory.repo().set_many(tenant_id, {"client_email": body.to_email})
    except Exception:
        # Log if you have logging; keep the response successful for UX
        return {"ok": True, "links": links, "warning": "settings_persist_failed"}
    return {"ok": True, "links": links}


@app.get("/admin/debug/mailer")
async def admin_debug_mailer(_: str = Depends(_require_admin)):
    """Return mailer configuration info to help diagnose delivery issues."""
    m = mailer()

    def _is_true(v: str | None) -> bool:
        return (v or "").strip().lower() in {"1", "true", "yes", "on"}

    tok = os.getenv("POSTMARK_SERVER_TOKEN") or ""
    return {
        "mailer": type(m).__name__,
        "postmark_token_present": bool(tok),
        "postmark_token_len": len(tok),
        "use_postmark_flag": _is_true(os.getenv("USE_POSTMARK")),
        "use_smtp_flag": _is_true(os.getenv("USE_SMTP")),
        "from_email": os.getenv("POSTMARK_FROM_EMAIL") or os.getenv("SMTP_FROM", ""),
        "message_stream": os.getenv("POSTMARK_MESSAGE_STREAM", "outbound"),
    }


@app.get("/admin/debug/oauth")
async def admin_debug_oauth(_: str = Depends(_require_admin)):
    return {
        "notion": {
            "client_id_present": bool(
                os.getenv("NOTION_CLIENT_ID") or NOTION_CLIENT_ID
            ),
            "redirect_uri": NOTION_REDIRECT_URI,
        },
        "nylas": {
            "client_id_present": bool(NYLAS_CLIENT_ID),
            "redirect_uri": NYLAS_REDIRECT_URI,
            "api_url": NYLAS_API_URL,
        },
    }


@app.get("/admin/debug/supabase-key")
async def admin_debug_supabase_key(_: str = Depends(_require_admin)):
    """Return minimal info about the configured Supabase key to verify role."""
    import base64

    info: Dict[str, Any] = {
        "present": bool(os.getenv("SUPABASE_SERVICE_KEY") or SUPABASE_SERVICE_KEY),
        "prefix": (os.getenv("SUPABASE_SERVICE_KEY") or SUPABASE_SERVICE_KEY)[:8],
    }
    try:
        tok = (os.getenv("SUPABASE_SERVICE_KEY") or SUPABASE_SERVICE_KEY).split(".")
        if len(tok) >= 2:
            pad = "=" * (-len(tok[1]) % 4)
            payload = json.loads(base64.urlsafe_b64decode(tok[1] + pad).decode())
            info["jwt_role"] = payload.get("role") or payload.get("user_role")
            info["iss"] = payload.get("iss")
        else:
            info["jwt_role"] = None
    except Exception:
        info["jwt_role"] = None
    return info


@app.get("/admin/debug/db-latency")
async def admin_debug_db_latency(_: str = Depends(_require_admin)):
    import time
    from infra.repos import settings_factory as _sf
    from infra.repos import tenant_rules_factory as _tf

    results = {}
    start = time.perf_counter()
    try:
        _tf.tenants_repo().list()
        results["tenants_list_ms"] = round((time.perf_counter() - start) * 1000)
    except Exception as e:
        results["tenants_list_error"] = str(e)

    start = time.perf_counter()
    try:
        # arbitrary UUID unlikely to exist; just test response time
        _sf.repo().get_all("00000000-0000-0000-0000-000000000000")
        results["settings_get_ms"] = round((time.perf_counter() - start) * 1000)
    except Exception as e:
        results["settings_get_error"] = str(e)

    return {"ok": True, **results}


@app.get("/oauth/notion/start")
async def notion_oauth_start(
    tenant_id: str = Query(TENANT_DEFAULT),
) -> RedirectResponse:
    """Start Notion OAuth flow."""
    state = state_store.new("notion", tenant_id)
    params = {
        "client_id": NOTION_CLIENT_ID,
        "response_type": "code",
        "owner": "user",
        "redirect_uri": NOTION_REDIRECT_URI,
        "state": state,
    }
    url = f"https://api.notion.com/v1/oauth/authorize?{urllib.parse.urlencode(params)}"
    return RedirectResponse(url=url, status_code=302)


@app.get("/oauth/notion/callback")
async def notion_oauth_callback(
    code: str = Query(...),
    state: str = Query(...),
) -> RedirectResponse:
    """Handle Notion OAuth callback, exchange code, and persist tokens."""
    ctx = state_store.pop(state)
    if not ctx or ctx.get("provider") not in (None, "notion"):
        # legacy states may not store provider; allow when missing but disallow mismatches
        raise HTTPException(status_code=400, detail="invalid_state")
    tenant_id = ctx.get("tenant_id", TENANT_DEFAULT)

    if MOCK_OAUTH:
        access_token = f"mock_notion_access_{secrets.token_hex(8)}"
        refresh_token = f"mock_notion_refresh_{secrets.token_hex(8)}"
        workspace_id = f"mock_workspace_{secrets.token_hex(4)}"
        expires_at = None
    else:
        try:
            basic_auth = httpx.BasicAuth(NOTION_CLIENT_ID, NOTION_CLIENT_SECRET)
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    "https://api.notion.com/v1/oauth/token",
                    json={
                        "grant_type": "authorization_code",
                        "code": code,
                        "redirect_uri": NOTION_REDIRECT_URI,
                    },
                    auth=basic_auth,
                    headers={"Accept": "application/json"},
                )
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPError as e:
            body = getattr(getattr(e, "response", None), "text", "") or str(e)
            raise HTTPException(
                status_code=400,
                detail=f"token_exchange_failed: {getattr(e, 'response', None).status_code if getattr(e, 'response', None) else ''} {body}",
            )

        access_token = data.get("access_token")
        refresh_token = data.get("refresh_token")
        expires_at = data.get("expires_in")  # seconds; optional
        workspace_id = data.get("workspace_id") or (data.get("bot") or {}).get(
            "workspace_id"
        )
        if not access_token or not workspace_id:
            raise HTTPException(status_code=400, detail="invalid_token_response")

    f, _ = fernet_from(ENCRYPTION_KEY)
    repo = connections_factory.repo()
    meta = {"workspace_id": workspace_id}
    if expires_at is not None:
        meta["expires_in"] = expires_at

    repo.upsert(
        tenant_id=tenant_id,
        provider="notion",
        access_token_encrypted=encrypt(f, access_token),
        refresh_token_encrypted=encrypt(f, refresh_token) if refresh_token else None,
        meta=meta,
    )

    # Redirect clients to the client-ui success screen
    success_url = f"{CLIENT_UI_ORIGIN}/oauth/success?provider=notion&tenant_id={urllib.parse.quote(tenant_id)}"
    return RedirectResponse(url=success_url, status_code=302)


@app.get("/oauth/callback")
async def legacy_oauth_callback(
    req: Request,
    code: str = Query(...),
    state: str = Query(...),
    provider: str | None = Query(default=None),
) -> RedirectResponse:
    """Backward-compatible GET callback handler.

    Some older integrations may still send users to /oauth/callback as a GET.
    Redirect to the provider-specific GET callback to avoid 405s.
    """
    base = str(req.base_url).rstrip("/")
    if provider in (None, "notion"):
        return RedirectResponse(
            url=f"{base}/oauth/notion/callback?code={urllib.parse.quote(code)}&state={urllib.parse.quote(state)}",
            status_code=307,
        )
    if provider == "nylas":
        # Classic Nylas (non-hosted) flows used /oauth/callback; redirect is not applicable here.
        # Prefer the existing hosted callback route when applicable.
        return RedirectResponse(
            url=f"{ADMIN_UI_ORIGIN}/oauth/error?reason=use_nylas_hosted",
            status_code=302,
        )
    return RedirectResponse(
        url=f"{ADMIN_UI_ORIGIN}/oauth/error?reason=unsupported_provider",
        status_code=302,
    )
