# Hub Orientation Contract

The `hub_orientation` AssistantChat mode is reserved for the Hub entry experience and is intentionally limited:

- **Surface gating**: only `what_next_v1` and `priority_list_v1` surfaces may render. Hub defaults to hiding surfaces unless a Hub section explicitly enables them (e.g., Day Overview).
- **Surface limits**: Hub renders at most one interactive surface per assistant message, and only inside Day Overview.
- **Workroom navigation**: all Hub actions must route through FocusContext with an origin of `{ source: "hub" }` and then push the user to `/workroom`. Supported anchors are `task`, `event`, `today`, `triage`, and `project`.
- **Orientation only**: Hub surfaces and controls are read-only orientation; no Kanban, drag-and-drop, or Context Space affordances are available.
