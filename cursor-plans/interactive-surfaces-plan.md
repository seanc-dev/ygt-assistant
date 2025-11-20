# Interactive Surfaces – Test Plan

## 1. Type Contract Parsing
### 1.1 Envelope validation
- Ensures each surface includes `surface_id`, `kind`, `title`, payload.
- Unknown `kind` values are dropped without affecting rest of response.
### 1.2 Payload schemas
- Validate required fields per surface kind (what_next, today_schedule, priority_list, triage_table).
- Reject malformed payloads while continuing message flow.
### 1.3 Navigate + op trigger helpers
- Confirm `SurfaceNavigateTo` objects normalize destinations.
- Confirm `SurfaceOpTrigger` carries literal op tokens and optional confirm flag.

## 2. LLM Response Integration
### 2.1 Backend parsing
- LLM pipeline attaches `surfaces` array to structured response.
- Invalid surfaces logged and ignored.
### 2.2 Thread serialization
- `/api/workroom/thread` includes `surfaces` on assistant messages.
- Absence of surfaces falls back to legacy behavior.

## 3. AssistantChat Rendering
### 3.1 Message model
- Assistant messages store `surfaces` and memoize them in `MessageView`.
### 3.2 AssistantSurfacesRenderer
- Switch statement renders correct surface component per `kind`.
- Invalid surface kinds skipped without breaking UI.
### 3.3 Action dispatch
- `onInvokeOp` emits op token only, feeding existing op pipeline.
- `onNavigate` routes to Hub/Workroom destinations and is no-op when handler missing.
### 3.4 Ordering + layout
- Surfaces render below assistant bubble and above ActionSummary.
- Multiple surfaces show stacked with consistent spacing.

## 4. Surface Components
### 4.1 WhatNextSurface
- Renders title, primary headline/body, optional notes, actions dispatch.
### 4.2 TodayScheduleSurface
- Lists schedule blocks with locked state indicators.
- Suggestions show accept buttons (op dispatch) and “Suggest 3 alternatives” control.
### 4.3 PriorityListSurface
- Ordered list with rank, label, reason, quick actions.
- Items trigger navigation handler when provided.
### 4.4 TriageTableSurface
- Groups with headers, summary, grouped actions.
- Item-level approve/decline buttons emit op tokens.

## 5. Hub 2.0 Integration
### 5.1 What’s Next block
- Hub top section consumes `what_next_v1` surface when available.
- Falls back to existing UI when no surfaces or invalid payload.

## 6. Safety & Degradation
### 6.1 Logging
- Invalid surfaces warned once per message; chat text still displays.
### 6.2 ActionSummary coexistence
- ActionSummary UI hides only when triage surface present; backend logging unaffected.
### 6.3 Loading states
- Renderer tolerates async arrival of surfaces (undefined → data).

