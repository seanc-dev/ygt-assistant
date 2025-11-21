# Workroom interactive surfaces integration (iteration)

This update wires the existing interactive surfaces pipeline into the Workroom task/event experience while keeping the FocusContext navigation guarantees intact.

## Key changes
- **AssistantChat surface controls** now accept `surfaceRenderAllowed` to gate rendering without losing cached surfaces, plus an optional `onSurfaceNavigateOverride` so Workroom can drive navigation through `pushFocus`.
- **WorkCanvas** computes whether surfaces should render (task/event anchors in Execute mode) and forwards a navigation override that translates surface intents into FocusContext pushes for tasks and calendar events.
- **Tests** cover Workroom mode gating, surface navigation hooks into FocusContext, surface rendering suppression, op-token invocation through the existing pipeline, and isolation of surfaces per chat context.

## Usage notes
- Surfaces remain scoped by `chatContextId` (`${anchor.type}:${anchor.id}`) and stay in memory when switching modes; they render only in Execute mode for task/event anchors.
- Surface navigation in Workroom never changes the route; it pushes a new FocusContext with `origin.source = "direct"`.
- Surface op tokens continue to flow through the existing assistant operation pipeline (task-focused endpoints when in Workroom mode).

## Test commands
Run the targeted suites for Workroom and FocusContext protections:

```
CI=1 node node_modules/vitest/vitest.mjs run src/state/__tests__/focusContextStore.test.ts src/components/workroom/__tests__/WorkCanvas.test.tsx src/components/workroom/__tests__/NavigationRails.test.tsx src/components/workroom/__tests__/NeighborhoodRail.test.tsx src/components/workroom/__tests__/WorkBoard.test.tsx src/components/workroom/__tests__/WorkroomAssistantSurfaces.test.tsx --reporter=basic
```
