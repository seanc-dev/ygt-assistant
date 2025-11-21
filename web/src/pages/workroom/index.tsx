import { useEffect } from "react";
import { Layout } from "../../components/Layout";
import { WorkroomAnchorBar } from "../../components/workroom/WorkroomAnchorBar";
import { WorkCanvas } from "../../components/workroom/WorkCanvas";
import { FocusStackRail } from "../../components/workroom/FocusStackRail";
import { NeighborhoodRail } from "../../components/workroom/NeighborhoodRail";
import { useFocusContextStore } from "../../state/focusContextStore";

export default function WorkroomPage() {
  const { current, setFocusContext } = useFocusContextStore();

  useEffect(() => {
    if (!current) {
      setFocusContext(
        {
          anchor: { type: "portfolio", id: "my_work" },
          mode: "plan",
          origin: { source: "direct" },
        },
        { pushToStack: false }
      );
    }
  }, [current, setFocusContext]);

  return (
    <Layout>
      <div className="flex h-full flex-col gap-4">
        <WorkroomAnchorBar />
        <div className="grid flex-1 grid-cols-1 gap-4 lg:grid-cols-[220px,1fr,260px]">
          <div className="hidden lg:block">
            <FocusStackRail />
          </div>
          <div className="min-h-[600px] rounded-lg border border-slate-200 bg-white shadow-sm">
            <WorkCanvas />
          </div>
          <div className="hidden lg:block">
            <NeighborhoodRail />
          </div>
        </div>
      </div>
    </Layout>
  );
}
