/**
 * Workload calculation utilities and thresholds.
 */

export type WorkloadRating = "manageable" | "rising" | "overloaded";

export interface WorkloadSegments {
  planned: number; // Planned minutes as percentage of total
  active: number; // Active minutes as percentage of total
  overrun: number; // Overrun minutes as percentage of total
}

export interface WorkloadSummary {
  plannedMin: number;
  activeMin: number;
  overrunMin: number;
  today: {
    items: Array<{
      id: string;
      title: string;
      due: string | null;
      source: "queue" | "calendar";
      priority: "low" | "med" | "high";
    }>;
  };
  weekly: {
    triaged: number;
    completed: number;
  };
  rating: WorkloadRating;
}

/**
 * Calculate segmented minutes distribution for progress bar.
 * Returns percentages for planned, active, and overrun segments.
 */
export function segmentMinutes(
  plannedMin: number,
  activeMin: number,
  totalCapacityMin: number = 480 // Default 8 hours
): WorkloadSegments {
  const total = Math.max(plannedMin + activeMin, totalCapacityMin);
  
  const planned = total > 0 ? (plannedMin / total) * 100 : 0;
  const active = total > 0 ? (Math.min(activeMin, plannedMin) / total) * 100 : 0;
  const overrun = total > 0 ? (Math.max(0, activeMin - plannedMin) / total) * 100 : 0;
  
  return {
    planned: Math.min(planned, 100),
    active: Math.min(active, 100),
    overrun: Math.min(overrun, 100),
  };
}

/**
 * Rate workload based on metrics.
 * Returns "manageable" | "rising" | "overloaded"
 */
export function rateWorkload(
  plannedMin: number,
  activeMin: number,
  openItems: number = 0,
  completed: number = 0,
  triaged: number = 0
): WorkloadRating {
  const plannedHours = plannedMin / 60;
  
  // Base rating on planned hours
  if (plannedHours < 8) {
    return "manageable";
  } else if (plannedHours < 10) {
    return "rising";
  } else {
    return "overloaded";
  }
}

/**
 * Pick top N items for today's display.
 * Limited to specified count, prioritized by due date and priority.
 */
export function pickToday<T extends { due?: string | null; priority?: string }>(
  items: T[],
  limit: number = 5
): T[] {
  // Sort by: high priority first, then by due date, then original order
  const sorted = [...items].sort((a, b) => {
    const priorityOrder = { high: 0, med: 1, low: 2 };
    const aPriority = priorityOrder[a.priority as keyof typeof priorityOrder] ?? 1;
    const bPriority = priorityOrder[b.priority as keyof typeof priorityOrder] ?? 1;
    
    if (aPriority !== bPriority) {
      return aPriority - bPriority;
    }
    
    // Compare due dates
    if (a.due && b.due) {
      return a.due.localeCompare(b.due);
    }
    if (a.due) return -1;
    if (b.due) return 1;
    
    return 0;
  });
  
  return sorted.slice(0, limit);
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

