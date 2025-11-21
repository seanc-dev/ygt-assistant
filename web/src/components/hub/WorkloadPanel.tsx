import { Panel, Stack, Heading } from "@lucid-work/ui";
import { useWorkloadSummary } from "../../hooks/useWorkloadSummary";
import { CapacityBar } from "./workload/CapacityBar";
import { ActiveFocus } from "./workload/ActiveFocus";
import { ActionFlow } from "./workload/ActionFlow";
import { WorkloadStatus } from "./workload/WorkloadStatus";
import { useRouter } from "next/router";
import { useCallback, useState, useRef } from "react";
import { formatRelativeTime } from "../../lib/workload";
import { CommandBarButton } from "../ui/CommandBarButton";
import { OverflowMenu, OverflowMenuItem } from "./OverflowMenu";
import {
  Add24Regular,
  Calendar24Regular,
  CalendarAdd24Regular,
  Box24Regular,
  Chat24Regular,
  Board24Regular,
  ClipboardTask24Regular,
  MoreHorizontal24Regular,
} from "@fluentui/react-icons";
import { useFocusContextStore } from "../../state/focusContextStore";

interface WorkloadPanelProps {
  onAddFocusBlock?: () => void;
}

/**
 * Workload Intelligence Panel - orchestrator component.
 * Semantic mirror of LucidWork with sections: Capacity, Active Focus, Action Flow, Summary.
 */
export function WorkloadPanel({ onAddFocusBlock }: WorkloadPanelProps) {
  const { data: workload, isLoading } = useWorkloadSummary();
  const router = useRouter();
  const [showOverflow, setShowOverflow] = useState(false);
  const overflowTriggerRef = useRef<HTMLButtonElement>(null);
  const { pushFocus } = useFocusContextStore();

  const handleReviewQueue = useCallback(() => {
    router.push("/hub#action-queue");
  }, [router]);

  const handlePlanTomorrow = useCallback(() => {
    router.push("/hub");
    // TODO: Open planning interface
  }, [router]);

  const handleOpenSchedule = useCallback(() => {
    router.push("/hub#schedule");
  }, [router]);

  const handleOpenQueueToday = useCallback(() => {
    router.push("/hub#action-queue?filter=today");
  }, [router]);

  const handleOpenWorkroom = useCallback(() => {
    pushFocus({ type: "portfolio", id: "my_work" }, { source: "hub_surface", surfaceKind: "workload" });
    router.push("/workroom");
  }, [pushFocus, router]);

  const handleOpenProjects = useCallback(() => {
    router.push("/projects");
  }, [router]);

  if (isLoading && !workload) {
    return (
      <Panel>
        <Stack gap="md">
          <Heading as="h2" variant="title">
            Workload
          </Heading>
          <p className="text-sm text-slate-500">Loading workload data...</p>
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
          <p className="text-sm text-slate-500">Unable to load workload data</p>
        </Stack>
      </Panel>
    );
  }

  return (
    <Panel>
      <Stack gap="md">
        {/* Header */}
        <div>
          <Heading as="h2" variant="title">
            Workload
          </Heading>

          {/* CommandBar - single quiet row */}
          <div className="flex flex-wrap items-center gap-1.5 text-sm text-slate-600 mt-1 mb-3">
            {/* Primary (only one subtle) */}
            {onAddFocusBlock && (
              <CommandBarButton
                size="xs"
                variant="subtle"
                onClick={onAddFocusBlock}
                aria-label="Add focus block"
              >
                <Add24Regular
                  className="h-3.5 w-3.5 md:h-4 md:w-4 text-slate-600"
                  aria-hidden="true"
                />
                <span>Add focus block</span>
              </CommandBarButton>
            )}

            {/* Divider dot */}
            <span className="mx-1 text-slate-300">•</span>

            {/* Ghost text links (no pills) */}
            <CommandBarButton
              size="xs"
              variant="ghost"
              onClick={handleReviewQueue}
              aria-label="Review Queue"
              className="hidden sm:inline-flex"
            >
              <Box24Regular
                className="h-3.5 w-3.5 md:h-4 md:w-4 text-slate-500"
                aria-hidden="true"
              />
              <span className="hidden sm:inline">Review Queue</span>
            </CommandBarButton>
            <span className="hidden sm:inline text-slate-300">•</span>
            <CommandBarButton
              size="xs"
              variant="ghost"
              onClick={handlePlanTomorrow}
              aria-label="Plan tomorrow"
              className="hidden sm:inline-flex"
            >
              <CalendarAdd24Regular
                className="h-3.5 w-3.5 md:h-4 md:w-4 text-slate-500"
                aria-hidden="true"
              />
              <span className="hidden sm:inline">Plan tomorrow</span>
            </CommandBarButton>

            <span className="hidden sm:inline mx-1 text-slate-300">•</span>

            {/* Navigation as ghost links */}
            <CommandBarButton
              size="xs"
              variant="ghost"
              onClick={handleOpenSchedule}
              aria-label="Open Schedule"
              className="hidden sm:inline-flex"
            >
              <Calendar24Regular
                className="h-3.5 w-3.5 md:h-4 md:w-4 text-slate-500"
                aria-hidden="true"
              />
              <span className="hidden md:inline">Schedule</span>
            </CommandBarButton>
            <span className="hidden sm:inline text-slate-300">•</span>
            <CommandBarButton
              size="xs"
              variant="ghost"
              onClick={handleOpenQueueToday}
              aria-label="Open Action Queue (Today)"
              className="hidden sm:inline-flex"
            >
              <ClipboardTask24Regular
                className="h-3.5 w-3.5 md:h-4 md:w-4 text-slate-500"
                aria-hidden="true"
              />
              <span className="hidden md:inline">Action Queue (Today)</span>
            </CommandBarButton>
            <span className="hidden sm:inline text-slate-300">•</span>
            <CommandBarButton
              size="xs"
              variant="ghost"
              onClick={handleOpenWorkroom}
              aria-label="Open Workroom"
              className="hidden sm:inline-flex"
            >
              <Chat24Regular
                className="h-3.5 w-3.5 md:h-4 md:w-4 text-slate-500"
                aria-hidden="true"
              />
              <span className="hidden md:inline">Workroom</span>
            </CommandBarButton>
            <span className="hidden sm:inline text-slate-300">•</span>
            <CommandBarButton
              size="xs"
              variant="ghost"
              onClick={handleOpenProjects}
              aria-label="Open Projects/Kanban"
              className="hidden sm:inline-flex"
            >
              <Board24Regular
                className="h-3.5 w-3.5 md:h-4 md:w-4 text-slate-500"
                aria-hidden="true"
              />
              <span className="hidden md:inline">Projects</span>
            </CommandBarButton>

            {/* Overflow on xs screens */}
            <div className="sm:hidden">
              <button
                ref={overflowTriggerRef}
                onClick={() => setShowOverflow(!showOverflow)}
                className="inline-flex h-7 w-7 items-center justify-center rounded-md hover:bg-slate-100 focus-visible:ring-2 focus-visible:ring-sky-300"
                aria-label="More"
                aria-expanded={showOverflow}
              >
                <MoreHorizontal24Regular
                  className="h-4 w-4 text-slate-600"
                  aria-hidden="true"
                />
              </button>
              <OverflowMenu
                open={showOverflow}
                onClose={() => setShowOverflow(false)}
                triggerRef={overflowTriggerRef as React.RefObject<HTMLElement>}
              >
                <OverflowMenuItem
                  onClick={() => {
                    handleReviewQueue();
                    setShowOverflow(false);
                  }}
                >
                  Review Queue
                </OverflowMenuItem>
                <OverflowMenuItem
                  onClick={() => {
                    handlePlanTomorrow();
                    setShowOverflow(false);
                  }}
                >
                  Plan tomorrow
                </OverflowMenuItem>
                <OverflowMenuItem
                  onClick={() => {
                    handleOpenSchedule();
                    setShowOverflow(false);
                  }}
                >
                  Schedule
                </OverflowMenuItem>
                <OverflowMenuItem
                  onClick={() => {
                    handleOpenQueueToday();
                    setShowOverflow(false);
                  }}
                >
                  Action Queue (Today)
                </OverflowMenuItem>
                <OverflowMenuItem
                  onClick={() => {
                    handleOpenWorkroom();
                    setShowOverflow(false);
                  }}
                >
                  Workroom
                </OverflowMenuItem>
                <OverflowMenuItem
                  onClick={() => {
                    handleOpenProjects();
                    setShowOverflow(false);
                  }}
                >
                  Projects
                </OverflowMenuItem>
              </OverflowMenu>
            </div>
          </div>
        </div>

        {/* Today's Capacity */}
        <div className="space-y-2">
          <p className="text-sm text-slate-600 font-medium">Capacity today</p>
          <CapacityBar
            capacityMin={workload.capacityMin}
            plannedMin={workload.plannedMin}
            focusedMin={workload.focusedMin}
            overbookedMin={workload.overbookedMin}
          />
        </div>

        {/* Active Focus */}
        <div className="space-y-2">
          <p className="text-sm text-slate-600 font-medium">
            Active focus ({workload.today.focus.length})
          </p>
          <ActiveFocus items={workload.today.focus} />
        </div>

        {/* Action Flow */}
        <div className="space-y-2">
          <p className="text-sm text-slate-600 font-medium">Action flow</p>
          <ActionFlow flowWeek={workload.flowWeek} />
        </div>

        {/* Summary */}
        <div className="pt-2 border-t border-slate-200 space-y-1">
          <WorkloadStatus rating={workload.rating} />
          {workload.lastSyncIso && (
            <p className="text-xs text-slate-500">
              Last sync {formatRelativeTime(workload.lastSyncIso)}
            </p>
          )}
        </div>
      </Stack>
    </Panel>
  );
}
