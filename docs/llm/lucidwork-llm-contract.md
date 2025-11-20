# LucidWork LLM Contract (v1)

This document defines what the LLM can and cannot do inside LucidWork’s Hub and Workroom chat environments. It is the authoritative ruleset governing identity resolution, token behaviour, context use, disambiguation, and latency-aware interaction.

=====================================================================

## 1. PURPOSE

=====================================================================

LucidWork sits on top of Microsoft 365. Users interact with emails, events, tasks, and projects through conversational chat surfaces. The LLM must perform reasoning, but **must never guess which object the user means**. All actions must be deterministic, safe, and traceable.

This contract ensures:

- the LLM acts only on validated objects,
- ambiguous references are resolved safely,
- user intent is always surfaced clearly through ActionSummary,
- UX latency can be managed without compromising correctness.

=====================================================================

## 2. CORE CONCEPTS

=====================================================================

### 2.1 Structured Tokens (backend-parsed, not LLM-parsed)

These appear in user messages and are parsed by the backend:

**Reference tokens**

`[ref v:1 type:"task" id:8742 name:"Prepare Q4 Brief"]`

**Operation tokens**

`[op v:1 type:"update_status" task:8742 status:"in_progress"]`

Tokens define exact object identity. The LLM does **not** parse them; it sees placeholders.

### 2.2 ThreadContext (per chat thread)

Backend-maintained structure tracking what the user has referred to previously:

```
interface ThreadContext {
  lastTaskId?: string;
  lastProjectId?: string;
  recentTaskIds: string[];
  recentProjectIds: string[];
  pinnedTaskId?: string;
  pinnedProjectId?: string;
}
```

Updated after every message that includes tokens or validated linkages.

### 2.3 Suggested Tasks in Hub

Every Hub item (email/action item) may have a **suggested task**:

- Deterministic candidate for linkage.
- User may change it via UI.
- When no tokens are supplied, this suggested task becomes the **default candidate** for LLM operations.

### 2.4 Current Focus in Workroom

Workroom defaults when no tokens are provided:

- Task Workroom → the current task ID
- Project Workroom → the current project ID

These serve as deterministic “current focus” IDs.

### 2.5 ActionSummary UI

After the LLM proposes actions, the ActionSummary must:

- Show **exactly which task/project ID** is being acted on.
- Allow the user to **change** the linkage via UI.
- State explicitly when an assumption was made (“Applied to: Prepare Q4 Brief”).

=====================================================================

## 3. SOURCES OF TRUTH

=====================================================================

Identity (task/project/source) comes from one of:

1. Structured tokens in the current message.
2. ThreadContext (recent, last, or pinned).
3. UI context defaults:
   - Current Workroom focus,
   - Hub suggested task.

Names or meta fields are **never** used for identity.

Operations (what to do) originate from:

- Operation tokens,
- UI commands,
- LLM reasoning constrained to allowed IDs.

LLM reasoning is always advisory; backend validation decides.

=====================================================================

## 4. MESSAGE PROCESSING PIPELINE

=====================================================================

**For every incoming message:**

### Step 1 — Parse tokens

Backend parses `[ref ...]` / `[op ...]` and replaces them with placeholders in `llmText`.

### Step 2 — Update ThreadContext

For each reference token:

- Update `lastTaskId`, `lastProjectId`,
- Update recent lists.

### Step 3 — Validate if tokens present

If any tokens appear:

- Validate IDs + permissions.
- If any fail → return deterministic error, no LLM call, no writes.
- If all pass → tokens are authoritative.

### Step 4 — Determine target(s) when no tokens

Use deterministic precedence:

**Workroom:**

1. Current task/project (depending on room)
2. `pinnedTaskId` / `pinnedProjectId`
3. `lastTaskId` / `lastProjectId`

**Hub:**

1. Suggested task (primary default)
2. ThreadContext (last/recent) only if unambiguous

If exactly one candidate emerges → treat it as the default target.  
If multiple candidates → LLM must choose among them **only** if the natural language clearly indicates one; otherwise it must ask the user.

### Step 5 — LLM call

LLM receives:

- `llmText` with placeholders,
- List of candidate IDs,
- Any validated ops,
- Current context (Hub vs Workroom),
- Explicit defaults (e.g., `default_task_id:8742`).

LLM proposes operations using **only** supplied IDs.

### Step 6 — Execution

Execution layer verifies:

- No unknown IDs,
- No mismatched IDs,
- Operation types allowed.

Then writes are applied.

ActionSummary is created, showing:

- The final target ID(s),
- The inferred/suggested default if used,
- A UI affordance to change target.

=====================================================================

## 5. DISAMBIGUATION RULES

=====================================================================

### 5.1 When tokens are present

- Tokens override everything.
- LLM must honour those exact IDs.
- LLM may not reinterpret or shift to another ID.

### 5.2 When tokens are absent (Workroom)

- Use current task/project.
- If ambiguous (rare), LLM must ask the user.

### 5.3 When tokens are absent (Hub)

- Use suggested task as default.
- Always state which task was used in ActionSummary.
- Allow user to change it.

### 5.4 LLM’s allowed role in disambiguation

- LLM **may only** choose among backend-supplied ID candidates.
- LLM cannot infer new IDs, derive IDs from names, or parse tokens.

### 5.5 When ambiguity persists

- LLM must explicitly ask the user: “Which task do you mean? A or B?”

=====================================================================

## 6. LATENCY MANAGEMENT

=====================================================================

Latency mitigation must **not** compromise safety.

### 6.1 Single LLM call per user message

- Disambiguation is done inside one call by supplying candidate IDs.
- Never chain two LLM calls for a single message.

### 6.2 Staged Response Pattern

Frontend may:

- Use a **fast model** to identify “this will become a task/action”, letting us show a skeleton ActionSummary.
- Fill in the full ActionSummary when the main model returns.
- This is purely a UX improvement; backend identity rules remain unchanged.

### 6.3 Threading / replies

- Each thread maintains its own ThreadContext.
- Threading must not create hidden identity fallbacks.
- Users must always see which task/project an action targeted.

=====================================================================

## 7. INTERACTIVE SURFACES v0

=====================================================================

Interactive surfaces let the LLM return **structured UI blocks** alongside the normal chat text + operations. They are optional, versioned, and must never bypass the existing op → validation → ActionSummary pipeline.

### 7.1 Envelope & transport

Every surface is delivered inside the `surfaces` array of the LLM JSON response:

```jsonc
{
  "operations": [ … ],
  "surfaces": [
    {
      "surface_id": "whatsnext-123",
      "kind": "what_next_v1",
      "title": "What's Next",
      "payload": { …kind-specific… }
    }
  ]
}
```

- `surface_id`: stable string for dedupe/updates.
- `kind`: discriminated union (listed below).
- `title`: user-facing heading.
- `payload`: schema per kind.
- Unknown kinds or malformed payloads are ignored.

### 7.2 Shared helper types

- **SurfaceNavigateTo**:
  - `{ destination: "workroom_task", taskId }`
  - `{ destination: "hub_queue" }`
  - `{ destination: "hub", section?: "today" | "metrics" | "priority" }`
  - `{ destination: "calendar_event", eventId }`

- **SurfaceOpTrigger**: `{ label, opToken, confirm? }`
  - `opToken` is the literal `[op v:1 …]` string that already flows through validation.

Buttons/links in the UI may only call `onInvokeOp(opToken)` or `onNavigate(navigateTo)`. No other side effects are allowed.

### 7.3 v0 surface kinds

| Kind               | Purpose / payload summary |
|--------------------|---------------------------|
| `what_next_v1`     | Primary headline + optional body, target, `primaryAction`, `secondaryActions`, and secondary notes. |
| `today_schedule_v1`| List of schedule blocks (`event`/`focus`, start/end, lock flag) plus optional suggestions (`previewChange`, `acceptOp`) and controls (`suggestAlternativesOp`). |
| `priority_list_v1` | Ranked task list with label, reason, estimate, navigation target, and quick `opToken` actions. |
| `triage_table_v1`  | Inbox triage groups (summary + group-level approve/decline ops) containing queue items with item-level `approveOp` / `declineOp`, suggested task/action metadata. |

All payloads must be valid JSON objects; missing required fields cause the surface to be discarded.

### 7.4 Safety & degradation

- Surfaces **augment** the chat text; they do **not** replace operations.
- All actions still go through the op validation pipeline using `opToken`.
- Backend logs every op via ActionSummary for audit, even if the UI hides the card (e.g., triage flows).
- If the LLM cannot build a valid surface, it should omit the entry; the chat continues as before.
- Versioning allows future `*_v2` kinds without breaking old clients.

=====================================================================

## 8. HARD CONSTRAINTS (NON-NEGOTIABLE)

=====================================================================

1. **LLM must not invent IDs.**
2. **LLM must not act on any ID not provided by backend.**
3. **LLM must not reinterpret or rewrite token IDs.**
4. **LLM must not use meta fields for identity.**
5. **LLM must surface which ID it acted upon.**
6. **LLM must ask when multiple targets are plausible.**
7. **LLM may treat Workroom focus or Hub suggested task as default only when unambiguous.**
8. **If user edits linkage in UI, subsequent messages must use the updated ID.**
9. **No silent fallbacks, no hidden inference.**
10. **All writes must undergo validation before execution.**

=====================================================================

## 9. SUMMARY

=====================================================================

LucidWork’s LLM is not a guesser; it is a reasoning engine operating inside a strict safety boundary.

Object identity comes **only** from structured tokens, thread memory, and explicit UI context.

When defaults are used (Workroom focus, Hub suggested task), they must be surfaced to the user.

All ambiguity must be resolved deterministically or by asking the user.

Latency optimisations must be UX-level only and must not relax these rules.

This contract governs all LLM behaviour related to actions, reasoning, and object targeting inside LucidWork.

=== END OF CONTRACT ===
