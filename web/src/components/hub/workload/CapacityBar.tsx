import {
  formatHours,
  freeMin,
} from "../../../lib/workload";
import { Tooltip } from "../../ui/Tooltip";

interface CapacityBarProps {
  capacityMin: number;
  plannedMin: number;
  focusedMin: number;
  overbookedMin: number;
}

/**
 * Capacity bar showing planned, focused, free/overbooked segments.
 * Primary visual focal point with legend showing hours.
 */
export function CapacityBar({
  capacityMin,
  plannedMin,
  focusedMin,
  overbookedMin,
}: CapacityBarProps) {
  const free = freeMin(capacityMin, plannedMin);
  const isOverbooked = overbookedMin > 0;
  
  // Calculate percentages for segments
  const plannedPercent = capacityMin > 0 ? (plannedMin / capacityMin) * 100 : 0;
  const focusedPercent = capacityMin > 0 ? (Math.min(focusedMin, plannedMin) / capacityMin) * 100 : 0;
  const freePercent = capacityMin > 0 ? (free / capacityMin) * 100 : 0;
  const overbookedPercent = capacityMin > 0 ? (overbookedMin / capacityMin) * 100 : 0;
  
  // Format display values
  const plannedH = formatHours(plannedMin);
  const focusedH = formatHours(focusedMin);
  const freeH = formatHours(free);
  const overbookedH = formatHours(overbookedMin);
  
  // Build aria label
  const ariaLabel = isOverbooked
    ? `Planned ${plannedH}, Focused ${focusedH}, Overbooked ${overbookedH}`
    : `Planned ${plannedH}, Focused ${focusedH}, Free ${freeH}`;
  
  // Caption text
  const captionText = isOverbooked
    ? `${plannedH} planned • ${focusedH} focused • +${overbookedH} overbooked`
    : `${plannedH} planned • ${focusedH} focused • ${freeH} free`;
  
  return (
    <div className="space-y-2">
      {/* Progress bar container */}
      <div className="relative">
        <div
          className="h-3 w-full rounded-full bg-slate-200 overflow-hidden relative"
          role="img"
          aria-label={ariaLabel}
        >
          {/* Planned segment */}
          {plannedPercent > 0 && (
            <div
              className="bg-sky-300 transition-all duration-150 relative rounded-full h-full"
              style={{ width: `${plannedPercent}%` }}
            >
              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-sky-300/20 to-transparent" />
            </div>
          )}
          
          {/* Focused overlay */}
          {focusedPercent > 0 && (
            <div
              className="absolute left-0 top-0 h-full bg-emerald-500 rounded-full transition-all duration-150"
              style={{ width: `${focusedPercent}%` }}
            />
          )}
          
          {/* Free segment (right side) */}
          {freePercent > 0 && (
            <div
              className="absolute right-0 top-0 h-full bg-slate-200 transition-all duration-150 rounded-full"
              style={{ width: `${freePercent}%` }}
            />
          )}
        </div>
        
        {/* Overbooked segment (extends beyond capacity) */}
        {overbookedPercent > 0 && (
          <div
            className="absolute top-0 h-3 bg-amber-400 transition-all duration-150 rounded-full"
            style={{
              left: "100%",
              width: `${overbookedPercent}%`,
              marginLeft: "2px",
            }}
          />
        )}
      </div>
      
      {/* Caption with legend */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <p className="text-sm text-slate-600">{captionText}</p>
        
        {/* Legend with hours */}
        <div className="flex items-center gap-3 text-xs text-slate-500">
          <Tooltip label="Time already scheduled today.">
            <div className="flex items-center gap-1">
              <div className="h-2 w-2 rounded-full bg-sky-300" />
              <span>Planned ({plannedH})</span>
            </div>
          </Tooltip>
          <Tooltip label="Time spent in active focus sessions.">
            <div className="flex items-center gap-1">
              <div className="h-2 w-2 rounded-full bg-emerald-500" />
              <span>Focused ({focusedH})</span>
            </div>
          </Tooltip>
          {!isOverbooked && (
            <Tooltip label="Remaining capacity based on your daily target.">
              <div className="flex items-center gap-1">
                <div className="h-2 w-2 rounded-full bg-slate-200 border border-slate-300" />
                <span>Free ({freeH})</span>
              </div>
            </Tooltip>
          )}
          {isOverbooked && (
            <Tooltip label="You've scheduled more than your capacity.">
              <div className="flex items-center gap-1">
                <div className="h-2 w-2 rounded-full bg-amber-400" />
                <span>Overbooked ({overbookedH})</span>
              </div>
            </Tooltip>
          )}
        </div>
      </div>
    </div>
  );
}

