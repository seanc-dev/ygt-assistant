# Workroom context integration (navigation + mode protections)

This iteration replaces ad-hoc mock neighborhood data with a typed Workroom Context API, wires the Workroom shell to consume it, and extends tests to guard the FocusContext-driven UX.

## Key additions
- **Types**: `src/lib/workroomContext.ts` defines `WorkroomContext`, anchor variants, and neighborhoods for forward compatibility with future surfaces.
- **Mock-backed API**: `src/pages/api/workroom/context.ts` returns a `WorkroomContext` for any Focus anchor using the shared mock data in `src/data/mockWorkroomData.ts`.
- **Hook**: `src/hooks/useWorkroomContext.ts` watches the FocusContext anchor, fetches the context (with abort safety), and provides loading/error/fallback states.

## Workroom consumption
- **WorkCanvas** now pulls anchor/title/status/priority/time from `useWorkroomContext()`, surfaces loading/error notes, and continues to render mode-specific sections and AssistantChat scoping.
- **NeighborhoodRail** renders related items from the fetched neighborhood, with loading/error fallbacks and push-to-focus navigation for related tasks/events.

## Data shaping
- `src/data/mockWorkroomData.ts` centralizes mock tasks/events/projects, canonical status labels, time formatting, and a `buildWorkroomContext` helper used by the API and tests.

## Tests updated
- **WorkCanvas** tests mock `useWorkroomContext` to assert loading/error/header rendering atop existing mode semantics.
- **NeighborhoodRail** tests cover loading, empty, and clickable related tasks via the hook-driven neighborhood.

Run `npm run test` (or the vitest command in CI) to execute the suite.
