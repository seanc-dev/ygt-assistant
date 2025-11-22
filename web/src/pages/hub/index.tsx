import { useCallback, useState } from "react";
import { Layout } from "../../components/Layout";
import { DayOverview } from "../../components/hub/DayOverview";
import { PrioritiesPanel } from "../../components/hub/PrioritiesPanel";
import { MyWorkSnapshot } from "../../components/hub/MyWorkSnapshot";
import { InboxDigest } from "../../components/hub/InboxDigest";
import { getMockTasks } from "../../data/mockWorkroomData";
import type { Task } from "../../hooks/useWorkroomStore";

export default function HubPage() {
  const [tasks, setTasks] = useState<Task[]>(getMockTasks());

  const handlePinChange = useCallback((taskId: string, next: boolean) => {
    setTasks((prev) =>
      prev.map((task) =>
        task.id === taskId
          ? {
              ...task,
              priority_pin: next,
            }
          : task
      )
    );
  }, []);

  return (
    <Layout variant="tight">
      <div className="mx-auto flex w-full max-w-3xl flex-col gap-4 pb-8">
        <DayOverview tasks={tasks} />
        <PrioritiesPanel tasks={tasks} onTogglePin={handlePinChange} />
        <MyWorkSnapshot tasks={tasks} onTogglePin={handlePinChange} />
        <InboxDigest />
      </div>
    </Layout>
  );
}
