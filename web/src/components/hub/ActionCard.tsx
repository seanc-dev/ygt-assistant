import {
  useState,
  useRef,
  useEffect,
  useLayoutEffect,
  useCallback,
} from "react";
import { useRouter } from "next/router";
import {
  Chat24Regular,
  ArrowRight24Regular,
  Pin24Regular,
  Add24Regular,
  Clock24Regular,
  MoreHorizontal24Regular,
} from "@fluentui/react-icons";
import { AssistantChat } from "./AssistantChat";

type ActionCardProps = {
  item: {
    action_id: string;
    source: "email" | "teams" | "doc";
    priority: "high" | "medium" | "low";
    preview: string;
    action_label: "Respond" | "Approve" | "Review";
    thread_id?: string;
    task_id?: string | null;
    task_title?: string | null;
  };
  onToggleExpand: (id: string) => void;
  expanded: boolean;
  selected?: boolean;
  trustMode?: "training_wheels" | "supervised" | "autonomous";
  onDefer: (
    id: string,
    bucket: "afternoon" | "tomorrow" | "this_week" | "next_week"
  ) => Promise<void>;
  onAddToToday: (id: string) => Promise<void>;
  onCreateTask: (id: string) => Promise<void>;
  onSchedule: (
    id: string,
    bucket: "afternoon" | "tomorrow" | "this_week" | "next_week"
  ) => Promise<void>;
  onOpenSchedule?: (id: string) => void;
  cardRef?: React.RefObject<HTMLDivElement | null>;
};

type MenuType =
  | "defer-collapsed"
  | "defer-expanded"
  | "schedule"
  | "add-to-today"
  | "overflow"
  | null;

const SOURCE_COLORS = {
  email: "bg-blue-500",
  teams: "bg-purple-500",
  doc: "bg-teal-500",
} as const;

const PRIORITY_STYLES = {
  high: "bg-rose-100 text-rose-700",
  medium: "bg-amber-100 text-amber-700",
  low: "bg-slate-100 text-slate-600",
} as const;

const PRIORITY_LABELS = {
  high: "High",
  medium: "Medium",
  low: "Low",
} as const;

export function ActionCard({
  item,
  expanded,
  selected = false,
  onToggleExpand,
  onDefer,
  onAddToToday,
  onCreateTask,
  onSchedule,
  onOpenSchedule,
  cardRef,
  trustMode = "training_wheels",
}: ActionCardProps) {
  const router = useRouter();
  const [openMenu, setOpenMenu] = useState<MenuType>(null);
  const [threadId, setThreadId] = useState<string | null>(
    item.thread_id || null
  );
  const deferMenuRefCollapsed = useRef<HTMLDivElement>(null);
  const deferMenuRefExpanded = useRef<HTMLDivElement>(null);
  const scheduleMenuRefCollapsed = useRef<HTMLDivElement>(null);
  const scheduleMenuRefExpanded = useRef<HTMLDivElement>(null);
  const addToTodayMenuRef = useRef<HTMLDivElement>(null);
  const overflowMenuRef = useRef<HTMLDivElement>(null);

  // Sync thread_id from item prop
  useEffect(() => {
    if (item.thread_id) {
      setThreadId(item.thread_id);
    }
  }, [item.thread_id]);

  // Close menus when card expands/collapses
  useEffect(() => {
    // When card state changes, close menus that shouldn't be visible
    if (openMenu) {
      if (
        (openMenu === "defer-collapsed" && expanded) ||
        (openMenu === "defer-expanded" && !expanded)
      ) {
        setOpenMenu(null);
      }
    }
  }, [expanded, openMenu, item.action_id]);

  // Handle keyboard events
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        if (openMenu) {
          setOpenMenu(null);
          return;
        }
        if (expanded) {
          onToggleExpand(item.action_id);
        }
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [expanded, openMenu, item.action_id, onToggleExpand]);

  // Close menus when clicking outside - using useLayoutEffect for synchronous DOM updates
  useLayoutEffect(() => {
    if (!openMenu) return;

    const handleClickOutside = (e: MouseEvent) => {
      const target = e.target as Node;
      const targetElement = target as HTMLElement;

      // Get the appropriate menu ref based on open menu type
      let menuRef: HTMLDivElement | null = null;
      if (openMenu === "defer-collapsed") {
        menuRef = deferMenuRefCollapsed.current;
      } else if (openMenu === "defer-expanded") {
        menuRef = deferMenuRefExpanded.current;
      } else if (openMenu === "schedule") {
        // Determine which schedule menu ref to use based on expanded state
        menuRef = expanded
          ? scheduleMenuRefExpanded.current
          : scheduleMenuRefCollapsed.current;
      } else if (openMenu === "add-to-today") {
        menuRef = addToTodayMenuRef.current;
      } else if (openMenu === "overflow") {
        menuRef = overflowMenuRef.current;
      }

      // Check if click is inside the menu
      const isInsideMenu = menuRef && menuRef.contains(target);

      // Check if click is on a trigger button
      const isTriggerButton = targetElement.closest("[data-menu-trigger]");

      // Close menu if click is outside and not on a trigger button
      if (!isInsideMenu && !isTriggerButton) {
        setOpenMenu(null);
      }
    };

    // Attach handler immediately (no delay)
    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [openMenu, item.action_id]);

  const handleCardClick = useCallback(
    (e: React.MouseEvent) => {
      // Ignore clicks on menu triggers and interactive elements
      const target = e.target as HTMLElement;
      if (
        target.closest("[data-menu-trigger]") ||
        target.closest("button") ||
        target.closest("textarea") ||
        target.closest("a")
      ) {
        return;
      }
      // Card click opens chat
      onToggleExpand(item.action_id);
    },
    [item.action_id, onToggleExpand]
  );

  const handleKeyDown = (e: React.KeyboardEvent) => {
    // Ignore if typing in input/textarea or contenteditable
    const target = e.target as HTMLElement;
    if (
      target.tagName === "INPUT" ||
      target.tagName === "TEXTAREA" ||
      target.isContentEditable
    ) {
      return;
    }

    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      onToggleExpand(item.action_id);
    }

    // Tab key cycles through action menus when expanded
    if (e.key === "Tab" && expanded && !e.shiftKey) {
      e.preventDefault();
      const menuOrder: MenuType[] = [
        "defer-expanded",
        "schedule",
        "add-to-today",
      ];
      const currentIndex = openMenu ? menuOrder.indexOf(openMenu) : -1;
      const nextIndex = (currentIndex + 1) % menuOrder.length;
      setOpenMenu(menuOrder[nextIndex]);
    } else if (e.key === "Tab" && expanded && e.shiftKey) {
      e.preventDefault();
      const menuOrder: MenuType[] = [
        "defer-expanded",
        "schedule",
        "add-to-today",
      ];
      const currentIndex = openMenu ? menuOrder.indexOf(openMenu) : -1;
      const prevIndex =
        currentIndex <= 0 ? menuOrder.length - 1 : currentIndex - 1;
      setOpenMenu(menuOrder[prevIndex]);
    }
  };

  const handleDeferClick = useCallback(
    async (bucket: "afternoon" | "tomorrow" | "this_week" | "next_week") => {
      await onDefer(item.action_id, bucket);
      setOpenMenu(null);
    },
    [item.action_id, onDefer]
  );

  const handleScheduleClick = useCallback(
    async (bucket: "afternoon" | "tomorrow" | "this_week" | "next_week") => {
      await onSchedule(item.action_id, bucket);
      setOpenMenu(null);
    },
    [item.action_id, onSchedule]
  );

  const handleAddToTodayScheduleClick = useCallback(
    async (
      preset: "focus_30m" | "focus_60m" | "block_pm_admin" | "pick_time"
    ) => {
      // Call both handlers: add to today and schedule with the selected preset
      await onAddToToday(item.action_id);
      await onSchedule(item.action_id, preset);
      setOpenMenu(null);
    },
    [item.action_id, onAddToToday, onSchedule]
  );

  const handleToggleAddToToday = useCallback(
    (e: React.MouseEvent) => {
      e.stopPropagation();
      setOpenMenu(openMenu === "add-to-today" ? null : "add-to-today");
    },
    [openMenu, item.action_id]
  );

  const handleCreateTaskClick = useCallback(async () => {
    await onCreateTask(item.action_id);
    setOpenMenu(null);
  }, [item.action_id, onCreateTask]);

  const handleScheduleFromOverflowClick = useCallback(async () => {
    setOpenMenu(null);
    // Expand card if needed, then open schedule menu
    if (!expanded) {
      onToggleExpand(item.action_id);
      // Wait for expansion, then open schedule menu
      setTimeout(() => {
        setOpenMenu("schedule");
        // Also trigger onOpenSchedule if provided
        onOpenSchedule?.(item.action_id);
      }, 100);
    } else {
      setOpenMenu("schedule");
      onOpenSchedule?.(item.action_id);
    }
  }, [expanded, item.action_id, onToggleExpand, onOpenSchedule]);

  // Menu toggle handlers
  const handleToggleDeferCollapsed = useCallback(
    (e: React.MouseEvent) => {
      e.stopPropagation();
      setOpenMenu(openMenu === "defer-collapsed" ? null : "defer-collapsed");
    },
    [openMenu, item.action_id]
  );

  const handleToggleDeferExpanded = useCallback(
    (e: React.MouseEvent) => {
      e.stopPropagation();
      setOpenMenu(openMenu === "defer-expanded" ? null : "defer-expanded");
    },
    [openMenu, item.action_id]
  );

  const handleToggleSchedule = useCallback(
    (e: React.MouseEvent) => {
      e.stopPropagation();
      setOpenMenu(openMenu === "schedule" ? null : "schedule");
    },
    [openMenu, item.action_id]
  );

  const handleToggleOverflow = useCallback(
    (e: React.MouseEvent) => {
      e.stopPropagation();
      setOpenMenu(openMenu === "overflow" ? null : "overflow");
    },
    [openMenu, item.action_id]
  );

  const handleOpenInWorkroom = useCallback(
    (threadId?: string) => {
      if (threadId) {
        router.push(`/workroom?thread=${threadId}`);
      } else {
        router.push("/workroom");
      }
    },
    [router]
  );

  const handleThreadCreated = useCallback((newThreadId: string) => {
    setThreadId(newThreadId);
    // TODO: Update the item's thread_id in the parent component/queue
    // This would typically be done via a callback prop or state management
  }, []);

  const sourceColor = SOURCE_COLORS[item.source];
  const priorityStyle = PRIORITY_STYLES[item.priority];
  const priorityLabel = PRIORITY_LABELS[item.priority];

  return (
    <div
      ref={cardRef}
      role="option"
      tabIndex={selected ? 0 : -1}
      aria-selected={selected}
      aria-expanded={expanded}
      aria-label={`${item.action_label}: ${item.preview.substring(0, 50)}`}
      onClick={handleCardClick}
      onMouseDown={(e) => {
        // Prevent card click on menu triggers
        const target = e.target as HTMLElement;
        if (target.closest("[data-menu-trigger]")) {
          e.stopPropagation();
        }
      }}
      onKeyDown={handleKeyDown}
      data-selected={selected}
      className={`group bg-slate-50 border border-slate-200 rounded-xl shadow-sm transition-all duration-200 ease-in-out focus:outline-none cursor-pointer ${
        selected
          ? "outline outline-2 outline-blue-500/60 outline-offset-2"
          : "focus:ring-2 focus:ring-slate-300 focus:ring-offset-2"
      } ${
        expanded
          ? "shadow-md ring-1 ring-slate-200 hover:shadow-lg"
          : "hover:shadow-md hover:-translate-y-0.5"
      }`}
    >
      {/* Card body */}
      <div className="flex gap-4 p-4">
        {/* Left accent bar */}
        <div
          className={`w-1 rounded-l-xl ${sourceColor} self-stretch flex-shrink-0`}
        />

        {/* Main content */}
        <div className="flex-1 min-w-0">
          {/* Header row */}
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs tracking-wide uppercase text-slate-500 font-medium">
              {item.source}
            </span>
            <span
              className={`text-xs px-2.5 py-0.5 rounded-full font-medium ${priorityStyle}`}
              aria-label={`Priority: ${item.priority}`}
            >
              {priorityLabel}
            </span>
          </div>

          {/* Title */}
          <h3 className="text-base font-semibold text-slate-900 mb-1 line-clamp-2">
            {item.preview}
          </h3>

          {/* Subtext */}
          <p
            className={`text-sm text-slate-500 transition-all duration-200 ${
              expanded ? "mb-0" : "mb-3"
            }`}
          >
            {item.action_label}
          </p>

          {/* Hover hint - left-aligned with text content, transitions with quick actions */}
          {!expanded && (
            <span className="text-xs text-slate-400 opacity-0 group-hover:opacity-100 focus-within:opacity-100 transition-opacity duration-200 pointer-events-none hidden md:block mt-0.5">
              Open chat ↩︎
            </span>
          )}
          {expanded && (
            <span className="text-xs text-slate-400 opacity-0 group-hover:opacity-100 focus-within:opacity-100 transition-opacity duration-200 pointer-events-none hidden md:block mt-0.5">
              Close chat ↩︎
            </span>
          )}

          {/* Collapsed toolbar - Defer, Schedule, Add to Today, Overflow */}
          <div
            className={`transition-all duration-200 flex items-center gap-2 justify-end relative ${
              expanded
                ? "opacity-0 max-h-0 overflow-hidden mt-0 pointer-events-none"
                : "opacity-0 group-hover:opacity-100 focus-within:opacity-100 mt-2"
            }`}
          >
            <div className="relative">
              <button
                data-menu-trigger
                data-defer-button
                onClick={handleToggleDeferCollapsed}
                onMouseDown={(e) => e.stopPropagation()}
                aria-label="Defer"
                className="text-slate-500 hover:text-slate-700 transition-colors duration-150 focus:outline-none focus:ring-2 focus:ring-slate-300 rounded-md p-1.5"
                title="Defer"
              >
                <ArrowRight24Regular />
              </button>
              {!expanded && openMenu === "defer-collapsed" && (
                <div
                  key="defer-collapsed"
                  ref={deferMenuRefCollapsed}
                  className="absolute right-0 top-full mt-2 w-48 rounded-lg bg-white shadow-lg ring-1 ring-black/5 z-20"
                  onClick={(e) => e.stopPropagation()}
                  onMouseDown={(e) => e.stopPropagation()}
                >
                  <button
                    onClick={() => handleDeferClick("afternoon")}
                    onMouseDown={(e) => e.stopPropagation()}
                    className="w-full text-left px-3 py-2 text-sm text-slate-700 hover:bg-slate-50 rounded-md focus:outline-none focus:bg-slate-50"
                  >
                    Afternoon
                  </button>
                  <button
                    onClick={() => handleDeferClick("tomorrow")}
                    onMouseDown={(e) => e.stopPropagation()}
                    className="w-full text-left px-3 py-2 text-sm text-slate-700 hover:bg-slate-50 rounded-md focus:outline-none focus:bg-slate-50"
                  >
                    Tomorrow
                  </button>
                  <button
                    onClick={() => handleDeferClick("this_week")}
                    onMouseDown={(e) => e.stopPropagation()}
                    className="w-full text-left px-3 py-2 text-sm text-slate-700 hover:bg-slate-50 rounded-md focus:outline-none focus:bg-slate-50"
                  >
                    This Week
                  </button>
                  <button
                    onClick={() => handleDeferClick("next_week")}
                    onMouseDown={(e) => e.stopPropagation()}
                    className="w-full text-left px-3 py-2 text-sm text-slate-700 hover:bg-slate-50 rounded-md focus:outline-none focus:bg-slate-50"
                  >
                    Next Week
                  </button>
                </div>
              )}
            </div>
            {!expanded && (
              <div className="relative">
                <button
                  data-menu-trigger
                  data-schedule-button
                  onClick={(e) => {
                    e.stopPropagation();
                    setOpenMenu(openMenu === "schedule" ? null : "schedule");
                  }}
                  onMouseDown={(e) => e.stopPropagation()}
                  aria-label="Schedule"
                  className="text-slate-500 hover:text-slate-700 transition-colors duration-150 focus:outline-none focus:ring-2 focus:ring-slate-300 rounded-md p-1.5"
                  title="Schedule"
                >
                  <Clock24Regular />
                </button>
                {openMenu === "schedule" && (
                  <div
                    key="schedule-collapsed"
                    ref={scheduleMenuRefCollapsed}
                    className="absolute right-0 top-full mt-2 w-48 rounded-lg bg-white shadow-lg ring-1 ring-black/5 z-20"
                    onClick={(e) => e.stopPropagation()}
                    onMouseDown={(e) => e.stopPropagation()}
                  >
                    <button
                      onClick={() => handleScheduleClick("afternoon")}
                      onMouseDown={(e) => e.stopPropagation()}
                      className="w-full text-left px-3 py-2 text-sm text-slate-700 hover:bg-slate-50 rounded-md focus:outline-none focus:bg-slate-50"
                    >
                      Afternoon
                    </button>
                    <button
                      onClick={() => handleScheduleClick("tomorrow")}
                      onMouseDown={(e) => e.stopPropagation()}
                      className="w-full text-left px-3 py-2 text-sm text-slate-700 hover:bg-slate-50 rounded-md focus:outline-none focus:bg-slate-50"
                    >
                      Tomorrow
                    </button>
                    <button
                      onClick={() => handleScheduleClick("this_week")}
                      onMouseDown={(e) => e.stopPropagation()}
                      className="w-full text-left px-3 py-2 text-sm text-slate-700 hover:bg-slate-50 rounded-md focus:outline-none focus:bg-slate-50"
                    >
                      This Week
                    </button>
                    <button
                      onClick={() => handleScheduleClick("next_week")}
                      onMouseDown={(e) => e.stopPropagation()}
                      className="w-full text-left px-3 py-2 text-sm text-slate-700 hover:bg-slate-50 rounded-md focus:outline-none focus:bg-slate-50"
                    >
                      Next Week
                    </button>
                  </div>
                )}
              </div>
            )}
            <div className="relative">
              <button
                data-menu-trigger
                data-add-to-today-button
                onClick={(e) => {
                  e.stopPropagation();
                  setOpenMenu(
                    openMenu === "add-to-today" ? null : "add-to-today"
                  );
                }}
                onMouseDown={(e) => e.stopPropagation()}
                aria-label="Add to Today"
                className="text-slate-500 hover:text-slate-700 transition-colors duration-150 focus:outline-none focus:ring-2 focus:ring-slate-300 rounded-md p-1.5"
                title="Add to Today"
              >
                <Pin24Regular />
              </button>
              {!expanded && openMenu === "add-to-today" && (
                <div
                  key="add-to-today-collapsed"
                  ref={addToTodayMenuRef}
                  className="absolute right-0 top-full mt-2 w-48 rounded-lg bg-white shadow-lg ring-1 ring-black/5 z-20"
                  onClick={(e) => e.stopPropagation()}
                  onMouseDown={(e) => e.stopPropagation()}
                >
                  <button
                    onClick={() => handleAddToTodayScheduleClick("focus_30m")}
                    onMouseDown={(e) => e.stopPropagation()}
                    className="w-full text-left px-3 py-2 text-sm text-slate-700 hover:bg-slate-50 rounded-md focus:outline-none focus:bg-slate-50"
                  >
                    Focus 30m
                  </button>
                  <button
                    onClick={() => handleAddToTodayScheduleClick("focus_60m")}
                    onMouseDown={(e) => e.stopPropagation()}
                    className="w-full text-left px-3 py-2 text-sm text-slate-700 hover:bg-slate-50 rounded-md focus:outline-none focus:bg-slate-50"
                  >
                    Focus 60m
                  </button>
                  <button
                    onClick={() =>
                      handleAddToTodayScheduleClick("block_pm_admin")
                    }
                    onMouseDown={(e) => e.stopPropagation()}
                    className="w-full text-left px-3 py-2 text-sm text-slate-700 hover:bg-slate-50 rounded-md focus:outline-none focus:bg-slate-50"
                  >
                    Block PM Admin
                  </button>
                  <button
                    onClick={() => handleAddToTodayScheduleClick("pick_time")}
                    onMouseDown={(e) => e.stopPropagation()}
                    className="w-full text-left px-3 py-2 text-sm text-slate-700 hover:bg-slate-50 rounded-md focus:outline-none focus:bg-slate-50"
                  >
                    Pick time…
                  </button>
                </div>
              )}
            </div>
            <div className="relative">
              <button
                data-menu-trigger
                data-overflow-button
                onClick={handleToggleOverflow}
                onMouseDown={(e) => e.stopPropagation()}
                aria-label="More actions"
                className="text-slate-500 hover:text-slate-700 transition-colors duration-150 focus:outline-none focus:ring-2 focus:ring-slate-300 rounded-md p-1.5"
                title="More actions"
              >
                <MoreHorizontal24Regular />
              </button>
              {openMenu === "overflow" && (
                <div
                  key="overflow-menu"
                  ref={overflowMenuRef}
                  className="absolute right-0 top-full mt-2 w-48 rounded-lg bg-white shadow-lg ring-1 ring-black/5 z-20"
                  onClick={(e) => e.stopPropagation()}
                  onMouseDown={(e) => e.stopPropagation()}
                >
                  <button
                    onClick={async (e) => {
                      e.stopPropagation();
                      setOpenMenu(null);
                      await handleCreateTaskClick();
                    }}
                    onMouseDown={(e) => e.stopPropagation()}
                    className="w-full text-left px-3 py-2 text-sm text-slate-700 hover:bg-slate-50 rounded-md focus:outline-none focus:bg-slate-50 flex items-center gap-2"
                  >
                    <Add24Regular className="w-4 h-4" />
                    Add as Task
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Expanded content */}
      <div
        className={`overflow-hidden transition-all duration-200 ease-in-out ${
          expanded ? "max-h-[60vh] opacity-100" : "max-h-0 opacity-0"
        }`}
      >
        <div className="px-4 pb-4 border-t border-slate-200 flex flex-col" style={{ height: expanded ? "60vh" : "auto" }}>
          {/* Workspace Action Bar */}
          <div className="pt-4 pb-4 flex flex-wrap gap-2 flex-shrink-0">
            <div className="relative">
              <button
                data-menu-trigger
                data-defer-button
                onClick={handleToggleDeferExpanded}
                onMouseDown={(e) => e.stopPropagation()}
                className="inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium border border-transparent focus:outline-none focus:ring-2 focus:ring-slate-300 transition-colors bg-amber-50 text-amber-800 hover:bg-amber-100"
              >
                <ArrowRight24Regular className="w-4 h-4" />
                Defer
              </button>
              {openMenu === "defer-expanded" && (
                <div
                  key="defer-expanded"
                  ref={deferMenuRefExpanded}
                  className="absolute left-0 top-full mt-2 w-48 rounded-lg bg-white shadow-lg ring-1 ring-black/5 z-20"
                  onClick={(e) => e.stopPropagation()}
                  onMouseDown={(e) => e.stopPropagation()}
                >
                  <button
                    onClick={() => handleDeferClick("afternoon")}
                    onMouseDown={(e) => e.stopPropagation()}
                    className="w-full text-left px-3 py-2 text-sm text-slate-700 hover:bg-slate-50 rounded-md focus:outline-none focus:bg-slate-50"
                  >
                    Afternoon
                  </button>
                  <button
                    onClick={() => handleDeferClick("tomorrow")}
                    onMouseDown={(e) => e.stopPropagation()}
                    className="w-full text-left px-3 py-2 text-sm text-slate-700 hover:bg-slate-50 rounded-md focus:outline-none focus:bg-slate-50"
                  >
                    Tomorrow
                  </button>
                  <button
                    onClick={() => handleDeferClick("this_week")}
                    onMouseDown={(e) => e.stopPropagation()}
                    className="w-full text-left px-3 py-2 text-sm text-slate-700 hover:bg-slate-50 rounded-md focus:outline-none focus:bg-slate-50"
                  >
                    This Week
                  </button>
                  <button
                    onClick={() => handleDeferClick("next_week")}
                    onMouseDown={(e) => e.stopPropagation()}
                    className="w-full text-left px-3 py-2 text-sm text-slate-700 hover:bg-slate-50 rounded-md focus:outline-none focus:bg-slate-50"
                  >
                    Next Week
                  </button>
                </div>
              )}
            </div>
            <div className="relative">
              <button
                data-menu-trigger
                data-schedule-button
                onClick={handleToggleSchedule}
                onMouseDown={(e) => e.stopPropagation()}
                className="inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium border border-transparent focus:outline-none focus:ring-2 focus:ring-slate-300 transition-colors bg-blue-50 text-blue-800 hover:bg-blue-100"
              >
                <Clock24Regular className="w-4 h-4" />
                Schedule for later
              </button>
              {expanded && openMenu === "schedule" && (
                <div
                  key="schedule-expanded"
                  ref={scheduleMenuRefExpanded}
                  className="absolute left-0 top-full mt-2 w-48 rounded-lg bg-white shadow-lg ring-1 ring-black/5 z-20"
                  onClick={(e) => e.stopPropagation()}
                  onMouseDown={(e) => e.stopPropagation()}
                >
                  <button
                    onClick={() => handleScheduleClick("afternoon")}
                    onMouseDown={(e) => e.stopPropagation()}
                    className="w-full text-left px-3 py-2 text-sm text-slate-700 hover:bg-slate-50 rounded-md focus:outline-none focus:bg-slate-50"
                  >
                    Afternoon
                  </button>
                  <button
                    onClick={() => handleScheduleClick("tomorrow")}
                    onMouseDown={(e) => e.stopPropagation()}
                    className="w-full text-left px-3 py-2 text-sm text-slate-700 hover:bg-slate-50 rounded-md focus:outline-none focus:bg-slate-50"
                  >
                    Tomorrow
                  </button>
                  <button
                    onClick={() => handleScheduleClick("this_week")}
                    onMouseDown={(e) => e.stopPropagation()}
                    className="w-full text-left px-3 py-2 text-sm text-slate-700 hover:bg-slate-50 rounded-md focus:outline-none focus:bg-slate-50"
                  >
                    This Week
                  </button>
                  <button
                    onClick={() => handleScheduleClick("next_week")}
                    onMouseDown={(e) => e.stopPropagation()}
                    className="w-full text-left px-3 py-2 text-sm text-slate-700 hover:bg-slate-50 rounded-md focus:outline-none focus:bg-slate-50"
                  >
                    Next Week
                  </button>
                </div>
              )}
            </div>
            <div className="relative">
              <button
                data-menu-trigger
                data-add-to-today-button
                onClick={handleToggleAddToToday}
                onMouseDown={(e) => e.stopPropagation()}
                className="inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium border border-transparent focus:outline-none focus:ring-2 focus:ring-slate-300 transition-colors bg-emerald-50 text-emerald-800 hover:bg-emerald-100"
              >
                <Pin24Regular className="w-4 h-4" />
                Add to Today
              </button>
              {expanded && openMenu === "add-to-today" && (
                <div
                  key="add-to-today-menu"
                  ref={addToTodayMenuRef}
                  className="absolute left-0 top-full mt-2 w-48 rounded-lg bg-white shadow-lg ring-1 ring-black/5 z-20"
                  onClick={(e) => e.stopPropagation()}
                  onMouseDown={(e) => e.stopPropagation()}
                >
                  <button
                    onClick={() => handleAddToTodayScheduleClick("focus_30m")}
                    onMouseDown={(e) => e.stopPropagation()}
                    className="w-full text-left px-3 py-2 text-sm text-slate-700 hover:bg-slate-50 rounded-md focus:outline-none focus:bg-slate-50"
                  >
                    Focus 30m
                  </button>
                  <button
                    onClick={() => handleAddToTodayScheduleClick("focus_60m")}
                    onMouseDown={(e) => e.stopPropagation()}
                    className="w-full text-left px-3 py-2 text-sm text-slate-700 hover:bg-slate-50 rounded-md focus:outline-none focus:bg-slate-50"
                  >
                    Focus 60m
                  </button>
                  <button
                    onClick={() =>
                      handleAddToTodayScheduleClick("block_pm_admin")
                    }
                    onMouseDown={(e) => e.stopPropagation()}
                    className="w-full text-left px-3 py-2 text-sm text-slate-700 hover:bg-slate-50 rounded-md focus:outline-none focus:bg-slate-50"
                  >
                    Block PM Admin
                  </button>
                  <button
                    onClick={() => handleAddToTodayScheduleClick("pick_time")}
                    onMouseDown={(e) => e.stopPropagation()}
                    className="w-full text-left px-3 py-2 text-sm text-slate-700 hover:bg-slate-50 rounded-md focus:outline-none focus:bg-slate-50"
                  >
                    Pick time…
                  </button>
                </div>
              )}
            </div>
            <button
              onClick={async (e) => {
                e.stopPropagation();
                await handleCreateTaskClick();
              }}
              onMouseDown={(e) => e.stopPropagation()}
              className="inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium border border-transparent focus:outline-none focus:ring-2 focus:ring-slate-300 transition-colors bg-violet-50 text-violet-800 hover:bg-violet-100"
            >
              <Add24Regular className="w-4 h-4" />
              Add as Task
            </button>
          </div>

          {/* Content area */}
          <div
            className="flex-1 min-h-0 relative"
            onClick={(e) => e.stopPropagation()}
          >
            <AssistantChat
              actionId={item.action_id}
              threadId={threadId}
              suggestedTaskId={item.task_id}
              suggestedTaskTitle={item.task_title || undefined}
              summary={item.preview}
              meta={{
                from: item.source,
                threadLen: undefined, // TODO: Get from thread data if available
                lastAt: undefined, // TODO: Get from thread data if available
              }}
              onThreadCreated={handleThreadCreated}
              onOpenWorkroom={handleOpenInWorkroom}
              shouldFocus={expanded}
              trustMode={trustMode}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
