export type FocusAnchorType =
  | "task"
  | "event"
  | "project"
  | "portfolio"
  | "today"
  | "triage";

export type FocusAnchor = {
  type: FocusAnchorType;
  id?: string;
};

export type FocusMode = "plan" | "execute" | "review";

export type FocusOriginSource = "hub_surface" | "board" | "direct" | "hub";

export type FocusOrigin = {
  source: FocusOriginSource;
  surfaceKind?: string;
  surfaceId?: string;
};

export type FocusNeighborhood = {
  tasks?: Array<{ id: string; title: string }>;
  events?: Array<{ id: string; title: string }>;
  docs?: Array<{ id: string; title: string }>;
  queueItems?: Array<{ id: string; title: string }>;
};

export type FocusContext = {
  anchor: FocusAnchor;
  mode: FocusMode;
  origin?: FocusOrigin;
  neighborhood?: FocusNeighborhood;
};
