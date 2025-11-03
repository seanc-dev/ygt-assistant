import useSWR from "swr";
import { api } from "../lib/api";

/**
 * Hook to fetch summary data from /api/brief/today (includes weather/news)
 * Returns greeting, weather, news, and status flags
 */
export function useSummary() {
  return useSWR("/api/brief/today", () => api.briefToday(), {
    refreshInterval: 60000, // Refresh every minute
    revalidateOnFocus: true,
    fallbackData: { ok: true, weather: null, news: [] },
  });
}

/**
 * Hook to fetch today's schedule from /api/schedule/today
 */
export function useToday() {
  return useSWR("/api/schedule/today", () => api.scheduleToday(), {
    refreshInterval: 30000, // Refresh every 30 seconds
    revalidateOnFocus: true,
  });
}

/**
 * Hook to fetch queue items from /api/queue with polling
 */
export function useQueue(options?: { pollMs?: number }) {
  const pollMs = options?.pollMs ?? 30000;
  return useSWR("/api/queue", () => api.queue(), {
    refreshInterval: pollMs,
    revalidateOnFocus: true,
  });
}

/**
 * Hook to fetch recent items from /api/summary/recent
 * Mocked for now - returns empty array
 */
export function useRecent() {
  // TODO: Replace with actual endpoint when available
  return useSWR(
    "/api/summary/recent",
    () => api.summaryRecent().catch(() => ({ ok: true, items: [] })),
    {
      refreshInterval: 60000,
      revalidateOnFocus: true,
      fallbackData: { ok: true, items: [] },
    }
  );
}

/**
 * Hook to fetch user settings from /api/settings
 */
export function useSettings() {
  return useSWR("/api/settings", () => api.settings(), {
    refreshInterval: 300000, // Refresh every 5 minutes
    revalidateOnFocus: false,
  });
}

/**
 * Hook to fetch user profile from /api/profile
 */
export function useProfile() {
  return useSWR("/api/profile", () => api.profile(), {
    refreshInterval: 300000, // Refresh every 5 minutes
    revalidateOnFocus: false,
  });
}
