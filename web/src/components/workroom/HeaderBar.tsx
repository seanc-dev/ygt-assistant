import { Button } from "@lucid-work/ui/primitives/Button";
import { Text } from "@lucid-work/ui";
import {
  Add24Regular,
  Filter24Regular,
  Settings24Regular,
  Attach24Regular,
  Calendar24Regular,
} from "@fluentui/react-icons";
import type { Level, TaskStatus, Project, Task, PrimaryView } from "../../hooks/useWorkroomStore";
import { ViewSwitcher } from "./ViewSwitcher";

interface HeaderBarProps {
  primaryView: PrimaryView;
  level: Level;
  project?: Project | null;
  task?: Task | null;
  status?: TaskStatus;
  onPrimaryViewChange: (view: PrimaryView) => void;
  onAddTask?: () => void;
  onFilter?: () => void;
  onProjectSettings?: () => void;
  onAttachSource?: () => void;
  onAddFocusBlock?: () => void;
  onStatusChange?: (status: TaskStatus) => void;
}

export function HeaderBar({
  primaryView,
  level,
  project,
  task,
  status,
  onPrimaryViewChange,
  onAddTask,
  onFilter,
  onProjectSettings,
  onAttachSource,
  onAddFocusBlock,
  onStatusChange,
}: HeaderBarProps) {
  return (
    <div className="flex items-center justify-between px-4 py-3 border-b border-slate-200 bg-white">
      {/* Left: ViewSwitcher */}
      <div className="flex items-center gap-3">
        <ViewSwitcher value={primaryView} onChange={onPrimaryViewChange} />
      </div>

      {/* Right: Contextual toolbar */}
      <div className="flex items-center gap-2">
        {primaryView === "kanban" ? (
          <>
            <Button variant="ghost" size="sm" onClick={onAddTask}>
              <Add24Regular className="w-4 h-4 mr-1" />
              Add task
            </Button>
            <Button variant="ghost" size="sm" onClick={onFilter}>
              <Filter24Regular className="w-4 h-4 mr-1" />
              Filter
            </Button>
            {level === "project" && (
              <Button variant="ghost" size="sm" onClick={onProjectSettings}>
                <Settings24Regular className="w-4 h-4 mr-1" />
                Project settings
              </Button>
            )}
          </>
        ) : (
          <>
            {level === "task" && (
              <>
                <Button variant="ghost" size="sm" onClick={onAttachSource}>
                  <Attach24Regular className="w-4 h-4 mr-1" />
                  Attach source
                </Button>
                <Button variant="ghost" size="sm" onClick={onAddFocusBlock}>
                  <Calendar24Regular className="w-4 h-4 mr-1" />
                  Add focus block
                </Button>
                {status && onStatusChange && (
                  <select
                    value={status}
                    onChange={(e) => onStatusChange(e.target.value as TaskStatus)}
                    className="text-xs border border-slate-200 rounded px-2 py-1 bg-white hover:bg-slate-50 h-7"
                  >
                    <option value="backlog">Backlog</option>
                    <option value="ready">Ready</option>
                    <option value="doing">Doing</option>
                    <option value="blocked">Blocked</option>
                    <option value="done">Done</option>
                  </select>
                )}
              </>
            )}
          </>
        )}
      </div>
    </div>
  );
}


