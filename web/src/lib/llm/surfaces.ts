export type SurfaceKind =
  | "what_next_v1"
  | "today_schedule_v1"
  | "priority_list_v1"
  | "triage_table_v1"
  | "context_add_v1";

export type SurfaceNavigateTo =
  | { destination: "workroom_task"; taskId: string }
  | { destination: "hub_queue" }
  | { destination: "hub"; section?: "today" | "metrics" | "priority" }
  | { destination: "calendar_event"; eventId: string };

export type SurfaceOpTrigger = {
  label: string;
  opToken: string;
  confirm?: boolean;
};

export type SurfaceAction =
  | SurfaceOpTrigger
  | {
      label: string;
      navigateTo: SurfaceNavigateTo;
    };

export type SurfaceNote = {
  icon?: string;
  text: string;
};

export type WhatNextPrimary = {
  headline: string;
  body?: string;
  target?: SurfaceNavigateTo;
  primaryAction?: SurfaceAction;
  secondaryActions?: SurfaceAction[];
};

export type WhatNextPayload = {
  primary: WhatNextPrimary;
  secondaryNotes?: SurfaceNote[];
};

export type ScheduleBlock = {
  blockId: string;
  type: "event" | "focus";
  eventId?: string;
  taskId?: string;
  label: string;
  start: string;
  end: string;
  isLocked: boolean;
};

export type ScheduleSuggestion = {
  suggestionId?: string;
  previewChange: string;
  acceptOp: string;
};

export type ScheduleControls = {
  suggestAlternativesOp?: string;
};

export type TodaySchedulePayload = {
  blocks: ScheduleBlock[];
  suggestions?: ScheduleSuggestion[];
  controls?: ScheduleControls;
};

export type PriorityItem = {
  rank: number;
  taskId: string;
  label: string;
  reason?: string;
  timeEstimateMinutes?: number;
  navigateTo?: SurfaceNavigateTo;
  quickActions?: SurfaceOpTrigger[];
};

export type PriorityListPayload = {
  items: PriorityItem[];
};

export type TriageItem = {
  queueItemId: string;
  source: string;
  subject: string;
  from?: string;
  receivedAt?: string;
  suggestedAction?: string;
  suggestedTask?: {
    taskId: string;
    label?: string;
  };
  approveOp: string;
  declineOp: string;
};

export type TriageGroupActions = {
  approveAllOp?: string;
  declineAllOp?: string;
};

export type TriageGroup = {
  groupId: string;
  label: string;
  summary?: string;
  items: TriageItem[];
  groupActions?: TriageGroupActions;
};

export type TriageTablePayload = {
  groups: TriageGroup[];
};

export type SurfaceEnvelope<K extends SurfaceKind, P> = {
  surface_id: string;
  kind: K;
  title: string;
  payload: P;
};

export type WhatNextV1Surface = SurfaceEnvelope<"what_next_v1", WhatNextPayload>;
export type TodayScheduleV1Surface = SurfaceEnvelope<
  "today_schedule_v1",
  TodaySchedulePayload
>;
export type PriorityListV1Surface = SurfaceEnvelope<
  "priority_list_v1",
  PriorityListPayload
>;
export type TriageTableV1Surface = SurfaceEnvelope<
  "triage_table_v1",
  TriageTablePayload
>;

export type ContextAddItem = {
  contextId: string;
  label: string;
  sourceType?: string;
  summary?: string;
  navigateTo?: SurfaceNavigateTo;
  addOp?: string;
};

export type ContextAddPayload = {
  headline?: string;
  items: ContextAddItem[];
};

export type ContextAddV1Surface = SurfaceEnvelope<
  "context_add_v1",
  ContextAddPayload
>;

export type InteractiveSurface =
  | WhatNextV1Surface
  | TodayScheduleV1Surface
  | PriorityListV1Surface
  | TriageTableV1Surface
  | ContextAddV1Surface;

type UnknownRecord = Record<string, any>;

const LOGGER_PREFIX = "[InteractiveSurfaces]";

function isObject(value: unknown): value is UnknownRecord {
  return Boolean(value) && typeof value === "object";
}

function logSurfaceWarning(message: string, surface?: UnknownRecord) {
  console.warn(
    `${LOGGER_PREFIX} ${message}`,
    surface?.surface_id ? { surface_id: surface.surface_id } : undefined
  );
}

function parseNavigateTo(value: unknown): SurfaceNavigateTo | undefined {
  if (!isObject(value)) {
    return undefined;
  }
  const destination = value.destination;
  if (destination === "workroom_task" && typeof value.taskId === "string") {
    return { destination, taskId: value.taskId };
  }
  if (destination === "hub_queue") {
    return { destination };
  }
  if (
    destination === "hub" &&
    (value.section === undefined ||
      value.section === "today" ||
      value.section === "metrics" ||
      value.section === "priority")
  ) {
    return value.section ? { destination, section: value.section } : { destination };
  }
  if (destination === "calendar_event" && typeof value.eventId === "string") {
    return { destination, eventId: value.eventId };
  }
  return undefined;
}

function parseOpTrigger(value: unknown): SurfaceOpTrigger | undefined {
  if (!isObject(value)) {
    return undefined;
  }
  if (typeof value.label === "string" && typeof value.opToken === "string") {
    return {
      label: value.label,
      opToken: value.opToken,
      confirm: typeof value.confirm === "boolean" ? value.confirm : undefined,
    };
  }
  return undefined;
}

function parseAction(value: unknown): SurfaceAction | undefined {
  const trigger = parseOpTrigger(value);
  if (trigger) {
    return trigger;
  }
  if (!isObject(value) || typeof value.label !== "string") {
    return undefined;
  }
  const navigateTo =
    parseNavigateTo(value.navigateTo) ??
    parseNavigateTo({
      destination: value.destination,
      taskId: value.taskId,
      eventId: value.eventId,
      section: value.section,
    });
  if (!navigateTo) {
    return undefined;
  }
  return { label: value.label, navigateTo };
}

function parseNotes(list: unknown): SurfaceNote[] | undefined {
  if (!Array.isArray(list)) {
    return undefined;
  }
  const items = list
    .map((note) => {
      if (!isObject(note) || typeof note.text !== "string") {
        return undefined;
      }
      return {
        text: note.text,
        icon: typeof note.icon === "string" ? note.icon : undefined,
      };
    })
    .filter(Boolean) as SurfaceNote[];
  return items.length ? items : undefined;
}

function parseWhatNextPayload(payload: unknown): WhatNextPayload | null {
  if (!isObject(payload) || !isObject(payload.primary)) {
    return null;
  }
  const primary = payload.primary;
  if (typeof primary.headline !== "string") {
    return null;
  }
  const parsedPrimary: WhatNextPrimary = {
    headline: primary.headline,
    body: typeof primary.body === "string" ? primary.body : undefined,
    target: parseNavigateTo(primary.target),
    primaryAction: parseAction(primary.primaryAction),
    secondaryActions: Array.isArray(primary.secondaryActions)
      ? (primary.secondaryActions
          .map((action: unknown) => parseAction(action))
          .filter(Boolean) as SurfaceAction[])
      : undefined,
  };
  return {
    primary: parsedPrimary,
    secondaryNotes: parseNotes(payload.secondaryNotes),
  };
}

function parseScheduleBlock(value: unknown): ScheduleBlock | null {
  if (!isObject(value)) {
    return null;
  }
  const requiredStrings: Array<keyof ScheduleBlock> = [
    "blockId",
    "label",
    "start",
    "end",
  ];
  for (const key of requiredStrings) {
    if (typeof value[key] !== "string") {
      return null;
    }
  }
  if (value.type !== "event" && value.type !== "focus") {
    return null;
  }
  if (typeof value.isLocked !== "boolean") {
    return null;
  }
  return {
    blockId: value.blockId,
    type: value.type,
    label: value.label,
    start: value.start,
    end: value.end,
    isLocked: value.isLocked,
    eventId: typeof value.eventId === "string" ? value.eventId : undefined,
    taskId: typeof value.taskId === "string" ? value.taskId : undefined,
  };
}

function parseTodaySchedulePayload(payload: unknown): TodaySchedulePayload | null {
  if (!isObject(payload) || !Array.isArray(payload.blocks)) {
    return null;
  }
  const blocks = payload.blocks
    .map((block: unknown) => parseScheduleBlock(block))
    .filter(Boolean) as ScheduleBlock[];
  if (!blocks.length) {
    return null;
  }
  const suggestions = Array.isArray(payload.suggestions)
    ? (payload.suggestions
        .map((item: unknown) => {
          if (!isObject(item) || typeof item.previewChange !== "string" || typeof item.acceptOp !== "string") {
            return undefined;
          }
          return {
            suggestionId: typeof item.suggestionId === "string" ? item.suggestionId : undefined,
            previewChange: item.previewChange,
            acceptOp: item.acceptOp,
          };
        })
        .filter(Boolean) as ScheduleSuggestion[])
    : undefined;
  const controls = isObject(payload.controls)
    ? {
        suggestAlternativesOp:
          typeof payload.controls.suggestAlternativesOp === "string"
            ? payload.controls.suggestAlternativesOp
            : undefined,
      }
    : undefined;
  return {
    blocks,
    suggestions,
    controls,
  };
}

function parsePriorityListPayload(payload: unknown): PriorityListPayload | null {
  if (!isObject(payload) || !Array.isArray(payload.items)) {
    return null;
  }
  const items = payload.items
    .map((item: unknown) => {
      if (!isObject(item)) {
        return undefined;
      }
      if (
        typeof item.rank !== "number" ||
        typeof item.taskId !== "string" ||
        typeof item.label !== "string"
      ) {
        return undefined;
      }
      return {
        rank: item.rank,
        taskId: item.taskId,
        label: item.label,
        reason: typeof item.reason === "string" ? item.reason : undefined,
        timeEstimateMinutes:
          typeof item.timeEstimateMinutes === "number"
            ? item.timeEstimateMinutes
            : undefined,
        navigateTo: parseNavigateTo(item.navigateTo),
        quickActions: Array.isArray(item.quickActions)
          ? (item.quickActions
              .map((action: unknown) => parseOpTrigger(action))
              .filter(Boolean) as SurfaceOpTrigger[])
          : undefined,
      };
    })
    .filter(Boolean) as PriorityItem[];
  if (!items.length) {
    return null;
  }
  return { items };
}

function parseTriageItem(value: unknown): TriageItem | null {
  if (!isObject(value)) {
    return null;
  }
  const requiredStrings: Array<keyof TriageItem> = [
    "queueItemId",
    "source",
    "subject",
    "approveOp",
    "declineOp",
  ];
  for (const key of requiredStrings) {
    if (typeof value[key] !== "string") {
      return null;
    }
  }
  return {
    queueItemId: value.queueItemId,
    source: value.source,
    subject: value.subject,
    from: typeof value.from === "string" ? value.from : undefined,
    receivedAt: typeof value.receivedAt === "string" ? value.receivedAt : undefined,
    suggestedAction:
      typeof value.suggestedAction === "string" ? value.suggestedAction : undefined,
    suggestedTask:
      isObject(value.suggestedTask) && typeof value.suggestedTask.taskId === "string"
        ? {
            taskId: value.suggestedTask.taskId,
            label:
              typeof value.suggestedTask.label === "string"
                ? value.suggestedTask.label
                : undefined,
          }
        : undefined,
    approveOp: value.approveOp,
    declineOp: value.declineOp,
  };
}

function parseTriageTablePayload(payload: unknown): TriageTablePayload | null {
  if (!isObject(payload) || !Array.isArray(payload.groups)) {
    return null;
  }
  const groups = payload.groups
    .map((group: unknown) => {
      if (!isObject(group)) {
        return undefined;
      }
      if (typeof group.groupId !== "string" || typeof group.label !== "string") {
        return undefined;
      }
      if (!Array.isArray(group.items)) {
        return undefined;
      }
      const items = group.items
        .map((item: unknown) => parseTriageItem(item))
        .filter(Boolean) as TriageItem[];
      if (!items.length) {
        return undefined;
      }
      return {
        groupId: group.groupId,
        label: group.label,
        summary: typeof group.summary === "string" ? group.summary : undefined,
        items,
        groupActions: isObject(group.groupActions)
          ? {
              approveAllOp:
                typeof group.groupActions.approveAllOp === "string"
                  ? group.groupActions.approveAllOp
                  : undefined,
              declineAllOp:
                typeof group.groupActions.declineAllOp === "string"
                  ? group.groupActions.declineAllOp
                  : undefined,
            }
          : undefined,
      };
    })
    .filter(Boolean) as TriageGroup[];
  if (!groups.length) {
    return null;
  }
  return { groups };
}

function parseContextAddPayload(payload: unknown): ContextAddPayload | null {
  if (!isObject(payload) || !Array.isArray(payload.items)) {
    return null;
  }

  const items = payload.items
    .map((item: unknown) => {
      if (!isObject(item) || typeof item.contextId !== "string" || typeof item.label !== "string") {
        return undefined;
      }
      return {
        contextId: item.contextId,
        label: item.label,
        sourceType: typeof item.sourceType === "string" ? item.sourceType : undefined,
        summary: typeof item.summary === "string" ? item.summary : undefined,
        navigateTo: parseNavigateTo(item.navigateTo),
        addOp: typeof item.addOp === "string" ? item.addOp : undefined,
      } as ContextAddItem;
    })
    .filter(Boolean) as ContextAddItem[];

  if (!items.length) {
    return null;
  }

  return {
    headline: typeof payload.headline === "string" ? payload.headline : undefined,
    items,
  };
}

function normalizeSurface(
  raw: UnknownRecord
): InteractiveSurface | undefined {
  if (
    typeof raw.surface_id !== "string" ||
    typeof raw.kind !== "string" ||
    typeof raw.title !== "string"
  ) {
    return undefined;
  }
  const base = {
    surface_id: raw.surface_id,
    kind: raw.kind as SurfaceKind,
    title: raw.title,
  };
  switch (raw.kind) {
    case "what_next_v1": {
      const payload = parseWhatNextPayload(raw.payload);
      if (!payload) return undefined;
      return { ...base, kind: "what_next_v1", payload };
    }
    case "today_schedule_v1": {
      const payload = parseTodaySchedulePayload(raw.payload);
      if (!payload) return undefined;
      return { ...base, kind: "today_schedule_v1", payload };
    }
    case "priority_list_v1": {
      const payload = parsePriorityListPayload(raw.payload);
      if (!payload) return undefined;
      return { ...base, kind: "priority_list_v1", payload };
    }
    case "triage_table_v1": {
      const payload = parseTriageTablePayload(raw.payload);
      if (!payload) return undefined;
      return { ...base, kind: "triage_table_v1", payload };
    }
    case "context_add_v1": {
      const payload = parseContextAddPayload(raw.payload);
      if (!payload) return undefined;
      return { ...base, kind: "context_add_v1", payload };
    }
    default:
      return undefined;
  }
}

// Cache for parsed surfaces by surface_id + payload hash
type CacheEntry = {
  surface: InteractiveSurface;
  payloadHash: string;
};

const SURFACE_CACHE_SIZE = 100;
const surfaceCache = new Map<string, CacheEntry>();

// Simple hash function for payload comparison
function hashPayload(payload: unknown): string {
  try {
    return JSON.stringify(payload);
  } catch {
    return String(payload);
  }
}

// LRU eviction: remove oldest entries when cache exceeds size
function evictOldestCacheEntries() {
  if (surfaceCache.size <= SURFACE_CACHE_SIZE) {
    return;
  }
  const entriesToRemove = surfaceCache.size - SURFACE_CACHE_SIZE;
  const keysToRemove = Array.from(surfaceCache.keys()).slice(0, entriesToRemove);
  keysToRemove.forEach((key) => surfaceCache.delete(key));
}

/**
 * Normalize raw surface payloads coming from the LLM into typed envelopes.
 * Results are memoized by surface_id + payload hash to avoid re-parsing identical surfaces.
 */
export function parseInteractiveSurfaces(
  input: unknown
): InteractiveSurface[] {
  if (!Array.isArray(input)) {
    return [];
  }
  const surfaces: InteractiveSurface[] = [];
  for (const raw of input) {
    if (!isObject(raw)) {
      logSurfaceWarning("Surface skipped: not an object");
      continue;
    }

    // Check cache: use surface_id + payload hash as key
    const surfaceId = typeof raw.surface_id === "string" ? raw.surface_id : null;
    const payloadHash = hashPayload(raw.payload);
    const cacheKey = surfaceId ? `${surfaceId}:${payloadHash}` : null;

    if (cacheKey) {
      const cached = surfaceCache.get(cacheKey);
      if (cached && cached.payloadHash === payloadHash) {
        // Cache hit: reuse parsed surface
        surfaces.push(cached.surface);
        continue;
      }
    }

    // Cache miss: parse surface
    const normalized = normalizeSurface(raw);
    if (normalized) {
      surfaces.push(normalized);
      // Store in cache if we have a surface_id
      if (cacheKey) {
        evictOldestCacheEntries();
        surfaceCache.set(cacheKey, {
          surface: normalized,
          payloadHash,
        });
      }
    } else {
      logSurfaceWarning("Surface skipped: invalid schema", raw);
    }
  }
  return surfaces;
}

/**
 * Clear the surface parsing cache (useful for testing or memory management).
 */
export function clearSurfaceCache(): void {
  surfaceCache.clear();
}

