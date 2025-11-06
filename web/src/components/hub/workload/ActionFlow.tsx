import { useState, useCallback } from "react";
import {
  ChevronDown24Regular,
  ChevronUp24Regular,
} from "@fluentui/react-icons";
import type { FlowWeek } from "../../../lib/workload";

interface ActionFlowProps {
  flowWeek: FlowWeek;
}

/**
 * Action Flow component showing weekly lifecycle summary.
 * Segmented bar with four stages: Deferred → Scheduled → Planned → Completed.
 */
export function ActionFlow({ flowWeek }: ActionFlowProps) {
  const [expanded, setExpanded] = useState(false);

  const toggleExpanded = useCallback(() => {
    setExpanded(!expanded);
  }, [expanded]);

  const { deferred, scheduled, planned, completed, total } = flowWeek;

  // Calculate percentages for segments
  // IMPORTANT: Normalize by total (sum of all categories), not maxValue.
  // This ensures segments always add up to 100% and prevents bar overflow.
  // Using maxValue would cause segments to exceed 100% when one category
  // is larger than others (e.g., 10 deferred + 5 scheduled = 200% width).
  const deferredPercent = total > 0 ? (deferred / total) * 100 : 0;
  const scheduledPercent = total > 0 ? (scheduled / total) * 100 : 0;
  const plannedPercent = total > 0 ? (planned / total) * 100 : 0;
  const completedPercent = total > 0 ? (completed / total) * 100 : 0;

  return (
    <div className="space-y-2">
      {/* Segmented bar */}
      <div
        className="h-3 w-full rounded-full overflow-hidden flex relative"
        role="img"
        aria-label={`Action flow: ${deferred} deferred, ${scheduled} scheduled, ${planned} planned, ${completed} completed`}
      >
        {/* Deferred */}
        {deferred > 0 && (
          <div
            className="bg-slate-300 transition-all duration-150"
            style={{ width: `${deferredPercent}%` }}
            title="Moved out of today or to later."
          />
        )}

        {/* Scheduled */}
        {scheduled > 0 && (
          <div
            className="bg-sky-300 transition-all duration-150"
            style={{ width: `${scheduledPercent}%` }}
            title="Assigned a specific time window."
          />
        )}

        {/* Planned */}
        {planned > 0 && (
          <div
            className="bg-emerald-400 transition-all duration-150"
            style={{ width: `${plannedPercent}%` }}
            title="Committed to upcoming capacity."
          />
        )}

        {/* Completed */}
        {completed > 0 && (
          <div
            className="bg-indigo-500 transition-all duration-150"
            style={{ width: `${completedPercent}%` }}
            title="Done and archived."
          />
        )}
      </div>

      {/* Caption */}
      <p className="text-sm text-slate-600">{total} actions this week</p>

      {/* Accordion (md+ only) */}
      <div className="hidden md:block">
        <button
          onClick={toggleExpanded}
          className="flex items-center gap-1 text-xs text-slate-500 hover:text-slate-700 transition-colors"
          aria-expanded={expanded}
          aria-label="Toggle action flow details"
        >
          {expanded ? (
            <ChevronUp24Regular className="w-4 h-4" />
          ) : (
            <ChevronDown24Regular className="w-4 h-4" />
          )}
          <span>Details</span>
        </button>

        {expanded && (
          <div className="mt-2 space-y-1 text-xs text-slate-600">
            <div className="flex items-center justify-between">
              <span>Deferred</span>
              <span className="font-semibold text-slate-800">{deferred}</span>
            </div>
            <div className="flex items-center justify-between">
              <span>Scheduled</span>
              <span className="font-semibold text-slate-800">{scheduled}</span>
            </div>
            <div className="flex items-center justify-between">
              <span>Planned</span>
              <span className="font-semibold text-slate-800">{planned}</span>
            </div>
            <div className="flex items-center justify-between">
              <span>Completed</span>
              <span className="font-semibold text-slate-800">{completed}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
