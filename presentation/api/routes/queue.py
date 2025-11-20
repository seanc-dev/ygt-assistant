"""Queue (Action Items) endpoints."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import uuid
import logging
import asyncio
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, Field
from settings import DEFAULT_TZ
from presentation.api.repos import user_settings, audit_log, workroom
from presentation.api.routes.llm_contract_support import build_contract_payload
from presentation.api.utils.defer import compute_defer_until
from presentation.api.stores import proposed_blocks_store
from core.chat.context import (
    load_thread_context,
    save_thread_context,
    update_thread_context_with_refs,
)
from core.chat.focus import UiContext, resolve_focus_candidates
from core.chat.tokens import parse_message_with_tokens
from core.chat.validation import ValidationOk, validate_parsed_message

logger = logging.getLogger(__name__)
router = APIRouter()

# Thread-level lock to prevent concurrent assistant response generation
_assistant_lock: Dict[str, asyncio.Lock] = {}
_lock_lock = asyncio.Lock()  # Lock for managing the lock dictionary


async def _get_thread_lock(thread_id: str) -> asyncio.Lock:
    """Get or create a lock for a specific thread."""
    async with _lock_lock:
        if thread_id not in _assistant_lock:
            _assistant_lock[thread_id] = asyncio.Lock()
        return _assistant_lock[thread_id]


def _get_user_id(request: Request) -> str:
    """Get user ID from request (stub - will use auth in Phase 5)."""
    return request.cookies.get("user_id") or "default"

# In-memory queue store (will be replaced with DB in Phase 2+)
queue_store: Dict[str, Dict[str, Any]] = {}
defer_store: Dict[str, Dict[str, Any]] = {}  # action_id -> defer info


class ActionItem(BaseModel):
    """Action item model."""
    action_id: str = Field(..., description="UUID")
    source: str = Field(..., description="email|teams|doc")
    category: str = Field(..., description="needs_response|needs_approval|fyi")
    priority: str = Field(..., description="low|medium|high")
    preview: str
    thread_id: Optional[str] = None
    defer_until: Optional[str] = None  # ISO datetime
    defer_bucket: Optional[str] = None  # afternoon|tomorrow|this_week|next_week
    added_to_today: Optional[bool] = None


class DeferRequest(BaseModel):
    bucket: str = Field(..., description="afternoon|tomorrow|this_week|next_week")


class AddToTodayRequest(BaseModel):
    kind: str = Field(..., description="admin|work")
    tasks: Optional[List[str]] = None


@router.get("/api/queue")
async def get_queue(
    request: Request,
    limit: int = 5,
    offset: int = 0,
    user_id: str = Depends(_get_user_id),
    use_unified: bool = False,
) -> Dict[str, Any]:
    """Get queue of action items.
    
    Returns action items from Outlook, Teams, and Docs change summaries.
    Keeps ≤5 visible; preloads 10.
    
    Query params:
    - limit: Number of items to return (default: 5)
    - offset: Offset for pagination (default: 0)
    - use_unified: If true, fetch from unified sources (default: false, uses queue_store)
    """
    # If mock DB is available (for testing), use it
    try:
        from llm_testing.mock_db import get_mock_client
        from presentation.api.repos.queue import _resolve_identity
        
        tenant_id, resolved_user_id = _resolve_identity(user_id)
        mock_db = get_mock_client()
        
        # Get action items from mock DB
        action_items = mock_db._tables.get("action_items", [])
        # Filter by tenant and owner
        user_items = [
            item for item in action_items
            if item.get("tenant_id") == tenant_id and item.get("owner_id") == resolved_user_id
        ]
        
        # Convert to queue format
        queue_items = []
        for item in user_items:
            queue_items.append({
                "action_id": item["id"],
                "source": item.get("source_type", "email"),
                "category": "needs_response",
                "priority": item.get("priority", "medium"),
                "preview": item.get("payload", {}).get("preview", ""),
                "created_at": item.get("created_at", datetime.now(timezone.utc).isoformat()),
            })
        
        # Sort by priority and creation time
        queue_items.sort(key=lambda x: (
            {"high": 0, "medium": 1, "low": 2}.get(x.get("priority", "medium"), 1),
            x.get("created_at", "")
        ))
        
        total = len(queue_items)
        items = queue_items[offset:offset + limit]
        
        return {
            "ok": True,
            "items": items,
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    except (ImportError, AttributeError, RuntimeError):
        # Mock DB not available - fall through to in-memory queue_store
        pass
    
    # If use_unified is true, fetch from unified sources
    if use_unified:
        try:
            from presentation.api.services.unified_actions import generate_unified_action_items
            unified_items = await generate_unified_action_items(user_id, days=7)
            
            # Merge with existing queue_store items
            for item in unified_items:
                if item["action_id"] not in queue_store:
                    queue_store[item["action_id"]] = {
                        **item,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    }
        except Exception:
            pass  # Fallback to queue_store if unified fails
    
    # Filter out deferred items that haven't resurfaced yet
    try:
        tz = ZoneInfo(DEFAULT_TZ)
    except Exception:
        tz = timezone.utc
    now = datetime.now(tz)
    visible_items = []
    for item in queue_store.values():
        defer_info = defer_store.get(item["action_id"])
        if defer_info and defer_info.get("defer_until"):
            defer_until = datetime.fromisoformat(defer_info["defer_until"].replace("Z", "+00:00"))
            if defer_until > now:
                continue  # Skip items not yet resurfaced
        visible_items.append(item)
    
    # Sort by priority and creation time
    visible_items.sort(key=lambda x: (
        {"high": 0, "medium": 1, "low": 2}.get(x.get("priority", "medium"), 1),
        x.get("created_at", "")
    ))
    
    total = len(visible_items)
    sliced_items = visible_items[offset:offset + limit]
    task_title_cache: Dict[str, Optional[str]] = {}

    response_items = []
    for item in sliced_items:
        entry = {
            "action_id": item["action_id"],
            "source": item.get("source"),
            "category": item.get("category"),
            "priority": item.get("priority"),
            "preview": item.get("preview"),
            "thread_id": item.get("thread_id"),
            "defer_until": item.get("defer_until"),
            "defer_bucket": item.get("defer_bucket"),
            "added_to_today": item.get("added_to_today"),
        }

        linked_task_id = item.get("task_id")
        if linked_task_id:
            entry["task_id"] = linked_task_id
            task_title = item.get("task_title") or task_title_cache.get(linked_task_id)
            if task_title is None:
                try:
                    task = workroom.get_task(user_id, linked_task_id)
                    task_title = task.get("title")
                    task_title_cache[linked_task_id] = task_title
                except ValueError:
                    task_title = None
            if task_title:
                entry["task_title"] = task_title

        response_items.append(entry)
    
    return {
        "ok": True,
        "items": response_items,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.post("/api/queue/{action_id}/defer")
async def defer_action(
    action_id: str,
    body: DeferRequest,
    request: Request,
    user_id: str = Depends(_get_user_id),
) -> Dict[str, Any]:
    """Defer an action item.
    
    Computes defer_until based on bucket and user settings.
    Persists defer info and audits.
    """
    if action_id not in queue_store:
        raise HTTPException(status_code=404, detail="action_not_found")
    
    user_settings_data = user_settings.get_settings(user_id)
    try:
        tz = ZoneInfo(user_settings_data.get("time_zone", DEFAULT_TZ))
    except Exception:
        tz = timezone.utc
    now = datetime.now(tz)
    
    defer_until_iso, defer_bucket = compute_defer_until(
        body.bucket, now, user_settings_data
    )
    
    # If bucket is hidden, return error
    if defer_until_iso is None:
        raise HTTPException(
            status_code=400,
            detail=f"Defer bucket '{body.bucket}' is not available at this time"
        )
    
    request_id = getattr(request.state, "request_id", None)
    
    defer_store[action_id] = {
        "action_id": action_id,
        "defer_until": defer_until_iso,
        "defer_bucket": defer_bucket,
    }
    
    # Update queue item
    queue_store[action_id]["defer_until"] = defer_until_iso
    queue_store[action_id]["defer_bucket"] = defer_bucket
    
    # Write audit log
    audit_log.write_audit(
        "defer",
        {
            "action_id": action_id,
            "bucket": body.bucket,
            "defer_until": defer_until_iso,
            "user_id": user_id,
        },
        request_id=request_id,
    )
    
    return {
        "ok": True,
        "action_id": action_id,
        "defer_until": defer_until_iso,
        "defer_bucket": defer_bucket,
    }


@router.post("/api/queue/{action_id}/add-to-today")
async def add_to_today(
    action_id: str,
    body: AddToTodayRequest,
    request: Request,
    user_id: str = Depends(_get_user_id),
) -> Dict[str, Any]:
    """Add action item to today's schedule.
    
    Creates a ScheduleBlock stub.
    Persists and audits.
    """
    if action_id not in queue_store:
        raise HTTPException(status_code=404, detail="action_not_found")
    
    # Generate schedule block ID
    schedule_block_id = str(uuid.uuid4())
    
    # Create schedule block and add to proposed blocks store
    schedule_block = {
        "id": schedule_block_id,
        "user_id": user_id,
        "kind": body.kind,
        "tasks": body.tasks or [],
        "action_id": action_id,
        "estimated_minutes": 60,  # Default, will be estimated by LLM later
        "priority": queue_store[action_id].get("priority", "medium"),
        "estimated_start": None,  # Will be resolved by collision resolver
    }
    proposed_blocks_store.append(schedule_block)
    
    queue_store[action_id]["added_to_today"] = True
    
    request_id = getattr(request.state, "request_id", None)
    
    # Write audit log
    audit_log.write_audit(
        "add_to_today",
        {
            "action_id": action_id,
            "schedule_block_id": schedule_block_id,
            "kind": body.kind,
            "tasks": body.tasks or [],
            "user_id": user_id,
        },
        request_id=request_id,
    )
    
    return {
        "ok": True,
        "action_id": action_id,
        "schedule_block_id": schedule_block_id,
        "kind": body.kind,
    }


@router.post("/api/queue/{action_id}/reply")
async def reply_action(
    action_id: str,
    body: Dict[str, Any],
    request: Request,
    user_id: str = Depends(_get_user_id),
) -> Dict[str, Any]:
    """Reply to an action item (mock).
    
    Persists draft and audits.
    """
    if action_id not in queue_store:
        raise HTTPException(status_code=404, detail="action_not_found")
    
    draft_id = f"draft_{uuid.uuid4().hex[:8]}"
    
    request_id = getattr(request.state, "request_id", None)
    
    # Write audit log
    audit_log.write_audit(
        "reply",
        {
            "action_id": action_id,
            "draft_id": draft_id,
            "draft": body.get("draft", ""),
            "user_id": user_id,
        },
        request_id=request_id,
    )
    
    return {
        "ok": True,
        "action_id": action_id,
        "draft_id": draft_id,
    }


class AssistantSuggestRequest(BaseModel):
    message: Optional[str] = Field(None, description="User message to the assistant (deprecated, use thread_id)")
    thread_id: Optional[str] = Field(None, description="Thread ID to aggregate pending messages from")


@router.post("/api/queue/{action_id}/assistant-suggest")
async def assistant_suggest_for_action(
    action_id: str,
    body: AssistantSuggestRequest,
    request: Request,
    user_id: str = Depends(_get_user_id),
) -> Dict[str, Any]:
    """Get LLM-suggested operations for an action item.
    
    Resolves tenant_id + user_id, calls propose_ops_for_user with focus_action_id,
    executes ops based on trust_mode, and returns operations, applied, pending.
    """
    from services import llm as llm_service
    from core.services.llm_executor import execute_ops
    from presentation.api.repos import user_settings, tasks
    from presentation.api.repos.workroom import _resolve_identity
    
    # Resolve tenant_id
    tenant_id, _ = _resolve_identity(user_id)
    
    # Get trust mode from settings
    settings = user_settings.get_settings(user_id)
    trust_mode = settings.get("trust_level", "training_wheels")
    # Map legacy "standard" to "supervised"
    if trust_mode == "standard":
        trust_mode = "supervised"
    
    # Verify action exists
    try:
        action = tasks.get_action_item(user_id, action_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="action_not_found")
    
    # Get thread_id from action or request
    thread_id = body.thread_id
    if not thread_id and action.get("thread_id"):
        thread_id = action["thread_id"]
    
    # Build context for resolution (shared across pipeline)
    from core.services.llm_context_builder import build_context_for_user
    
    context = build_context_for_user(
        tenant_id=tenant_id,
        user_id=user_id,
        focus_action_id=action_id,
    )

    context_thread_id = thread_id or f"action:{action_id}"
    
    # Define a helper function to execute the operation pipeline
    async def execute_pipeline():
        # Aggregate pending user messages if thread_id provided
        input_messages = None
        if thread_id:
            # Get pending user messages since last assistant response
            pending_messages = workroom.get_pending_user_messages(thread_id, user_id)
            if pending_messages:
                input_messages = [msg.get("content", "") for msg in pending_messages]
        
        # Fallback to single message if no thread_id or no pending messages
        if not input_messages:
            if not body.message:
                raise HTTPException(status_code=400, detail="Either message or thread_id must be provided")
            input_messages = [body.message]
        
        thread_context = load_thread_context(context_thread_id)
        ui_context = UiContext(
            mode="hub",
            hub_suggested_task_id=action.get("task_id"),
        )

        latest_message = input_messages[-1] if input_messages else ""
        parsed_message = parse_message_with_tokens(latest_message)
        validation_ok: Optional[ValidationOk] = None

        if input_messages:
            llm_input_messages = list(input_messages)
            llm_input_messages[-1] = parsed_message.llm_text
        else:
            llm_input_messages = [parsed_message.llm_text]

        if parsed_message.references or parsed_message.operations:
            validation_result = validate_parsed_message(
                parsed_message,
                user_context={
                    "userId": user_id,
                    "tenantId": tenant_id,
                    "threadContext": thread_context.to_dict(),
                },
            )
            if isinstance(validation_result, ValidationOk):
                validation_ok = validation_result
                thread_context = update_thread_context_with_refs(
                    thread_context, parsed_message.references
                )
            else:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "token_validation_failed",
                        "code": getattr(validation_result, "error_code", "UNKNOWN"),
                        "details": getattr(validation_result, "details", {}),
                    },
                )

        focus_candidates = resolve_focus_candidates(thread_context, ui_context, parsed_message)
        contract_payload = build_contract_payload(
            parsed_message=parsed_message,
            thread_context=thread_context,
            ui_context=ui_context,
            focus_candidates=focus_candidates,
            validation=validation_ok,
            context=context,
        )
        
        # Propose operations with aggregated messages
        operations = llm_service.propose_ops_for_user(
            tenant_id=tenant_id,
            user_id=user_id,
            input_messages=llm_input_messages,
            focus_action_id=action_id,
            context_override=context,
            contract_payload=contract_payload,
        )

        # Convert to typed operations for executor
        from core.domain.llm_ops import validate_operation
        typed_ops = []
        for op_dict in operations:
            try:
                op = validate_operation(op_dict)
                typed_ops.append(op)
            except ValueError as e:
                logger.warning(f"Invalid operation skipped: {e}")

        # Execute with trust gating and context for resolution
        result = execute_ops(
            typed_ops,
            tenant_id=tenant_id,
            user_id=user_id,
            trust_mode=trust_mode,
            thread_id=thread_id,
            context=context,
        )
        save_thread_context(context_thread_id, thread_context)
        
        return operations, result
    
    # Execute pipeline with thread lock if thread_id is present
    if thread_id:
        # Acquire lock for this thread to prevent concurrent processing
        # Lock wraps entire pipeline: message reading, LLM calls, operation execution, and context save
        thread_lock = await _get_thread_lock(thread_id)
        async with thread_lock:
            operations, result = await execute_pipeline()
    else:
        # No thread_id, execute without lock
        operations, result = await execute_pipeline()
    
    # Refresh action item
    try:
        refreshed_action = tasks.get_action_item(user_id, action_id)
    except ValueError:
        refreshed_action = action
    
    request_id = getattr(request.state, "request_id", None)
    
    # Write audit log
    audit_log.write_audit(
        "assistant_suggest",
        {
            "action_id": action_id,
            "user_id": user_id,
            "thread_id": thread_id,
            "message_count": len(input_messages),
            "operations_count": len(operations),
            "applied_count": len(result["applied"]),
            "pending_count": len(result["pending"]),
        },
        request_id=request_id,
    )
    
    return {
        "ok": True,
        "operations": operations,
        "applied": result["applied"],
        "pending": result["pending"],
        "errors": result["errors"],
        "action": refreshed_action,
    }


class ApproveOperationRequest(BaseModel):
    operation: Dict[str, Any] = Field(..., description="Operation to approve")


@router.post("/api/queue/{action_id}/assistant-approve")
async def assistant_approve_operation(
    action_id: str,
    body: ApproveOperationRequest,
    request: Request,
    user_id: str = Depends(_get_user_id),
) -> Dict[str, Any]:
    """Approve and execute a pending operation for an action item."""
    from core.services.llm_executor import execute_single_op_approved
    from core.domain.llm_ops import validate_operation
    from presentation.api.repos.workroom import _resolve_identity
    from presentation.api.repos import tasks
    
    tenant_id, _ = _resolve_identity(user_id)
    
    # Validate operation (convert to dict if it's a Pydantic model)
    try:
        operation_dict = body.operation
        if hasattr(operation_dict, 'dict'):
            operation_dict = operation_dict.dict()
        elif hasattr(operation_dict, 'model_dump'):
            operation_dict = operation_dict.model_dump()
        op = validate_operation(operation_dict)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid operation: {e}")
    
    # Get thread_id from action
    try:
        action = tasks.get_action_item(user_id, action_id)
        thread_id = action.get("thread_id")
    except ValueError:
        thread_id = None
    
    # Build context for resolution
    from core.services.llm_context_builder import build_context_for_user
    
    context = build_context_for_user(
        tenant_id=tenant_id,
        user_id=user_id,
        focus_action_id=action_id,
    )
    
    # Execute approved operation (bypasses trust gating) with context
    result = execute_single_op_approved(
        op,
        tenant_id=tenant_id,
        user_id=user_id,
        thread_id=thread_id,
        context=context,
    )
    
    # Check for duplicate errors and return 409 with assistant-facing message
    if not result.get("ok") and result.get("assistant_message"):
        raise HTTPException(
            status_code=409,
            detail={
                "error": result.get("error"),
                "assistant_message": result.get("assistant_message"),
                "operation": body.operation,
            }
        )
    
    # Refresh action
    try:
        refreshed_action = tasks.get_action_item(user_id, action_id)
    except ValueError:
        refreshed_action = None
    
    request_id = getattr(request.state, "request_id", None)
    audit_log.write_audit(
        "assistant_approve",
        {
            "action_id": action_id,
            "operation": body.operation,
            "result": result,
        },
        request_id=request_id,
    )
    
    return {
        "ok": result.get("ok", False),
        "result": result,
        "action": refreshed_action,
    }


class EditOperationRequest(BaseModel):
    operation: Dict[str, Any] = Field(..., description="Original operation")
    edited_params: Dict[str, Any] = Field(..., description="Edited parameters")


@router.post("/api/queue/{action_id}/assistant-edit")
async def assistant_edit_operation(
    action_id: str,
    body: EditOperationRequest,
    request: Request,
    user_id: str = Depends(_get_user_id),
) -> Dict[str, Any]:
    """Edit and execute a pending operation for an action item."""
    from core.services.llm_executor import execute_single_op_approved
    from core.domain.llm_ops import validate_operation
    from presentation.api.repos.workroom import _resolve_identity
    from presentation.api.repos import tasks
    
    tenant_id, _ = _resolve_identity(user_id)
    
    # Create edited operation
    edited_op_dict = {
        "op": body.operation.get("op"),
        "params": {**body.operation.get("params", {}), **body.edited_params},
    }
    
    # Validate edited operation
    try:
        op = validate_operation(edited_op_dict)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid edited operation: {e}")
    
    # Get thread_id from action
    try:
        action = tasks.get_action_item(user_id, action_id)
        thread_id = action.get("thread_id")
    except ValueError:
        thread_id = None
    
    # Execute edited operation
    result = execute_single_op_approved(
        op,
        tenant_id=tenant_id,
        user_id=user_id,
        thread_id=thread_id,
    )
    
    # Refresh action
    try:
        refreshed_action = tasks.get_action_item(user_id, action_id)
    except ValueError:
        refreshed_action = None
    
    request_id = getattr(request.state, "request_id", None)
    audit_log.write_audit(
        "assistant_edit",
        {
            "action_id": action_id,
            "original_operation": body.operation,
            "edited_operation": edited_op_dict,
            "result": result,
        },
        request_id=request_id,
    )
    
    return {
        "ok": result.get("ok", False),
        "result": result,
        "action": refreshed_action,
    }


class DeclineOperationRequest(BaseModel):
    operation: Dict[str, Any] = Field(..., description="Operation to decline")


@router.post("/api/queue/{action_id}/assistant-decline")
async def assistant_decline_operation(
    action_id: str,
    body: DeclineOperationRequest,
    request: Request,
    user_id: str = Depends(_get_user_id),
) -> Dict[str, Any]:
    """Decline a pending operation for an action item."""
    from presentation.api.repos.workroom import _resolve_identity
    from presentation.api.repos import tasks
    
    tenant_id, _ = _resolve_identity(user_id)
    
    # Just log the decline - no execution needed
    request_id = getattr(request.state, "request_id", None)
    audit_log.write_audit(
        "assistant_decline",
        {
            "action_id": action_id,
            "operation": body.operation,
        },
        request_id=request_id,
    )
    
    # Refresh action
    try:
        refreshed_action = tasks.get_action_item(user_id, action_id)
    except ValueError:
        refreshed_action = None
    
    return {
        "ok": True,
        "action": refreshed_action,
    }


class UndoOperationRequest(BaseModel):
    operation: Dict[str, Any] = Field(..., description="Operation to undo")
    original_state: Optional[Dict[str, Any]] = Field(None, description="Original state before operation")


@router.post("/api/queue/{action_id}/assistant-undo")
async def assistant_undo_operation(
    action_id: str,
    body: UndoOperationRequest,
    request: Request,
    user_id: str = Depends(_get_user_id),
) -> Dict[str, Any]:
    """Undo a previously applied operation for an action item."""
    from core.services.llm_executor import undo_operation
    from core.domain.llm_ops import validate_operation
    from presentation.api.repos.workroom import _resolve_identity
    from presentation.api.repos import tasks
    
    tenant_id, _ = _resolve_identity(user_id)
    
    # Validate operation (convert to dict if it's a Pydantic model)
    try:
        operation_dict = body.operation
        if hasattr(operation_dict, 'dict'):
            operation_dict = operation_dict.dict()
        elif hasattr(operation_dict, 'model_dump'):
            operation_dict = operation_dict.model_dump()
        op = validate_operation(operation_dict)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid operation: {e}")
    
    # Undo operation
    result = undo_operation(
        op,
        tenant_id=tenant_id,
        user_id=user_id,
        original_state=body.original_state,
    )
    
    # Refresh action
    try:
        refreshed_action = tasks.get_action_item(user_id, action_id)
    except ValueError:
        refreshed_action = None
    
    request_id = getattr(request.state, "request_id", None)
    audit_log.write_audit(
        "assistant_undo",
        {
            "action_id": action_id,
            "operation": body.operation,
            "result": result,
        },
        request_id=request_id,
    )
    
    return {
        "ok": result.get("ok", False),
        "result": result,
        "action": refreshed_action,
    }
