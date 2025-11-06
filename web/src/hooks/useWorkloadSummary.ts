import useSWR from "swr";
import { api } from "../lib/api";
import type { WorkloadSummary } from "../lib/workload";

/**
 * Hook to fetch workload summary from /api/workload/summary.
 * Refetches every 60 seconds and on focus.
 */
export function useWorkloadSummary() {
  return useSWR<WorkloadSummary>(
    "/api/workload/summary",
    () => api.getWorkloadSummary(),
    {
      refreshInterval: 60000, // Refresh every 60 seconds
      revalidateOnFocus: true,
      fallbackData: {
        plannedMin: 0,
        activeMin: 0,
        overrunMin: 0,
        today: { items: [] },
        weekly: { triaged: 0, completed: 0 },
        rating: "manageable",
      },
    }
  );
}

