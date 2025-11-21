from __future__ import annotations
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
import os
import json
import re
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    import openai
except ImportError:
    openai = None

if openai is not None:
    OpenAIError = getattr(openai, "OpenAIError", Exception)
else:  # pragma: no cover - fallback when OpenAI client unavailable

    class OpenAIError(Exception):
        """Fallback OpenAI error placeholder."""


RECOVERABLE_LLM_ERRORS = (
    OpenAIError,
    json.JSONDecodeError,
    OSError,
    ValueError,
    RuntimeError,
)


@dataclass
class LlmProposedContent:
    operations: List[Any]
    surfaces: List[Dict[str, Any]]


def _sanitize_surfaces(raw: Any) -> List[Dict[str, Any]]:
    """Normalize surface envelopes returned by the LLM."""
    if not isinstance(raw, list):
        return []
    surfaces: List[Dict[str, Any]] = []
    for candidate in raw:
        if not isinstance(candidate, dict):
            continue
        surface_id = candidate.get("surface_id") or candidate.get("surfaceId")
        kind = candidate.get("kind")
        title = candidate.get("title")
        payload = candidate.get("payload")
        if not all(isinstance(value, str) for value in (surface_id, kind, title)):
            logger.debug("Skipping invalid surface envelope: %s", candidate)
            continue
        if not isinstance(payload, dict):
            logger.debug("Skipping surface without payload: %s", candidate)
            continue
        surfaces.append(
            {
                "surface_id": surface_id,
                "kind": kind,
                "title": title,
                "payload": payload,
            }
        )
    return surfaces


def generate_assistant_response(
    user_message: Optional[str] = None,
    user_messages: Optional[List[str]] = None,
    thread_messages: List[Dict[str, Any]] = None,
    action_context: Dict[str, Any] = None,
) -> str:
    """Generate an assistant response for a workroom thread.

    Args:
        user_message: Single user message (deprecated, use user_messages)
        user_messages: List of user messages to respond to (preferred)
        thread_messages: Previous messages in the thread (for context)
        action_context: Optional context about the action item this thread relates to

    Returns:
        Assistant response text
    """
    # Handle backward compatibility: convert single message to list
    if user_messages is None:
        if user_message is None:
            raise ValueError("Either user_message or user_messages must be provided")
        user_messages = [user_message]

    # LLM_TESTING_MODE: return deterministic fixture response
    if os.getenv("LLM_TESTING_MODE", "false").lower() in {"1", "true", "yes", "on"}:
        fixture_path = Path("llm_testing/fixtures/llm_ops/chat_response.json")
        if fixture_path.exists():
            with open(fixture_path, "r", encoding="utf-8") as f:
                fixture = json.load(f)
                return fixture.get(
                    "response",
                    _generate_fallback_response(
                        user_messages[0] if user_messages else ""
                    ),
                )

    # Fallback to dev pattern matching if OpenAI not available
    if not openai:
        # Use first message for fallback
        return _generate_fallback_response(user_messages[0] if user_messages else "")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return _generate_fallback_response(user_messages[0] if user_messages else "")

    try:
        client = openai.OpenAI(api_key=api_key)

        # Build conversation history
        messages = []

        # System message
        system_content = (
            "You are a helpful assistant in a workroom collaboration tool. "
            "You help users manage tasks, schedule work, and handle action items. "
            "Be concise, professional, and action-oriented. "
            "If the user asks about scheduling, deferring, or managing tasks, provide helpful guidance."
        )

        if action_context:
            system_content += f"\n\nContext: This thread relates to an action item: {action_context.get('preview', '')}"

        messages.append({"role": "system", "content": system_content})

        # Add thread history (last 10 messages for context)
        if thread_messages:
            for msg in thread_messages[-10:]:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role in ["user", "assistant"]:
                    messages.append({"role": role, "content": content})

        # Add current user message(s) - aggregate if multiple
        if len(user_messages) == 1:
            messages.append({"role": "user", "content": user_messages[0]})
        else:
            # Format multiple messages as numbered list
            messages_text = "\n".join(
                [f"{i+1}. {msg}" for i, msg in enumerate(user_messages)]
            )
            messages.append(
                {"role": "user", "content": f"User messages:\n{messages_text}"}
            )

        # Generate response
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Use cheaper model for chat
            messages=messages,
            temperature=0.7,
            max_tokens=500,
            timeout=30,
        )

        return response.choices[0].message.content.strip()
    except RECOVERABLE_LLM_ERRORS:
        logger.exception("Failed to call OpenAI chat completions; falling back")
        return _generate_fallback_response(user_messages[0] if user_messages else "")


def _generate_fallback_response(user_message: str) -> str:
    """Fallback pattern-based response generator (dev mode)."""
    user_lower = user_message.lower()

    if any(word in user_lower for word in ["hello", "hi", "hey"]):
        return "Hello! How can I help you today?"
    elif any(word in user_lower for word in ["thanks", "thank", "appreciate"]):
        return "You're welcome! Is there anything else you'd like me to help with?"
    elif any(
        word in user_lower for word in ["yes", "yeah", "yep", "sure", "ok", "okay"]
    ):
        return "Great! I'll take care of that for you."
    elif any(word in user_lower for word in ["no", "nope", "nah"]):
        return "Understood. Let me know if you change your mind."
    elif any(word in user_lower for word in ["draft", "write", "create", "make"]):
        return "I've drafted that for you. Would you like to review it before sending?"
    elif any(word in user_lower for word in ["schedule", "meeting", "calendar"]):
        return "I can help you schedule that. What time works best for you?"
    elif any(word in user_lower for word in ["follow up", "follow-up"]):
        return "I'll follow up on that. Should I include any specific details?"
    elif "?" in user_message:
        return "That's a good question. Let me think about the best approach here."
    else:
        return (
            "I understand. I can help you with that. What would you like me to do next?"
        )


def summarise_and_propose(
    context: Dict[str, Any], _core_ctx: Dict[str, Any]
) -> List[Dict[str, Any]]:
    # If live inbox items are provided in context, propose actions from them
    inbox = context.get("inbox") or []
    if isinstance(inbox, list) and inbox:
        approvals: List[Dict[str, Any]] = []
        for it in inbox[:10]:
            subj = (it or {}).get("subject") or "Email"
            sender = (it or {}).get("from") or ""
            preview = (it or {}).get("preview") or ""
            link = (it or {}).get("link") or ""
            msg_id = (it or {}).get("id") or ""
            approvals.append(
                {
                    "id": (
                        f"inbox-{msg_id}"
                        if msg_id
                        else f"inbox-{abs(hash(subj+sender))}"
                    ),
                    "kind": "email",
                    "source": "inbox",
                    "title": subj or (f"Email from {sender}" if sender else "Email"),
                    "summary": preview,
                    "metadata": {"sender": sender, "message_id": msg_id, "link": link},
                    "status": "proposed",
                }
            )
        return approvals
    # Fallback POC suggestion when no inbox context available
    return [
        {
            "id": "appr-1",
            "kind": "email",
            "source": "llm",
            "title": "Follow up on top email",
            "summary": "Suggest replying to the most urgent email.",
            "payload": context,
            "risk": "low",
            "status": "proposed",
        }
    ]


def draft_email(
    intent: Dict[str, Any], tone: str | None, _core_ctx: Dict[str, Any]
) -> Dict[str, Any]:
    return {
        "id": "draft-1",
        "to": intent.get("to") or [],
        "subject": intent.get("subject") or "Quick, calm update",
        "body": f"Hey, just following up. Tone: {tone or 'calm'}",
        "tone": tone or "neutral",
        "status": "proposed",
        "risk": "low",
    }


def propose_ops_for_user(
    tenant_id: str,
    user_id: str,
    *,
    input_message: Optional[str] = None,
    input_messages: Optional[List[str]] = None,
    focus_action_id: Optional[str] = None,
    focus_task_id: Optional[str] = None,
    use_tools: bool = True,
    context_override: Optional[Dict[str, Any]] = None,
    contract_payload: Optional[Dict[str, Any]] = None,
    context_input: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """Propose LLM operations for a user based on their message(s) and context.

    Args:
        tenant_id: Tenant identifier
        user_id: User identifier
        input_message: Single user message/request (deprecated, use input_messages)
        input_messages: List of user messages to aggregate (preferred)
        focus_action_id: Optional action ID to focus on
        focus_task_id: Optional task ID to focus on
        use_tools: If True, use OpenAI function calling; else use JSON-only mode
        context_override: Precomputed context dict (skips redundant DB fetches)
        contract_payload: Structured token/context information from the caller

    Returns:
        List of operation dicts: [{"op": "...", "params": {...}}, ...]
    """
    # Handle backward compatibility: convert single message to list
    if input_messages is None:
        if input_message is None:
            raise ValueError("Either input_message or input_messages must be provided")
        input_messages = [input_message]
    from core.services.llm_context_builder import build_context_for_user
    from core.domain.llm_ops import parse_operations_response

    # Build or reuse context snapshot
    context = context_override or build_context_for_user(
        tenant_id,
        user_id,
        focus_action_id=focus_action_id,
        focus_task_id=focus_task_id,
    )

    focus_item = context.get("focus_item") if context else None
    current_project_name = None
    if focus_item and focus_item.get("type") == "task":
        focus_task_id_from_context = focus_item.get("id")
        focus_task = next(
            (
                t
                for t in context.get("tasks", [])
                if t.get("id") == focus_task_id_from_context
            ),
            None,
        )
        if focus_task:
            project_id = focus_task.get("project_id")
            project = next(
                (p for p in context.get("projects", []) if p.get("id") == project_id),
                None,
            )
            if project:
                current_project_name = project.get("name") or None

    if current_project_name:
        current_project_label = f'"{current_project_name}"'
    else:
        current_project_label = "the current project shown in the UI"

    # LLM_TESTING_MODE: return deterministic fixture operations
    if os.getenv("LLM_TESTING_MODE", "false").lower() in {"1", "true", "yes", "on"}:
        # Check user message for delete operations FIRST (before checking focus_task_id)
        user_msg = (
            input_messages[0] if input_messages else input_message or ""
        ).lower()
        is_delete_request = "delete" in user_msg

        # Determine fixture based on focus and context
        if is_delete_request:
            # Check for error handling scenario (non-existent item)
            if (
                "non-existent" in user_msg
                or "doesn't exist" in user_msg
                or "not found" in user_msg
            ):
                fixture_path = Path(
                    "llm_testing/fixtures/llm_ops/delete_error_handling.json"
                )
            # Check for task deletion FIRST (before project, since messages may mention both)
            elif "task" in user_msg or "tasks" in user_msg:
                # Check for multiple deletions
                if (
                    "all" in user_msg
                    or "both" in user_msg
                    or ("and" in user_msg)
                    or ("tasks" in user_msg)
                ):
                    fixture_path = Path(
                        "llm_testing/fixtures/llm_ops/delete_task_multiple.json"
                    )
                else:
                    fixture_path = Path("llm_testing/fixtures/llm_ops/delete_task.json")
            # Check for project deletion
            elif "project" in user_msg or "projects" in user_msg:
                # Check for multiple deletions
                if (
                    "all" in user_msg
                    or "both" in user_msg
                    or ("and" in user_msg and "project" in user_msg)
                ):
                    fixture_path = Path(
                        "llm_testing/fixtures/llm_ops/delete_project_multiple.json"
                    )
                else:
                    fixture_path = Path(
                        "llm_testing/fixtures/llm_ops/delete_project.json"
                    )
            else:
                # Default to project deletion if unclear
                fixture_path = Path("llm_testing/fixtures/llm_ops/delete_project.json")
        elif "create task" in user_msg or "new task" in user_msg:
            fixture_path = Path(
                "llm_testing/fixtures/llm_ops/task_suggest_autonomous.json"
            )
        elif focus_task_id:
            # Try training_wheels fixture first, fallback to autonomous
            fixture_name = "task_suggest_training_wheels.json"
            fixture_path = Path(f"llm_testing/fixtures/llm_ops/{fixture_name}")
            if not fixture_path.exists():
                fixture_path = Path(
                    "llm_testing/fixtures/llm_ops/task_suggest_autonomous.json"
                )
        elif focus_action_id:
            fixture_path = Path("llm_testing/fixtures/llm_ops/queue_suggest.json")
        else:
            fixture_path = None

        if fixture_path and fixture_path.exists():
            with open(fixture_path, "r", encoding="utf-8") as f:
                fixture = json.load(f)
                ops = fixture.get("operations", [])
                # Replace placeholders with actual IDs from context
                projects = context.get("projects", [])
                tasks = context.get("tasks", [])

                for op in ops:
                    params = op.get("params", {})
                    params_str = json.dumps(params)

                    # Replace task_id placeholders
                    # For multiple deletions, prioritize context tasks over focus_task_id
                    if tasks and "<task_id_1>" in params_str:
                        params_str = params_str.replace(
                            "<task_id_1>", tasks[0].get("id", "")
                        )
                    elif focus_task_id and "<task_id_1>" in params_str:
                        params_str = params_str.replace("<task_id_1>", focus_task_id)

                    if tasks and len(tasks) > 1 and "<task_id_2>" in params_str:
                        params_str = params_str.replace(
                            "<task_id_2>", tasks[1].get("id", "")
                        )

                    # Single task_id placeholder (not numbered)
                    if focus_task_id and "<task_id>" in params_str:
                        params_str = params_str.replace("<task_id>", focus_task_id)

                    # Replace project_id placeholders (backward compatibility - old fixtures)
                    if projects and "<project_id_1>" in params_str:
                        params_str = params_str.replace(
                            "<project_id_1>", projects[0].get("id", "")
                        )
                    if projects and "<project_id_2>" in params_str:
                        params_str = params_str.replace(
                            "<project_id_2>",
                            projects[1].get("id", "") if len(projects) > 1 else "",
                        )
                    if projects and "<project_id>" in params_str:
                        params_str = params_str.replace(
                            "<project_id>", projects[0].get("id", "")
                        )

                    # Replace project_name placeholders (semantic references)
                    if projects and "<project_name_1>" in params_str:
                        params_str = params_str.replace(
                            "<project_name_1>", projects[0].get("name", "")
                        )
                    if projects and "<project_name_2>" in params_str:
                        params_str = params_str.replace(
                            "<project_name_2>",
                            projects[1].get("name", "") if len(projects) > 1 else "",
                        )
                    if projects and "<project_name>" in params_str:
                        params_str = params_str.replace(
                            "<project_name>", projects[0].get("name", "")
                        )

                    # Replace task_title placeholders (semantic references)
                    if tasks and "<task_title_1>" in params_str:
                        params_str = params_str.replace(
                            "<task_title_1>", tasks[0].get("title", "")
                        )
                    elif focus_task_id and "<task_title_1>" in params_str:
                        # Try to get task title from focus task
                        try:
                            from presentation.api.repos import workroom

                            focus_task = workroom.get_task(user_id, focus_task_id)
                            params_str = params_str.replace(
                                "<task_title_1>", focus_task.get("title", "")
                            )
                        except ValueError:
                            params_str = params_str.replace(
                                "<task_title_1>", "this task"
                            )

                    if tasks and len(tasks) > 1 and "<task_title_2>" in params_str:
                        params_str = params_str.replace(
                            "<task_title_2>", tasks[1].get("title", "")
                        )

                    if focus_action_id and "<action_id>" in params_str:
                        params_str = params_str.replace("<action_id>", focus_action_id)

                    op["params"] = json.loads(params_str)
                surfaces = _sanitize_surfaces(fixture.get("surfaces"))
                return LlmProposedContent(operations=ops, surfaces=surfaces)

    # If OpenAI not available, return empty operations
    if not openai:
        logger.warning("OpenAI not available, returning empty operations")
        return LlmProposedContent(operations=[], surfaces=[])

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning("OPENAI_API_KEY not set, returning empty operations")
        return LlmProposedContent(operations=[], surfaces=[])

    try:
        client = openai.OpenAI(api_key=api_key)

        # Build system prompt
        system_prompt = f"""You are a helpful assistant that helps users manage their work.
You can propose operations to create tasks, update task status, link actions to tasks, update action states, and delete projects or tasks.
Always respond with a JSON object containing an "operations" array.
Each operation must have an "op" field and a "params" field.

CRITICAL: Use semantic references (names, titles, "current project", "this task") instead of UUIDs or IDs.
NEVER output UUIDs, IDs, or placeholders like "current_project_id". Use human-readable identifiers.

Workroom context_input rules:
- Use ONLY the projects, tasks, and actions listed in the provided context_input JSON. If the requested item is missing, ask the user to surface it instead of inventing a name.
- The anchor task/project reflects the current Workroom focus. Prefer these anchors when the user says "this task" or "current project".
- If any list is truncated (see the "truncated" counts), ask the user to pick from the visible items before proposing operations that rely on the omitted ones.

PROJECT CONTEXT RULES:
- The current project is {current_project_label}. Assume any task-related request refers to this project unless the user explicitly names a different one.
- When the user confirms a task belongs to {current_project_label}, proceed with the requested operation.
- If the user explicitly asks to work in another project (e.g., "Create a task in Project ABC"), respond with a chat operation such as: "I can only act on tasks within {current_project_label}. To work with Project ABC, please navigate to a chat within that project." Do NOT emit create_task, update_task_status, delete_task, or link_action_to_task operations for the other project.
- When creating tasks, ALWAYS use "project": "current project" in the params—never insert the other project's name.

Allowed enum values (adhere exactly):
- priority: low | medium | high | urgent
- task status: backlog | ready | doing | blocked | done | todo
- action state: queued | deferred | completed | dismissed | converted_to_task
If the user requests something outside these lists, ask for a valid option or choose the closest allowed value and mention the adjustment.

Available operations:
- chat: {{"op": "chat", "params": {{"message": "..."}}}}
- create_task: {{"op": "create_task", "params": {{"title": "...", "project": "'current project'", "description": "...", "priority": "low|medium|high|urgent", "from_action": "action preview"}}}}
- update_task_status: {{"op": "update_task_status", "params": {{"task": "task title or 'this task'", "status": "backlog|ready|doing|blocked|done|todo"}}}}
- link_action_to_task: {{"op": "link_action_to_task", "params": {{"action": "action preview", "task": "task title"}}}}
- update_action_state: {{"op": "update_action_state", "params": {{"action": "action preview", "state": "queued|deferred|completed|dismissed|converted_to_task", "defer_until": "...", "added_to_today": true/false}}}}
- delete_project: {{"op": "delete_project", "params": {{"projects": ["project name 1", "project name 2", ...]}}}}
- delete_task: {{"op": "delete_task", "params": {{"tasks": ["task title 1", "task title 2", ...]}}}}

Semantic reference rules:
- For projects: Use the project name (e.g., "Launch Readiness") or "current project" if referring to the focus task's project
- For tasks: Use the task title (e.g., "Finalize onboarding flow") or "this task" if referring to the focus task
- For actions: Use the action preview/subject from the context
- If context shows duplicate names, ask the user to clarify before proposing operations (e.g., "There are two tasks named 'Review Q4 metrics' - which one?")

Important notes:
- When deleting multiple items, use a single operation with a list of names (e.g., {{"op": "delete_project", "params": {{"projects": ["Project A", "Project B"]}}}})
- Deleting a project will also delete all tasks in that project (cascade deletion)
- Deletion is soft delete (items are archived, not permanently removed)
- Check the provided context for available projects, tasks, and actions before proposing operations

Respond ONLY with JSON matching this schema:
{{
  "operations": [
    {{"op": "...", "params": {{...}}}},
    ...
  ]
}}
"""

        # Build user message with context - aggregate multiple messages if provided
        if len(input_messages) == 1:
            user_content = f"""User message: {input_messages[0]}"""
        else:
            # Format multiple messages as numbered list
            messages_text = "\n".join(
                [f"{i+1}. {msg}" for i, msg in enumerate(input_messages)]
            )
            user_content = f"""User messages:
{messages_text}"""

        if contract_payload:
            metadata = contract_payload.get("candidate_metadata", {})
            tasks_meta = metadata.get("tasks", {})
            projects_meta = metadata.get("projects", {})
            actions_meta = metadata.get("actions", {})
            structured_lines: List[str] = []

            for ref in contract_payload.get("resolved_references", []):
                display_name = (
                    ref.get("meta", {}).get("name")
                    or ref.get("record", {}).get("title")
                    or ref.get("record", {}).get("name")
                    or ref.get("record", {}).get("preview")
                    or ref.get("id")
                )
                structured_lines.append(
                    f"- {ref.get('placeholder')}: {ref.get('type')} → {display_name} ({ref.get('id')})"
                )

            focus_candidates = contract_payload.get("focus_candidates", {})
            if focus_candidates:
                default_task_id = focus_candidates.get("default_task_id")
                if default_task_id:
                    structured_lines.append(
                        f"- Default task target: {tasks_meta.get(default_task_id, default_task_id)} ({default_task_id})"
                    )
                default_project_id = focus_candidates.get("default_project_id")
                if default_project_id:
                    structured_lines.append(
                        f"- Default project target: {projects_meta.get(default_project_id, default_project_id)} ({default_project_id})"
                    )
                candidate_tasks = focus_candidates.get("candidate_task_ids") or []
                if candidate_tasks:
                    task_names = [
                        tasks_meta.get(t_id, t_id) for t_id in candidate_tasks[:3]
                    ]
                    structured_lines.append(
                        "- Candidate tasks: " + ", ".join(task_names)
                    )
                candidate_projects = focus_candidates.get("candidate_project_ids") or []
                if candidate_projects:
                    project_names = [
                        projects_meta.get(p_id, p_id) for p_id in candidate_projects[:3]
                    ]
                    structured_lines.append(
                        "- Candidate projects: " + ", ".join(project_names)
                    )

            if structured_lines:
                user_content += "\n\nStructured identity hints:\n" + "\n".join(
                    structured_lines
                )

        if context_input:
            user_content += "\n\ncontext_input (WorkroomContextSpace):\n"
            user_content += json.dumps(context_input, ensure_ascii=False, indent=2)

        user_content += f"""

Context:
- Projects: {len(context.get('projects', []))} projects available
- Tasks: {len(context.get('tasks', []))} tasks available
- Actions: {len(context.get('actions', []))} action items in queue
"""
        if focus_item:
            user_content += f"\nFocus item: {focus_item.get('type')} {focus_item.get('id')} - {focus_item.get('title') or focus_item.get('preview', '')}"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]

        if use_tools:
            # Try function calling first
            try:
                tools = [
                    {
                        "type": "function",
                        "function": {
                            "name": "propose_operations",
                            "description": "Propose operations to help the user",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "operations": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "op": {
                                                    "type": "string",
                                                    "enum": [
                                                        "chat",
                                                        "create_task",
                                                        "update_task_status",
                                                        "link_action_to_task",
                                                        "update_action_state",
                                                    ],
                                                },
                                                "params": {
                                                    "type": "object",
                                                    "additionalProperties": True,
                                                    "properties": {
                                                        "priority": {
                                                            "type": "string",
                                                            "enum": [
                                                                "low",
                                                                "medium",
                                                                "high",
                                                                "urgent",
                                                            ],
                                                        },
                                                        "status": {
                                                            "type": "string",
                                                            "enum": [
                                                                "backlog",
                                                                "ready",
                                                                "doing",
                                                                "blocked",
                                                                "done",
                                                                "todo",
                                                            ],
                                                        },
                                                        "state": {
                                                            "type": "string",
                                                            "enum": [
                                                                "queued",
                                                                "deferred",
                                                                "completed",
                                                                "dismissed",
                                                                "converted_to_task",
                                                            ],
                                                        },
                                                    },
                                                },
                                            },
                                            "required": ["op", "params"],
                                        },
                                    },
                                },
                                "required": ["operations"],
                            },
                        },
                    }
                ]

                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    tools=tools,
                    tool_choice={
                        "type": "function",
                        "function": {"name": "propose_operations"},
                    },
                    temperature=0.7,
                    timeout=30,
                )

                tool_calls = response.choices[0].message.tool_calls
                if tool_calls:
                    function_args = json.loads(tool_calls[0].function.arguments)
                    return LlmProposedContent(
                        operations=parse_operations_response(function_args),
                        surfaces=_sanitize_surfaces(function_args.get("surfaces")),
                    )
            except RECOVERABLE_LLM_ERRORS:
                logger.warning(
                    "Function calling failed, falling back to JSON mode",
                    exc_info=True,
                )
                use_tools = False

        if not use_tools:
            # JSON-only fallback
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.7,
                max_tokens=1000,
                timeout=30,
            )

            content = response.choices[0].message.content.strip()

            # Parse JSON from response (may be wrapped in code fences or have stray text)
            json_data = _extract_json_from_text(content)
            if json_data:
                return LlmProposedContent(
                    operations=parse_operations_response(json_data),
                    surfaces=_sanitize_surfaces(json_data.get("surfaces")),
                )

            # If parsing failed, return empty
            logger.warning(
                "Failed to parse JSON from LLM response: %.200s", content or ""
            )
            return LlmProposedContent(operations=[], surfaces=[])

    except RECOVERABLE_LLM_ERRORS:
        logger.exception("Error proposing operations")
        return LlmProposedContent(operations=[], surfaces=[])


def _extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    """Extract JSON object from text that may contain code fences or stray prose.

    Handles:
    - Clean JSON: {"operations": [...]}
    - JSON in code fences: ```json\n{"operations": [...]}\n```
    - JSON with stray text: Some text {"operations": [...]} more text
    """
    if not text:
        return None

    # Try to find JSON object
    # First, try to strip code fences
    text = text.strip()
    if text.startswith("```"):
        # Remove opening fence
        lines = text.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        # Remove closing fence if present
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines)

    # Try to find JSON object boundaries
    # Look for { ... } pattern
    brace_start = text.find("{")
    if brace_start == -1:
        return None

    # Find matching closing brace
    brace_count = 0
    brace_end = -1
    for i in range(brace_start, len(text)):
        if text[i] == "{":
            brace_count += 1
        elif text[i] == "}":
            brace_count -= 1
            if brace_count == 0:
                brace_end = i + 1
                break

    if brace_end == -1:
        return None

    json_str = text[brace_start:brace_end]

    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        # Try one more time with cleaned string
        json_str = re.sub(
            r"[^\x20-\x7E\n\r\t]", "", json_str
        )  # Remove non-printable chars
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            return None
