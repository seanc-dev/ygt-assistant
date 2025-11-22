import { useCallback, useMemo } from "react";
import { useRouter } from "next/router";
import { Panel, Stack, Heading, Text, Badge } from "@lucid-work/ui";
import { Button } from "@lucid-work/ui/primitives/Button";
import { Star20Filled, Star20Regular } from "@fluentui/react-icons";
import type { Task } from "../../hooks/useWorkroomStore";
import { statusLabelMap } from "../../data/mockWorkroomData";
import { getPinnedTasks, toggleTaskPin } from "../../lib/hubSelectors";
import { useFocusContextStore } from "../../state/focusContextStore";

interface PrioritiesPanelProps {
  tasks: Task[];
  onTogglePin?: (taskId: string, next: boolean) => void;
}

export function PrioritiesPanel({ tasks, onTogglePin }: PrioritiesPanelProps) {
  const router = useRouter();
  const { pushFocus } = useFocusContextStore();
  const pinnedTasks = useMemo(() => getPinnedTasks(tasks), [tasks]);

  const handleToggle = useCallback(
    (task: Task) => {
      const next = !task.priority_pin;
      toggleTaskPin(task.id, next);
      onTogglePin?.(task.id, next);
    },
    [onTogglePin]
  );

  const openTask = useCallback(
    (task: Task) => {
      pushFocus({ type: "task", id: task.id }, { source: "hub" });
      router.push("/workroom");
    },
    [pushFocus, router]
  );

  return (
    <Panel>
      <Stack gap="md">
        <div className="flex items-center justify-between">
          <Heading as="h2" variant="title">
            Priorities
          </Heading>
          <Badge color="amber" variant="soft">
            {pinnedTasks.length} pinned
          </Badge>
        </div>
        {pinnedTasks.length === 0 ? (
          <Text variant="muted">No pinned tasks yet.</Text>
        ) : (
          <div className="flex flex-col gap-3" data-testid="priority-items">
            {pinnedTasks.map((task) => (
              <div
                key={task.id}
                className="flex items-center justify-between rounded-lg border border-slate-200 bg-white px-3 py-2"
              >
                <div className="flex flex-1 flex-col gap-1">
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => handleToggle(task)}
                      aria-label={task.priority_pin ? "Unpin task" : "Pin task"}
                      className="text-amber-500"
                    >
                      {task.priority_pin ? <Star20Filled /> : <Star20Regular />}
                    </button>
                    <Text variant="body" className="font-semibold">
                      {task.title}
                    </Text>
                  </div>
                  <div className="flex flex-wrap gap-2 text-xs text-slate-500">
                    <Badge color="gray" variant="soft">
                      {statusLabelMap[task.status] || task.status}
                    </Badge>
                    {task.microNote && <Badge color="blue" variant="outline">{task.microNote}</Badge>}
                  </div>
                </div>
                <Button size="xs" variant="ghost" onClick={() => openTask(task)}>
                  Open in Workroom
                </Button>
              </div>
            ))}
          </div>
        )}
      </Stack>
    </Panel>
  );
}
