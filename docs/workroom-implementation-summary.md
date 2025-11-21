# Workroom UX Implementation Summary

This document walks through the specification line-by-line and explains how each part was implemented in the current codebase. It is updated after each Workroom UX iteration; the most recent pass (enhanced mode semantics, neighborhood rail navigation, and canonical task status handling) is reflected below so reviewers can see where the latest changes live.

## Latest iteration highlights
- **Mode semantics & task headers**: See the WorkCanvas section for how Planning/Execution/Review surfaces render differently for task/event anchors and how headers expose status/time context.
- **Neighborhood navigation**: The Rails section notes how `NeighborhoodRail` consumes focus neighborhoods (with mock fallback) and pushes new FocusContexts in-place.
- **Canonical task status**: The WorkBoard section explains the `TaskStatus` binding and persistence via `workroomApi.updateTaskStatus` after drag-and-drop.

## FocusContext types and store
- **Type definitions**: `web/src/lib/focusContext.ts` declares `FocusAnchorType`, `FocusAnchor`, `FocusMode`, `FocusOriginSource`, `FocusOrigin`, `FocusNeighborhood`, and `FocusContext`, matching the requested shapes.
- **Zustand store**: `web/src/state/focusContextStore.ts` maintains `current` and `stack`, and exposes `setFocusContext`, `updateFocusMode`, `pushFocus`, and `popFocus`. `pushFocus` assigns default modes (`plan` for portfolio/project, `execute` for task/event) and pushes the previous context on the stack when moving forward. `setFocusContext` can skip stacking for initial load, and `popFocus` restores the previous context.

## Workroom shell layout
- **Page composition**: `web/src/pages/workroom/index.tsx` renders the `WorkroomAnchorBar`, `FocusStackRail`, central `WorkCanvas`, and a placeholder `NeighborhoodRail` inside the shared `Layout`.
- **Default focus**: On first load, the page initializes the focus to the My Work portfolio (`{type:"portfolio", id:"my_work"}`) in `plan` mode with origin `direct`.

## WorkroomAnchorBar
- **Context display**: `web/src/components/workroom/WorkroomAnchorBar.tsx` reads focus state to show origin, anchor label, clock, and mode toggles.
- **Back navigation**: When the stack has entries, a Back button calls `popFocus()`.
- **Dynamic origin labeling**: Origins from Hub, boards (including My Work), or direct entry render specific labels; board-derived contexts show “From: My work board” when applicable.

## WorkCanvas
- **Context-driven rendering**: `web/src/components/workroom/WorkCanvas.tsx` routes portfolio/project anchors to the aggregate `WorkBoard` while showing per-mode emphasis text, and task/event anchors to AssistantChat surfaces keyed by `chatContextId` derived from the anchor type and id.
- **Mode semantics**: Task/event views now render mode-specific sections for Planning, Execution, and Review with dedicated placeholders for future surfaces, while boards keep visible and swap emphasis copy based on the current mode.
- **Task/event header**: Task and event views present enriched header chips with title, status, priority (when available), and time/linking context derived from the focused anchor.

## WorkBoard
- **Aggregate board**: `web/src/components/workroom/WorkBoard.tsx` implements a Kanban with Backlog/Ready/Doing/Blocked/Done columns bound to the canonical `TaskStatus` shape.
- **Interaction**: Drag-and-drop updates task status optimistically and calls `workroomApi.updateTaskStatus` to persist the canonical `status`; clicking a card pushes a new task focus (`origin.source: "board"`, including surfaceKind for My Work vs project boards).
- **Filtering**: Project boards filter tasks by `projectId`; the My Work portfolio board shows all tasks.

## Rails
- **FocusStackRail**: `web/src/components/workroom/FocusStackRail.tsx` shows stack size and a button to return to the previous focus when available.
- **NeighborhoodRail**: `web/src/components/workroom/NeighborhoodRail.tsx` reads real/neighborhood data (with mock fallback) to render related tasks/events/docs/queue items; clicking an item pushes a new focus without leaving the Workroom.

## Hub → Workroom navigation
- **Action cards**: `web/src/components/hub/ActionCard.tsx` uses `pushFocus` with origin `hub_surface` and navigates to `/workroom` to open the selected task.
- **Quick review**: `web/src/components/hub/QuickReview.tsx` opens individual tasks in Workroom or the My Work board with appropriate focus origins.
- **Workload panel**: `web/src/components/hub/WorkloadPanel.tsx` provides a shortcut to open the My Work board via the unified focus flow.

## AssistantChat scoping
- **Stable context ids**: In `WorkCanvas`, the AssistantChat `actionId` combines anchor type and id (`"task:task-1"`, etc.), keeping chat history scoped per task/event focus.

## Default experiences
- **Direct entry**: Visiting `/workroom` without prior context loads the My Work board automatically.
- **Board-to-task flow**: Clicking a card on the board opens the task view with board origin and supports returning via the stack rail/back button.
- **Hub-to-task flow**: Hub surfaces set the focus with origin `hub_surface` before navigating to Workroom, preserving context for the anchor bar.
