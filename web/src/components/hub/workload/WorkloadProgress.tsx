import { segmentMinutes, formatMinutes } from "../../lib/workload";

interface WorkloadProgressProps {
  plannedMin: number;
  activeMin: number;
  overrunMin: number;
}

/**
 * Segmented progress bar showing planned, active, and overrun minutes.
 */
export function WorkloadProgress({
  plannedMin,
  activeMin,
  overrunMin,
}: WorkloadProgressProps) {
  const segments = segmentMinutes(plannedMin, activeMin + overrunMin);
  
  const totalMin = plannedMin + overrunMin;
  const ariaLabel = `Workload: ${formatMinutes(plannedMin)} planned, ${formatMinutes(activeMin)} active, ${formatMinutes(overrunMin)} overrun`;
  
  return (
    <div className="space-y-2">
      <div className="flex justify-between text-sm">
        <span className="text-slate-600">Workload</span>
        <span className="font-medium text-slate-900">
          {formatMinutes(totalMin)} planned
        </span>
      </div>
      
      <div
        className="h-3 w-full rounded-full bg-slate-200 overflow-hidden flex"
        role="progressbar"
        aria-label={ariaLabel}
        aria-valuenow={totalMin}
        aria-valuemin={0}
        aria-valuemax={480}
      >
        {/* Planned segment */}
        {segments.planned > 0 && (
          <div
            className="bg-sky-300 transition-all duration-150"
            style={{ width: `${segments.planned}%` }}
            title={`Planned: ${formatMinutes(plannedMin)}`}
          />
        )}
        
        {/* Active segment */}
        {segments.active > 0 && (
          <div
            className="bg-emerald-500 transition-all duration-150"
            style={{ width: `${segments.active}%` }}
            title={`Active: ${formatMinutes(activeMin)}`}
          />
        )}
        
        {/* Overrun segment */}
        {segments.overrun > 0 && (
          <div
            className="bg-amber-400 transition-all duration-150"
            style={{ width: `${segments.overrun}%` }}
            title={`Overrun: ${formatMinutes(overrunMin)}`}
          />
        )}
      </div>
      
      <div className="flex gap-4 text-xs text-slate-600">
        <span>Planned: {formatMinutes(plannedMin)}</span>
        <span>Active: {formatMinutes(activeMin)}</span>
        {overrunMin > 0 && <span>Overrun: {formatMinutes(overrunMin)}</span>}
      </div>
    </div>
  );
}

