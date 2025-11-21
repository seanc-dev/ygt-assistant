# Workroom focus navigation tests

This document records the invariants covered by the new unit tests that protect the FocusContext navigation model, mode semantics, and neighborhood/board behaviors.

## Coverage highlights

- **FocusContext store** (`src/state/focusContextStore.ts`)
  - Starts empty and defaults mode based on anchor type.
  - `pushFocus` stacks the previous context and applies default modes (`plan` for portfolio/project; `execute` for task/event).
  - `setFocusContext` honors `pushToStack` to control stacking semantics.
  - `popFocus` safely restores prior focus or no-ops when the stack is empty.

- **WorkCanvas mode semantics** (`src/components/workroom/WorkCanvas.tsx`)
  - Task/event views always render chat plus a single active mode section (Planning, Execution, or Review) per `FocusMode`.
  - Portfolio/project anchors keep the board visible in all modes while swapping emphasis text for plan/execute/review states.

- **Navigation rails** (`src/components/workroom/WorkroomAnchorBar.tsx`, `src/components/workroom/FocusStackRail.tsx`)
  - Back controls appear only when the focus stack has entries and correctly trigger `popFocus` to restore prior context.
  - Origin labeling aligns with source metadata: Hub surfaces, boards, or direct entry.

- **Neighborhood rail** (`src/components/workroom/NeighborhoodRail.tsx`)
  - Shows a friendly empty state when no related items exist.
  - Related items push a new FocusContext in-place without routing away from the Workroom.

- **WorkBoard status updates** (`src/components/workroom/WorkBoard.tsx`)
  - Dragging a task between columns updates its canonical `status` and calls `workroomApi.updateTaskStatus` to persist the change.
  - The board reflects the updated column membership immediately, preserving the canonical workflow states.

## How to run the suite

From `web/` run:

```bash
npm run test
```

Vitest executes the component and store tests with jsdom + React Testing Library so the Workroom navigation model stays guarded.
