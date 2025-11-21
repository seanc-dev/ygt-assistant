import type {
  InteractiveSurface,
  PriorityListV1Surface,
  SurfaceAction,
  SurfaceNavigateTo,
  WhatNextV1Surface,
} from "./llm/surfaces";
import type { WorkroomContext } from "./workroomContext";

const collectNavigateTargetsFromAction = (
  action?: SurfaceAction
): SurfaceNavigateTo[] => {
  if (!action || !("navigateTo" in action)) return [];
  return action.navigateTo ? [action.navigateTo] : [];
};

const collectNavigateTargets = (
  surface: InteractiveSurface
): SurfaceNavigateTo[] => {
  if (surface.kind === "what_next_v1") {
    const { primary } = (surface as WhatNextV1Surface).payload;
    const actions = [primary.primaryAction, ...(primary.secondaryActions || [])];
    const targets = actions.flatMap((action) =>
      collectNavigateTargetsFromAction(action)
    );
    return primary.target ? [primary.target, ...targets] : targets;
  }

  if (surface.kind === "priority_list_v1") {
    return (surface as PriorityListV1Surface).payload.items.flatMap((item) =>
      item.navigateTo ? [item.navigateTo] : []
    );
  }

  return [];
};

const buildVisibleTargets = (context: WorkroomContext | null) => {
  if (!context) return null;

  const visibleTasks = new Set<string>();
  const visibleEvents = new Set<string>();

  if (context.anchor.type === "task") {
    visibleTasks.add(context.anchor.id);
    if (context.anchor.linkedEventId) {
      visibleEvents.add(context.anchor.linkedEventId);
    }
  }

  if (context.anchor.type === "event") {
    visibleEvents.add(context.anchor.id);
  }

  context.neighborhood.tasks?.forEach((task) => {
    if (task.id) visibleTasks.add(task.id);
  });

  context.neighborhood.events?.forEach((event) => {
    if (event.id) visibleEvents.add(event.id);
  });

  return { visibleTasks, visibleEvents };
};

const isNavigationAllowed = (
  nav: SurfaceNavigateTo,
  targets: { visibleTasks: Set<string>; visibleEvents: Set<string> }
) => {
  switch (nav.destination) {
    case "workroom_task":
      return targets.visibleTasks.has(nav.taskId);
    case "calendar_event":
      return targets.visibleEvents.has(nav.eventId);
    default:
      return true;
  }
};

export function filterSurfacesByWorkroomContext(
  surfaces: InteractiveSurface[] | undefined,
  context: WorkroomContext | null
): InteractiveSurface[] | undefined {
  if (!surfaces || surfaces.length === 0) return surfaces;

  const targets = buildVisibleTargets(context);
  if (!targets) return surfaces;

  return surfaces.filter((surface) => {
    const navigateTargets = collectNavigateTargets(surface);
    if (navigateTargets.length === 0) return true;

    return navigateTargets.every((nav) => isNavigationAllowed(nav, targets));
  });
}
