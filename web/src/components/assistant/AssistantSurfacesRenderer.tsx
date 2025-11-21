import type {
  InteractiveSurface,
  SurfaceNavigateTo,
  WhatNextV1Surface,
  TodayScheduleV1Surface,
  PriorityListV1Surface,
  TriageTableV1Surface,
  ContextAddV1Surface,
} from "../../lib/llm/surfaces";
import { WhatNextSurface } from "./WhatNextSurface";
import { TodayScheduleSurface } from "./TodayScheduleSurface";
import { PriorityListSurface } from "./PriorityListSurface";
import { TriageTableSurface } from "./TriageTableSurface";
import { ContextAddSurface } from "./ContextAddSurface";

export type AssistantSurfacesRendererProps = {
  surfaces?: InteractiveSurface[];
  onInvokeOp?: (opToken: string, options?: { confirm?: boolean }) => void;
  onNavigate?: (nav: SurfaceNavigateTo) => void;
};

/**
 * Render a stack of interactive surfaces underneath an assistant message bubble.
 */
export function AssistantSurfacesRenderer({
  surfaces,
  onInvokeOp,
  onNavigate,
}: AssistantSurfacesRendererProps) {
  const renderSurface = (surface: InteractiveSurface) => {
    switch (surface.kind) {
      case "what_next_v1":
        return (
          <WhatNextSurface
            surface={surface as WhatNextV1Surface}
            onInvokeOp={onInvokeOp}
            onNavigate={onNavigate}
          />
        );
      case "today_schedule_v1":
        return (
          <TodayScheduleSurface
            surface={surface as TodayScheduleV1Surface}
            onInvokeOp={onInvokeOp}
            onNavigate={onNavigate}
          />
        );
      case "priority_list_v1":
        return (
          <PriorityListSurface
            surface={surface as PriorityListV1Surface}
            onInvokeOp={onInvokeOp}
            onNavigate={onNavigate}
          />
        );
      case "triage_table_v1":
        return (
          <TriageTableSurface
            surface={surface as TriageTableV1Surface}
            onInvokeOp={onInvokeOp}
            onNavigate={onNavigate}
          />
        );
      case "context_add_v1":
        return (
          <ContextAddSurface
            surface={surface as ContextAddV1Surface}
            onInvokeOp={onInvokeOp}
            onNavigate={onNavigate}
          />
        );
      default:
        return null;
    }
  };

  if (!surfaces || surfaces.length === 0) {
    return null;
  }

  return (
    <div
      className="flex flex-col gap-4 w-full"
      data-testid="assistant-surfaces-root"
    >
      {surfaces.map((surface) => (
        <div
          key={surface.surface_id}
          className="w-full"
          data-testid={`surface-${surface.kind}`}
        >
          {renderSurface(surface)}
        </div>
      ))}
    </div>
  );
}

