/**
 * Schedule utility functions and types for managing calendar events and blocks.
 */

export type ScheduleItemType = "event" | "block";

export interface ScheduleItem {
  id: string;
  title: string;
  start: string; // ISO datetime string
  end: string; // ISO datetime string
  type: ScheduleItemType;
  kind?: string; // For blocks: "work", "personal", etc.
  tasks?: string[]; // Task names for blocks
  note?: string;
}

export interface PeriodGroup {
  period: "morning" | "afternoon" | "evening";
  label: string;
  items: ScheduleItem[];
}

/**
 * Format a time string to HH:MM format.
 */
export function formatTime(isoString: string): string {
  const date = new Date(isoString);
  const hours = date.getHours().toString().padStart(2, "0");
  const minutes = date.getMinutes().toString().padStart(2, "0");
  return `${hours}:${minutes}`;
}

/**
 * Format a time range from start to end.
 */
export function formatTimeRange(start: string, end: string): string {
  return `${formatTime(start)} - ${formatTime(end)}`;
}

/**
 * Check if a time is in the past.
 */
export function isPast(isoString: string): boolean {
  return new Date(isoString) < new Date();
}

/**
 * Get the accent color class for a schedule item based on its type and source.
 */
export function getAccentColor(item: ScheduleItem): string {
  if (item.type === "event") {
    // Events get blue accent
    return "border-l-4 border-l-blue-400";
  } else if (item.type === "block") {
    // Blocks get green accent
    return "border-l-4 border-l-green-400";
  }
  return "";
}

/**
 * Check if a schedule item overlaps with any other items.
 */
export function hasOverlap(
  item: ScheduleItem,
  items: ScheduleItem[],
  currentIndex: number
): boolean {
  const itemStart = new Date(item.start).getTime();
  const itemEnd = new Date(item.end).getTime();

  for (let i = 0; i < items.length; i++) {
    if (i === currentIndex) continue;

    const other = items[i];
    const otherStart = new Date(other.start).getTime();
    const otherEnd = new Date(other.end).getTime();

    // Check for overlap: items overlap if one starts before the other ends
    if (
      (itemStart < otherEnd && itemEnd > otherStart) ||
      (otherStart < itemEnd && otherEnd > itemStart)
    ) {
      return true;
    }
  }

  return false;
}

/**
 * Add minutes to an ISO datetime string.
 */
function addMinutes(isoString: string, minutes: number): string {
  const date = new Date(isoString);
  date.setMinutes(date.getMinutes() + minutes);
  return date.toISOString();
}

/**
 * Apply a time delta (in minutes) to an event's start and end times.
 */
export function applyDelta(
  { start, end }: { start: string; end: string },
  deltaMinutes: number
): { start: string; end: string } {
  const duration = new Date(end).getTime() - new Date(start).getTime();
  const newStart = addMinutes(start, deltaMinutes);
  const newEnd = new Date(new Date(newStart).getTime() + duration).toISOString();
  return { start: newStart, end: newEnd };
}

/**
 * Defer an event to a specific period (afternoon or tomorrow morning).
 */
export function deferTo(
  { start, end }: { start: string; end: string },
  period: "afternoon" | "tomorrow_morning"
): { start: string; end: string } {
  const duration = new Date(end).getTime() - new Date(start).getTime();
  const now = new Date();
  let targetStart: Date;

  if (period === "afternoon") {
    targetStart = new Date(now);
    targetStart.setHours(14, 0, 0, 0); // 2 PM
    if (targetStart < now) {
      targetStart.setDate(targetStart.getDate() + 1);
    }
  } else {
    // tomorrow_morning
    targetStart = new Date(now);
    targetStart.setDate(targetStart.getDate() + 1);
    targetStart.setHours(9, 0, 0, 0); // 9 AM
  }

  const newEnd = new Date(targetStart.getTime() + duration).toISOString();
  return { start: targetStart.toISOString(), end: newEnd };
}

/**
 * Group schedule items by time period (Morning, Afternoon, Evening).
 */
export function segmentByPeriod(items: ScheduleItem[]): PeriodGroup[] {
  const groups: PeriodGroup[] = [
    { period: "morning", label: "Morning", items: [] },
    { period: "afternoon", label: "Afternoon", items: [] },
    { period: "evening", label: "Evening", items: [] },
  ];

  for (const item of items) {
    const hour = new Date(item.start).getHours();
    if (hour < 12) {
      groups[0].items.push(item);
    } else if (hour < 18) {
      groups[1].items.push(item);
    } else {
      groups[2].items.push(item);
    }
  }

  // Filter out empty groups
  return groups.filter((group) => group.items.length > 0);
}

/**
 * Normalize command text for processing.
 */
export function normalizeCommandText(text: string): string {
  return text.trim().replace(/\s+/g, " ").replace(/\n/g, " ");
}
