import { useEffect, useRef, useState } from "react";
import type { ProjectOption, TaskOption, TaskSuggestion } from "./types";

export type ReferenceSearchPanelProps = {
  anchorRef:
    | React.RefObject<HTMLDivElement>
    | React.MutableRefObject<HTMLDivElement | null>;
  query: string;
  onQueryChange: (value: string) => void;
  projectOptions: ProjectOption[];
  projectId: string | null;
  onProjectChange: (value: string | null) => void;
  results: TaskSuggestion[];
  loading: boolean;
  onSelect: (task: TaskOption) => void;
  onClose: () => void;
  activeIndex: number;
  onActiveIndexChange: (index: number) => void;
};

export function ReferenceSearchPanel({
  anchorRef,
  query,
  onQueryChange,
  projectOptions,
  projectId,
  onProjectChange,
  results,
  loading,
  onSelect,
  onClose,
  activeIndex,
  onActiveIndexChange,
}: ReferenceSearchPanelProps) {
  const panelRef = useRef<HTMLDivElement | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [position, setPosition] = useState({
    left: 0,
    bottom: 0,
    width: 0,
  });

  useEffect(() => {
    const updatePosition = () => {
      if (!anchorRef.current) return;
      const rect = anchorRef.current.getBoundingClientRect();
      setPosition({
        left: rect.left,
        bottom: window.innerHeight - rect.top + 12,
        width: rect.width,
      });
    };
    updatePosition();
    window.addEventListener("resize", updatePosition);
    return () => window.removeEventListener("resize", updatePosition);
  }, [anchorRef]);

  useEffect(() => {
    const handleClick = (event: MouseEvent) => {
      if (
        panelRef.current &&
        !panelRef.current.contains(event.target as Node)
      ) {
        onClose();
      }
    };
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [onClose]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      onActiveIndexChange(
        Math.min(activeIndex + 1, Math.max(results.length - 1, 0))
      );
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      onActiveIndexChange(Math.max(activeIndex - 1, 0));
    } else if (event.key === "Enter") {
      event.preventDefault();
      const task = results[activeIndex];
      if (task) {
        onSelect(task);
      }
    } else if (event.key === "Escape") {
      event.preventDefault();
      onClose();
    }
  };

  const hasProjects = projectOptions.length > 0;

  return (
    <div
      className="fixed z-40"
      style={{
        left: position.left,
        bottom: position.bottom,
        width: position.width || "100%",
      }}
    >
      <div
        ref={panelRef}
        className="rounded-2xl border border-slate-200 bg-slate-950/95 text-white shadow-2xl backdrop-blur-md p-3"
      >
        <div className="flex items-center gap-2 mb-3">
          <input
            ref={inputRef}
            value={query}
            onChange={(e) => onQueryChange(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Search tasks…"
            className="flex-1 bg-transparent text-white placeholder:text-slate-400 text-sm focus:outline-none"
          />
          {hasProjects && (
            <select
              value={projectId || ""}
              onChange={(e) => onProjectChange(e.target.value || null)}
              className="text-xs bg-slate-800 rounded-lg px-2 py-1 text-slate-200 focus:outline-none"
            >
              <option value="">All projects</option>
              {projectOptions.map((project) => (
                <option key={project.id} value={project.id}>
                  {project.title}
                </option>
              ))}
            </select>
          )}
        </div>
        <div className="max-h-72 overflow-y-auto">
          {loading && (
            <div className="px-3 py-2 text-sm text-slate-400">Searching…</div>
          )}
          {!loading && results.length === 0 && (
            <div className="px-3 py-2 text-sm text-slate-400">
              {query ? "No matches yet. Keep typing." : "Start typing to search tasks."}
            </div>
          )}
          {results.map((task, index) => {
            const isActive = index === activeIndex;
            return (
              <button
                key={`${task.id}-${task.meta || "result"}`}
                onClick={() => onSelect(task)}
                onMouseEnter={() => onActiveIndexChange(index)}
                className={`w-full text-left px-3 py-2 rounded-lg transition-colors ${
                  isActive ? "bg-slate-800" : "hover:bg-slate-900"
                }`}
              >
                <div className="text-sm font-medium text-white">
                  {task.title}
                </div>
                <div className="text-xs text-slate-400 flex items-center justify-between">
                  <span>{task.projectTitle || "No project"}</span>
                  {task.meta && <span>{task.meta}</span>}
                </div>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}

