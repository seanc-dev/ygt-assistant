import { useEffect } from "react";
import { useRouter } from "next/router";
import { Layout } from "../../components/Layout";
import { WorkroomAnchorBar } from "../../components/workroom/WorkroomAnchorBar";
import { WorkCanvas } from "../../components/workroom/WorkCanvas";
import { FocusStackRail } from "../../components/workroom/FocusStackRail";
import { ContextTabs } from "../../components/workroom/ContextTabs";
import { NeighborhoodPanel } from "../../components/workroom/NeighborhoodPanel";
import { ContextPanel } from "../../components/ContextPanel";
import { DocsPanel } from "../../components/workroom/DocsPanel";
import { useFocusContextStore } from "../../state/focusContextStore";

export default function WorkroomPage() {
  const router = useRouter();
  const { current, pushFocus, setFocusContext } = useFocusContextStore();
  const { projectId, taskId } = router.query;

  useEffect(() => {
    // Only initialize focus if there's no current focus
    if (!current) {
      // Check for deep-link query parameters
      const projectIdStr = typeof projectId === "string" ? projectId : undefined;
      const taskIdStr = typeof taskId === "string" ? taskId : undefined;

      if (taskIdStr) {
        // Deep link to a specific task (projectId may be provided but focus only needs taskId)
        pushFocus({ type: "task", id: taskIdStr }, { source: "direct" });
      } else if (projectIdStr) {
        // Deep link to a specific project
        pushFocus({ type: "project", id: projectIdStr }, { source: "direct" });
      } else {
        // Default to portfolio if no query params
        setFocusContext(
          {
            anchor: { type: "portfolio", id: "my_work" },
            mode: "plan",
            origin: { source: "direct" },
          },
          { pushToStack: false }
        );
      }
    }
  }, [current, projectId, taskId, pushFocus, setFocusContext]);

  return (
    <Layout>
      <div className="flex h-full flex-col gap-4">
        <WorkroomAnchorBar />
        <div className="grid flex-1 grid-cols-1 gap-4 lg:grid-cols-[220px,minmax(0,1fr),320px]">
          <div className="hidden lg:block">
            <FocusStackRail />
          </div>
          <div className="min-h-[600px] rounded-lg border border-slate-200 bg-white shadow-sm">
            <WorkCanvas />
          </div>
          <div className="hidden lg:block">
            <ContextTabs
              neighborhood={<NeighborhoodPanel />}
              context={<ContextPanel />}
              docs={<DocsPanel />}
            />
          </div>
        </div>
      </div>
    </Layout>
  );
}
