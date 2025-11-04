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

type ActionCardProps = {
  item: {
    action_id: string;
    source: "email" | "teams" | "doc";
    priority: "high" | "medium" | "low";
    preview: string;
    action_label: "Respond" | "Approve" | "Review";
    thread_id?: string;
  };
  onToggleExpand: (id: string) => void;
  expanded: boolean;
  onDefer: (
    id: string,
    bucket: "afternoon" | "tomorrow" | "this_week" | "next_week"
  ) => Promise<void>;
  onAddToToday: (id: string) => Promise<void>;
  onOpenChat: (id: string) => void;
  onCreateTask: (id: string) => Promise<void>;
  onSchedule: (
    id: string,
    preset: "focus_30m" | "focus_60m" | "block_pm_admin" | "pick_time"
  ) => Promise<void>;
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
  onToggleExpand,
  onDefer,
  onAddToToday,
  onOpenChat,
  onCreateTask,
  onSchedule,
}: ActionCardProps) {
  const router = useRouter();
  const [openMenu, setOpenMenu] = useState<MenuType>(null);
  const deferMenuRefCollapsed = useRef<HTMLDivElement>(null);
  const deferMenuRefExpanded = useRef<HTMLDivElement>(null);
  const scheduleMenuRefExpanded = useRef<HTMLDivElement>(null);
  const addToTodayMenuRef = useRef<HTMLDivElement>(null);
  const overflowMenuRef = useRef<HTMLDivElement>(null);

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
        menuRef = scheduleMenuRefExpanded.current;
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
      // Ignore clicks on menu triggers
      const target = e.target as HTMLElement;
      if (target.closest("[data-menu-trigger]")) {
        return;
      }
      onToggleExpand(item.action_id);
    },
    [item.action_id, onToggleExpand]
  );

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      onToggleExpand(item.action_id);
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
    async (
      preset: "focus_30m" | "focus_60m" | "block_pm_admin" | "pick_time"
    ) => {
      await onSchedule(item.action_id, preset);
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
    // Expand card to show defer menu (Schedule uses defer menu now)
    if (!expanded) {
      onToggleExpand(item.action_id);
      // Open defer menu after expansion
      setTimeout(() => {
        setOpenMenu("defer-expanded");
      }, 100);
    } else {
      setOpenMenu("defer-expanded");
    }
  }, [expanded, item.action_id, onToggleExpand]);

  const handleChatClick = useCallback(
    (e: React.MouseEvent) => {
      e.stopPropagation();
      // onOpenChat already handles expanding/collapsing the card
      onOpenChat(item.action_id);
    },
    [item.action_id, onOpenChat]
  );

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

  const handleOpenInWorkroom = () => {
    router.push("/workroom");
  };

  const sourceColor = SOURCE_COLORS[item.source];
  const priorityStyle = PRIORITY_STYLES[item.priority];
  const priorityLabel = PRIORITY_LABELS[item.priority];

  return (
    <div
      role="button"
      tabIndex={0}
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
      data-selected={expanded}
      className={`group bg-slate-50 border border-slate-200 rounded-xl shadow-sm transition-all duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-slate-300 focus:ring-offset-2 cursor-pointer ${
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
          <p className="text-sm text-slate-500 mb-3">{item.action_label}</p>

          {/* Collapsed toolbar - Chat, Defer, Overflow */}
          <div className="opacity-0 group-hover:opacity-100 focus-within:opacity-100 transition-opacity duration-200 flex items-center gap-2 justify-end">
            <button
              onClick={handleChatClick}
              onMouseDown={(e) => e.stopPropagation()}
              aria-label="Chat"
              className="text-slate-500 hover:text-slate-700 transition-colors duration-150 focus:outline-none focus:ring-2 focus:ring-slate-300 rounded-md p-1.5"
              title="Chat"
            >
              <Chat24Regular />
            </button>
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
              {openMenu === "defer-collapsed" && (
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
                    onClick={(e) => {
                      e.stopPropagation();
                      setOpenMenu(null);
                      // Expand card and open Add to Today menu
                      if (!expanded) {
                        onToggleExpand(item.action_id);
                        setTimeout(() => {
                          setOpenMenu("add-to-today");
                        }, 100);
                      } else {
                        setOpenMenu("add-to-today");
                      }
                    }}
                    onMouseDown={(e) => e.stopPropagation()}
                    className="w-full text-left px-3 py-2 text-sm text-slate-700 hover:bg-slate-50 rounded-md focus:outline-none focus:bg-slate-50 flex items-center gap-2"
                  >
                    <Pin24Regular className="w-4 h-4" />
                    Add to Today
                  </button>
                  <button
                    onClick={handleCreateTaskClick}
                    onMouseDown={(e) => e.stopPropagation()}
                    className="w-full text-left px-3 py-2 text-sm text-slate-700 hover:bg-slate-50 rounded-md focus:outline-none focus:bg-slate-50 flex items-center gap-2"
                  >
                    <Add24Regular className="w-4 h-4" />
                    Add as Task
                  </button>
                  <button
                    onClick={handleScheduleFromOverflowClick}
                    onMouseDown={(e) => e.stopPropagation()}
                    className="w-full text-left px-3 py-2 text-sm text-slate-700 hover:bg-slate-50 rounded-md focus:outline-none focus:bg-slate-50 flex items-center gap-2"
                  >
                    <Clock24Regular className="w-4 h-4" />
                    Schedule for later
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
        <div className="px-4 pb-4 border-t border-slate-200">
          {/* Workspace Action Bar */}
          <div className="pt-4 pb-4 flex flex-wrap gap-2">
            <button
              onClick={handleChatClick}
              onMouseDown={(e) => e.stopPropagation()}
              className="inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium border border-transparent focus:outline-none focus:ring-2 focus:ring-slate-300 transition-colors bg-slate-50 text-slate-700 hover:bg-slate-100"
            >
              <Chat24Regular className="w-4 h-4" />
              Chat
            </button>
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
              {openMenu === "schedule" && (
                <div
                  key="schedule-expanded"
                  ref={scheduleMenuRefExpanded}
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
                data-add-to-today-button
                onClick={handleToggleAddToToday}
                onMouseDown={(e) => e.stopPropagation()}
                className="inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium border border-transparent focus:outline-none focus:ring-2 focus:ring-slate-300 transition-colors bg-emerald-50 text-emerald-800 hover:bg-emerald-100"
              >
                <Pin24Regular className="w-4 h-4" />
                Add to Today
              </button>
              {openMenu === "add-to-today" && (
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
          <div className="space-y-4 max-h-[calc(60vh-180px)] overflow-y-auto">
            {/* Inline Chat preview */}
            <div className="rounded-lg border border-slate-200 p-4 bg-white">
              <div className="mb-2 text-sm font-medium text-slate-700">
                Inline Chat
              </div>
              <div className="mb-2 text-xs text-slate-500">Stub - Phase 0</div>
              {item.thread_id && (
                <div className="text-xs text-slate-500 mb-2">
                  Thread: {item.thread_id}
                </div>
              )}
              <button
                onClick={handleOpenInWorkroom}
                className="text-xs text-blue-600 hover:text-blue-700 underline focus:outline-none focus:ring-2 focus:ring-blue-300 rounded"
              >
                Open in Workroom
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
