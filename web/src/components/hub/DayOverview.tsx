import { useMemo } from "react";
import { useRouter } from "next/router";
import { Panel, Stack, Heading, Text, Badge } from "@lucid-work/ui";
import { Button } from "@lucid-work/ui/primitives/Button";
import { AssistantChat } from "./AssistantChat";
import { getInboxDigest, getMyWorkGrouped, getPinnedTasks, getTodayEvents } from "../../lib/hubSelectors";
import type { Task } from "../../hooks/useWorkroomStore";
import { useFocusContextStore } from "../../state/focusContextStore";

interface DayOverviewProps {
  tasks: Task[];
}

export function DayOverview({ tasks }: DayOverviewProps) {
  const router = useRouter();
  const { pushFocus } = useFocusContextStore();

  const pinnedTasks = useMemo(() => getPinnedTasks(tasks), [tasks]);
  const groups = useMemo(() => getMyWorkGrouped(tasks), [tasks]);
  const overdueCount = groups.find((group) => group.key === "overdue")?.tasks.length ?? 0;
  const events = useMemo(() => getTodayEvents(), []);
  const inboxGroups = useMemo(() => getInboxDigest(), []);
  const inboxTotal = inboxGroups.reduce((acc, group) => acc + group.items.length, 0);

  const handleOpenToday = () => {
    pushFocus({ type: "today" }, { source: "hub" });
    router.push("/workroom");
  };

  const summary = `Pinned: ${pinnedTasks.length} • Overdue: ${overdueCount} • Events: ${events.length} • Inbox: ${inboxTotal}`;

  return (
    <Panel>
      <Stack gap="md">
        <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
          <div className="flex flex-col gap-1">
            <Heading as="h2" variant="title">
              Day Overview
            </Heading>
            <Text variant="muted">LLM-guided orientation into Workroom.</Text>
            <div className="flex flex-wrap gap-2 text-xs text-slate-500" aria-label="day-overview-stats">
              <Badge color="blue" variant="soft">
                {pinnedTasks.length} pinned
              </Badge>
              <Badge color={overdueCount > 0 ? "red" : "gray"} variant="soft">
                {overdueCount} overdue
              </Badge>
              <Badge color="indigo" variant="soft">
                {events.length} events
              </Badge>
              <Badge color="purple" variant="soft">
                {inboxTotal} inbox
              </Badge>
            </div>
          </div>
          <Button size="sm" onClick={handleOpenToday} data-testid="open-today-cta">
            Open Today in Workroom
          </Button>
        </div>

        <div className="rounded-lg border border-slate-200 bg-white">
          <AssistantChat
            actionId="hub-day-overview"
            mode="hub_orientation"
            summary={summary}
            surfaceRenderAllowed
          />
        </div>
      </Stack>
    </Panel>
  );
}
