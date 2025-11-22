# Hub v2 Orientation Layer

## Summary
- Introduced a single-column Hub experience with Day Overview, Priorities, My Work Snapshot, and Inbox Digest sections.
- Added hub-specific selectors for pinned tasks, grouped work states, inbox digest data, and today events, plus canonical task pin toggling.
- Extended AssistantChat with a `hub_orientation` mode that filters interactive surfaces to hub-safe kinds and tightened navigation to Workroom via focus context updates.

## Testing
- `npm test -- HubOrientation.test.tsx` *(fails: jsdom/react hook initialization error; see logs for `useMemo`/`useSyncExternalStore` null references).* 
- `npm test` *(fails for same hook initialization error across suite after adding new hub tests).* 

## Updates
- Stabilized Vitest configuration to force a single React instance and added hub surface guard helpers/tests.
- Tightened Hub CTA routing to push hub-origin focus anchors into Workroom for Today, tasks, and triage from the new panels.
- Documented the `hub_orientation` contract and added grouping/nav assertions for Priorities, My Work Snapshot, and Inbox Digest.

## Latest
- Added additional Hub guardrail tests to ensure Day Overview is the only surface-enabled section and that hub-safe surfaces are limited to one per message.
- Updated the hub orientation contract to note the single-surface limit and refreshed docs to reflect the passing hub test suite.
