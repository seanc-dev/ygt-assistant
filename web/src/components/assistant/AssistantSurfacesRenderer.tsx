import type {
  InteractiveSurface,
  SurfaceNavigateTo,
} from "../../lib/llm/surfaces";
import { WhatNextSurface } from "./WhatNextSurface";
import { TodayScheduleSurface } from "./TodayScheduleSurface";
import { PriorityListSurface } from "./PriorityListSurface";
import { TriageTableSurface } from "./TriageTableSurface";

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
    const commonProps = {
      surface,
      onInvokeOp,
      onNavigate,
    };
    switch (surface.kind) {
      case "what_next_v1":
        return <WhatNextSurface {...commonProps} />;
      case "today_schedule_v1":
        return <TodayScheduleSurface {...commonProps} />;
      case "priority_list_v1":
        return <PriorityListSurface {...commonProps} />;
      case "triage_table_v1":
        return <TriageTableSurface {...commonProps} />;
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

