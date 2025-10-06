from typing import Dict, Any, List
import re
import yaml
import os
from pydantic import BaseModel, Field


class EmailEnvelope(BaseModel):
    """Minimal email envelope for rules-first triage."""

    message_id: str
    sender: str
    subject: str = ""
    body_text: str = ""
    received_at: str = ""


class ProposedAction(BaseModel):
    """A proposed action resulting from rules-first triage."""

    type: str  # create_task | label_email | create_event | propose_event_change | upsert_contact
    payload: Dict[str, Any] = Field(default_factory=dict)
    requires_confirmation: bool = True
    confidence: float = 0.8


class TriageResult(BaseModel):
    """Result of triage including actions and applied rules."""

    actions: List[ProposedAction] = Field(default_factory=list)
    rules_applied: List[str] = Field(default_factory=list)


def _match_rule(env: EmailEnvelope, rule: Dict[str, Any]) -> bool:
    m = rule.get("match", {})

    def _contains_any(text: str, needles: List[str]) -> bool:
        t = text.lower()
        return any(n.lower() in t for n in needles)

    if "from" in m:
        patterns: List[str] = m["from"]
        ok = any(re.fullmatch(p.replace("*", "[^@]*"), env.sender) for p in patterns)
        if not ok:
            return False
    if "subject_has" in m and not _contains_any(env.subject, m["subject_has"]):
        return False
    if "body_has" in m and not _contains_any(env.body_text, m["body_has"]):
        return False
    return True


def load_rules(path: str = "config/rules.yaml") -> Dict[str, Any]:
    """Load rules YAML or fall back to sample."""

    if not os.path.exists(path):
        path = "config/rules.sample.yaml"
    with open(path, "r") as f:
        return yaml.safe_load(f) or {}


def triage_email(
    envelope: EmailEnvelope,
    rules_path: str = "config/rules.yaml",
    enable_fallback: bool = True,
    cfg: dict | None = None,
) -> TriageResult:
    """Apply rules-first triage to an email envelope and return proposed actions.

    When no rules match and enable_fallback is True, emit a low-confidence create_task action.
    """

    cfg = cfg or load_rules(rules_path)
    res = TriageResult()
    for rule in cfg.get("email_triage") or []:
        if _match_rule(envelope, rule):
            res.rules_applied.append(rule.get("action", ""))
            act = ProposedAction(
                type=rule["action"],
                payload=rule.get("fields", {}),
                requires_confirmation=True,
                confidence=0.9,
            )
            # Carry source
            act.payload.setdefault("source_ids", {})[
                "email_message_id"
            ] = envelope.message_id
            res.actions.append(act)
    if not res.actions and enable_fallback:
        title = (envelope.subject or "Follow up").strip()
        if len(title) > 80:
            title = title[:77] + "..."
        payload = {
            "title": f"Follow up: {title}",
            "source_ids": {"email_message_id": envelope.message_id},
        }
        res.actions.append(
            ProposedAction(
                type="create_task",
                payload=payload,
                requires_confirmation=True,
                confidence=0.6,
            )
        )
        res.rules_applied.append("fallback_create_task")
    return res
