/**
 * Workload calculation utilities and thresholds.
 */

export type WorkloadRating = "manageable" | "rising" | "overloaded";

export interface FlowWeek {
  deferred: number;
  scheduled: number;
  planned: number;
  completed: number;
  total: number;
}

export interface FocusItem {
  id: string;
  title: string;
  source: "calendar" | "task" | "ai";
  urgent?: boolean;
}

export interface WorkloadSummary {
  capacityMin: number; // User-configured daily capacity
  plannedMin: number; // Scheduled today
  focusedMin: number; // Logged/started focus
  overbookedMin: number; // plannedMin - capacityMin, clamped >=0
  today: {
    focus: FocusItem[];
  };
  flowWeek: FlowWeek;
  lastSyncIso: string;
  rating: WorkloadRating;
}

/**
 * Calculate free minutes (capacity - planned).
 */
export function freeMin(capacityMin: number, plannedMin: number): number {
  return Math.max(capacityMin - plannedMin, 0);
}

/**
 * Calculate overbooked minutes (planned - capacity).
 */
export function overbookedMin(capacityMin: number, plannedMin: number): number {
  return Math.max(plannedMin - capacityMin, 0);
}

/**
 * Calculate utilization percentage.
 */
export function utilizationPct(capacityMin: number, plannedMin: number): number {
  return capacityMin > 0 ? plannedMin / capacityMin : 0;
}

/**
 * Calculate focus ratio (focused / planned).
 */
export function focusRatio(plannedMin: number, focusedMin: number): number {
  return plannedMin > 0 ? focusedMin / plannedMin : 0;
}

/**
 * Rate workload based on capacity thresholds.
 * Returns "manageable" | "rising" | "overloaded"
 */
export function rateWorkload(
  capacityMin: number,
  plannedMin: number
): WorkloadRating {
  const overbooked = overbookedMin(capacityMin, plannedMin);
  const utilization = utilizationPct(capacityMin, plannedMin);
  
  // Overloaded if overbooked OR utilization > 95%
  if (overbooked > 0 || utilization > 0.95) {
    return "overloaded";
  }
  
  // Rising if utilization 75-95%
  if (utilization >= 0.75) {
    return "rising";
  }
  
  // Manageable otherwise
  return "manageable";
}

/**
 * Format minutes to hours display.
 */
export function formatMinutes(minutes: number): string {
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  if (hours > 0 && mins > 0) {
    return `${hours}h ${mins}m`;
  } else if (hours > 0) {
    return `${hours}h`;
  } else {
    return `${mins}m`;
  }
}

/**
 * Format hours only (for display).
 */
export function formatHours(minutes: number): string {
  const hours = Math.floor(minutes / 60);
  return `${hours}h`;
}

/**
 * Format relative time from ISO string.
 */
export function formatRelativeTime(isoString: string): string {
  const date = new Date(isoString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);
  
  if (diffMins < 1) {
    return "just now";
  } else if (diffMins < 60) {
    return `${diffMins}m ago`;
  } else if (diffHours < 24) {
    return `${diffHours}h ago`;
  } else if (diffDays === 1) {
    return "yesterday";
  } else {
    return `${diffDays}d ago`;
  }
}
