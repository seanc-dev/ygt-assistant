import { useMemo, useState, useCallback } from "react";
import { useRouter } from "next/router";
import { Panel, Stack, Heading, Text, Badge } from "@lucid-work/ui";
import { Button } from "@lucid-work/ui/primitives/Button";
import { ChevronDown12Regular, ChevronRight12Regular, Star12Filled, Star12Regular } from "@fluentui/react-icons";
import type { Task } from "../../hooks/useWorkroomStore";
import { statusLabelMap } from "../../data/mockWorkroomData";
import { getMyWorkGrouped, toggleTaskPin, type MyWorkGroupKey } from "../../lib/hubSelectors";
import { useFocusContextStore } from "../../state/focusContextStore";

interface MyWorkSnapshotProps {
  tasks: Task[];
  onTogglePin?: (taskId: string, next: boolean) => void;
}

export function MyWorkSnapshot({ tasks, onTogglePin }: MyWorkSnapshotProps) {
  const router = useRouter();
  const { pushFocus } = useFocusContextStore();
  const [collapsed, setCollapsed] = useState<Record<MyWorkGroupKey, boolean>>({
    overdue: false,
    doing: false,
    ready: false,
    blocked: false,
  });

  const groups = useMemo(() => getMyWorkGrouped(tasks), [tasks]);

  const toggleCollapse = useCallback((key: MyWorkGroupKey) => {
    setCollapsed((prev) => ({ ...prev, [key]: !prev[key] }));
  }, []);

  const handleTogglePin = useCallback(
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
        <Heading as="h2" variant="title">
          My Work Snapshot
        </Heading>
        {groups.map((group) => (
          <div key={group.key} className="rounded-lg border border-slate-200 bg-white">
            <button
              type="button"
              onClick={() => toggleCollapse(group.key)}
              className="flex w-full items-center justify-between px-3 py-2 text-left"
            >
              <div className="flex items-center gap-2">
                {collapsed[group.key] ? <ChevronRight12Regular /> : <ChevronDown12Regular />}
                <Text variant="body" className="font-semibold">
                  {group.label}
                </Text>
                <Badge color="gray" variant="soft">
                  {group.tasks.length}
                </Badge>
              </div>
              <Text variant="muted" className="text-xs">
                {group.tasks.length === 0 ? "Nothing here" : "Tap to collapse"}
              </Text>
            </button>
            {!collapsed[group.key] && (
              <div className="flex flex-col divide-y divide-slate-100" data-testid={`group-${group.key}`}>
                {group.tasks.length === 0 ? (
                  <Text variant="muted" className="px-3 py-2 text-sm">
                    No items.
                  </Text>
                ) : (
                  group.tasks.map((task) => (
                    <div key={task.id} className="flex items-center justify-between px-3 py-2">
                      <div className="flex flex-col gap-1">
                        <div className="flex items-center gap-2">
                          <button
                            type="button"
                            onClick={() => handleTogglePin(task)}
                            aria-label={task.priority_pin ? "Unpin task" : "Pin task"}
                            className="text-amber-500"
                          >
                            {task.priority_pin ? <Star12Filled /> : <Star12Regular />}
                          </button>
                          <Text variant="body" className="font-semibold">
                            {task.title}
                          </Text>
                        </div>
                        <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500">
                          <Badge color="gray" variant="soft">
                            {statusLabelMap[task.status] || task.status}
                          </Badge>
                          {task.microNote && <Badge color="blue" variant="outline">{task.microNote}</Badge>}
                        </div>
                      </div>
                      <Button size="xs" variant="ghost" onClick={() => openTask(task)}>
                        Open
                      </Button>
                    </div>
                  ))
                )}
              </div>
            )}
          </div>
        ))}
      </Stack>
    </Panel>
  );
}
