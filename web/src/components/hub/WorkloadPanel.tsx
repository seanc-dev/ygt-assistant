import { Panel, Stack, Heading, Text, Button } from "@ygt-assistant/ui";
import { useWorkloadSummary } from "../../hooks/useWorkloadSummary";
import { WorkloadProgress } from "./workload/WorkloadProgress";
import { WorkloadToday } from "./workload/WorkloadToday";
import { WorkloadStats } from "./workload/WorkloadStats";
import { WorkloadStatus } from "./workload/WorkloadStatus";
import { useRouter } from "next/router";
import { useCallback, useState } from "react";
import { Add24Regular, Sync24Regular } from "@fluentui/react-icons";
import { isNotionSyncEnabled, pushWorkloadWeeklyDigest } from "../../lib/notionSync";

interface WorkloadPanelProps {
  onAddFocusBlock?: () => void;
}

/**
 * Workload Intelligence Panel - orchestrator component.
 * Displays capacity, progress, today's items, weekly stats, and rating.
 */
export function WorkloadPanel({ onAddFocusBlock }: WorkloadPanelProps) {
  const { data: workload, isLoading } = useWorkloadSummary();
  const router = useRouter();
  const [isSyncing, setIsSyncing] = useState(false);
  const notionSyncEnabled = isNotionSyncEnabled();
  
  const handleReviewQueue = useCallback(() => {
    router.push("/hub#action-queue");
  }, [router]);
  
  const handlePlanTomorrow = useCallback(() => {
    router.push("/hub");
    // TODO: Open planning interface
  }, [router]);
  
  const handleSyncToNotion = useCallback(async () => {
    if (!workload || isSyncing) return;
    
    setIsSyncing(true);
    try {
      // Calculate week start (Monday of current week)
      const now = new Date();
      const day = now.getDay();
      const diff = now.getDate() - day + (day === 0 ? -6 : 1); // Adjust to Monday
      const weekStart = new Date(now.setDate(diff));
      weekStart.setHours(0, 0, 0, 0);
      
      const utilizationPct = workload.weekly.triaged > 0
        ? Math.round((workload.weekly.completed / workload.weekly.triaged) * 100)
        : 0;
      
      await pushWorkloadWeeklyDigest({
        weekStart: weekStart.toISOString(),
        triaged: workload.weekly.triaged,
        completed: workload.weekly.completed,
        utilizationPct,
      });
      
      // Show success feedback
      alert("Synced to Notion successfully");
    } catch (error) {
      console.error("Failed to sync to Notion:", error);
      alert("Failed to sync to Notion. Check console for details.");
    } finally {
      setIsSyncing(false);
    }
  }, [workload, isSyncing]);
  
  if (isLoading && !workload) {
    return (
      <Panel>
        <Stack gap="md">
          <Heading as="h2" variant="title">
            Workload
          </Heading>
          <Text variant="muted">Loading workload data...</Text>
        </Stack>
      </Panel>
    );
  }
  
  if (!workload) {
    return (
      <Panel>
        <Stack gap="md">
          <Heading as="h2" variant="title">
            Workload
          </Heading>
          <Text variant="muted">Unable to load workload data</Text>
        </Stack>
      </Panel>
    );
  }
  
  return (
    <Panel>
      <Stack gap="md">
        <div className="flex justify-between items-center">
          <Heading as="h2" variant="title">
            Workload
          </Heading>
          
          {/* Quick actions */}
          <div className="flex items-center gap-2">
            {onAddFocusBlock && (
              <button
                onClick={onAddFocusBlock}
                className="text-xs text-sky-600 hover:text-sky-700 font-medium flex items-center gap-1"
                aria-label="Add focus block"
              >
                <Add24Regular className="w-4 h-4" />
                <span>Add focus block</span>
              </button>
            )}
            <button
              onClick={handleReviewQueue}
              className="text-xs text-slate-600 hover:text-slate-700 font-medium"
              aria-label="Review Action Queue"
            >
              Review Queue
            </button>
            <button
              onClick={handlePlanTomorrow}
              className="text-xs text-slate-600 hover:text-slate-700 font-medium"
              aria-label="Plan tomorrow"
            >
              Plan tomorrow
            </button>
            {notionSyncEnabled && (
              <button
                onClick={handleSyncToNotion}
                disabled={isSyncing}
                className="text-xs text-sky-600 hover:text-sky-700 font-medium flex items-center gap-1 disabled:opacity-50"
                aria-label="Sync to Notion"
              >
                <Sync24Regular className={`w-4 h-4 ${isSyncing ? "animate-spin" : ""}`} />
                <span>Sync to Notion</span>
              </button>
            )}
          </div>
        </div>
        
        {/* Progress bar */}
        <WorkloadProgress
          plannedMin={workload.plannedMin}
          activeMin={workload.activeMin}
          overrunMin={workload.overrunMin}
        />
        
        {/* Today's items */}
        <div className="space-y-2">
          <Text variant="caption" className="text-xs font-medium text-slate-600">
            Today&apos;s focus
          </Text>
          <WorkloadToday items={workload.today.items} />
        </div>
        
        {/* Weekly stats */}
        <div className="space-y-2">
          <Text variant="caption" className="text-xs font-medium text-slate-600">
            This week
          </Text>
          <WorkloadStats
            triaged={workload.weekly.triaged}
            completed={workload.weekly.completed}
          />
        </div>
        
        {/* Status badge */}
        <div className="pt-2 border-t border-slate-200">
          <WorkloadStatus rating={workload.rating} />
        </div>
      </Stack>
    </Panel>
  );
}

