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
        capacityMin: 480,
        plannedMin: 0,
        focusedMin: 0,
        overbookedMin: 0,
        today: { focus: [] },
        flowWeek: {
          deferred: 0,
          scheduled: 0,
          planned: 0,
          completed: 0,
          total: 0,
        },
        lastSyncIso: new Date().toISOString(),
        rating: "manageable",
      },
    }
  );
}
