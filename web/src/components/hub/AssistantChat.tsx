import { useState, useRef, useEffect, useCallback, memo, useMemo } from "react";
import {
  Send24Regular,
  ChevronDown24Regular,
  ArrowClockwise24Regular,
  Add24Regular,
  Link24Regular,
} from "@fluentui/react-icons";
import { api } from "../../lib/api";
import { workroomApi } from "../../lib/workroomApi";
import useSWR from "swr";
import { ActionEmbedComponent } from "../workroom/ActionEmbed";
import { ActionSummary } from "../shared/ActionSummary";
import type { LlmOperation as SummaryOperation } from "../shared/ActionSummary";
import { SlashMenu, SlashCommand } from "../ui/SlashMenu";
import { AssistantSurfacesRenderer } from "../assistant/AssistantSurfacesRenderer";
import {
  parseInteractiveSurfaces,
  type InteractiveSurface,
  type SurfaceNavigateTo,
} from "../../lib/llm/surfaces";

// Custom scrollbar styles
const scrollbarStyles = `
  .chat-scrollbar::-webkit-scrollbar {
    width: 8px;
  }
  .chat-scrollbar::-webkit-scrollbar-track {
    background: #ffffff;
    border-radius: 4px;
  }
  .chat-scrollbar::-webkit-scrollbar-thumb {
    background: #cbd5e1;
    border-radius: 4px;
  }
  .chat-scrollbar::-webkit-scrollbar-thumb:hover {
    background: #94a3b8;
  }
`;

type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  ts: string;
  optimistic?: boolean;
  error?: boolean;
  retryable?: boolean;
  errorMessage?: string;
  embeds?: any[]; // ActionEmbed[]
  surfaces?: InteractiveSurface[];
};

type MessageView = {
  id: string;
  role: "user" | "assistant";
  content: string;
  embeds?: any[];
  surfaces?: InteractiveSurface[];
  marginTop: string;
  timestampLabel: string;
  showTimestamp: boolean;
  shouldAnimate: boolean;
  startDelayMs?: number;
  error?: boolean;
  retryable?: boolean;
  errorMessage?: string;
};

type OperationRecord = SummaryOperation & {
  localId: string;
};

type OperationError = {
  id: string;
  message: string;
  op?: string;
  params?: Record<string, any>;
};

type ProjectOption = {
  id: string;
  title: string;
};

type TaskOption = {
  id: string;
  title: string;
  projectId?: string | null;
  projectTitle?: string | null;
};

type TaskSuggestion = TaskOption & {
  meta?: string;
  isSuggested?: boolean;
};

type ParsedTokenChip = {
  raw: string;
  kind: "ref" | "op";
  label: string;
};

type OperationsState = {
  applied: OperationRecord[];
  pending: OperationRecord[];
  errors: OperationError[];
};

type OperationApiGroup = {
  suggest: (body: { message?: string; thread_id?: string }) => Promise<any>;
  approve: (body: { operation: any }) => Promise<any>;
  edit: (body: { operation: any; edited_params: any }) => Promise<any>;
  decline: (body: { operation: any }) => Promise<any>;
  undo: (body: { operation: any; original_state?: any }) => Promise<any>;
};

const generateOperationLocalId = () => {
  const cryptoObj =
    typeof globalThis !== "undefined" ? globalThis.crypto : undefined;
  if (cryptoObj?.randomUUID) {
    return cryptoObj.randomUUID();
  }
  return `op-${Math.random().toString(36).slice(2)}-${Date.now()}`;
};

const removeByLocalId = (ops: OperationRecord[], id: string) =>
  ops.filter((item) => item.localId !== id);

const sanitizeOperationForApi = (
  op: SummaryOperation | OperationRecord,
  options?: { forceCurrentProject?: boolean }
) => {
  const params = { ...op.params };
  if (options?.forceCurrentProject) {
    delete params.project;
    delete params.project_id;
  }
  return {
    op: op.op,
    params,
  };
};

const formatOperationErrors = (errors?: any[]): OperationError[] =>
  (errors ?? []).map((err) => ({
    id: generateOperationLocalId(),
    message: err?.error || "Operation failed. Please try again.",
    op: err?.op,
    params: err?.params,
  }));

const createAssistantMessage = (content: string): Message => ({
  id: generateOperationLocalId(),
  role: "assistant",
  content,
  ts: new Date().toISOString(),
  optimistic: false,
  error: false,
});

const TOKEN_REGEX = /\[(ref|op)\s+([^\]]+)\]/gi;
const KEY_VALUE_REGEX = /(\w+):(?:"([^"]*)"|([^\s]+))/g;
const OP_TOKEN_REGEX = /^\[op\s+([^\]]+)\]$/i;

const escapeTokenValue = (value: string) => value.replace(/"/g, '\\"');

const parseTokenBody = (body: string): Record<string, string> => {
  const pairs: Record<string, string> = {};
  body.replace(
    KEY_VALUE_REGEX,
    (_, key: string, quoted: string, bare: string) => {
      const cleaned = (quoted ?? bare ?? "").replace(/\\"/g, '"');
      pairs[key] = cleaned;
      return "";
    }
  );
  return pairs;
};

const convertOpTokenToOperation = (
  token: string
): SummaryOperation | null => {
  const match = token.match(OP_TOKEN_REGEX);
  if (!match) {
    return null;
  }
  const pairs = parseTokenBody(match[1]);
  const opType = pairs.type;
  if (!opType) {
    return null;
  }
  const params: Record<string, string> = {};
  Object.entries(pairs).forEach(([key, value]) => {
    if (key !== "type" && key !== "v") {
      params[key] = value;
    }
  });
  return {
    op: opType,
    params,
  };
};

const extractTokensFromMessage = (text: string): ParsedTokenChip[] => {
  if (!text) {
    return [];
  }
  const matches = text.matchAll(TOKEN_REGEX);
  const tokens: ParsedTokenChip[] = [];
  for (const match of matches) {
    const raw = match[0] || "";
    const kind = (match[1] as "ref" | "op") || "ref";
    const body = match[2] || "";
    const data = parseTokenBody(body);
    if (!raw) continue;
    if (kind === "ref") {
      const refType = data.type || "ref";
      const name = data.name || data.id || "";
      tokens.push({
        raw,
        kind,
        label: `${refType}: ${name || "unnamed"}`,
      });
    } else {
      const opType = data.type || "op";
      const hint = data.title || data.status || data.project || "";
      tokens.push({
        raw,
        kind,
        label: hint ? `${opType} • ${hint}` : opType,
      });
    }
  }
  return tokens;
};

type ThreadResponse = {
  ok: boolean;
  thread: {
    id: string;
    messages: Message[];
  };
};

type AssistantChatProps = {
  actionId: string;
  taskId?: string | null; // For workroom mode
  threadId?: string | null;
  projectId?: string | null;
  projectTitle?: string | null;
  suggestedTaskId?: string | null;
  suggestedTaskTitle?: string | null;
  summary?: string;
  meta?: {
    from?: string;
    threadLen?: number;
    lastAt?: string;
  };
  onThreadCreated?: (threadId: string) => void;
  onOpenWorkroom?: (threadId?: string) => void;
  shouldFocus?: boolean;
  mode?: "workroom" | "default";
  onAddReference?: (ref: any) => void;
  onInputFocus?: () => void;
  trustMode?: "training_wheels" | "supervised" | "autonomous";
  onOperationsUpdate?: (ops: {
    applied: any[];
    pending: any[];
    errors: any[];
  }) => void;
};

// MessageItem component - only accepts data props, no functions
const MessageItem = memo(
  ({
    view,
    onRetry,
    onEmbedUpdate,
    animatedRef,
    activeAssistantId,
    onInvokeSurfaceOp,
    onNavigateSurface,
  }: {
    view: MessageView;
    onRetry: (id: string) => void;
    onEmbedUpdate: (messageId: string, embed: any) => void;
    animatedRef: React.MutableRefObject<Set<string>>;
    activeAssistantId: string | null;
    onInvokeSurfaceOp?: (
      opToken: string,
      options?: { confirm?: boolean }
    ) => void;
    onNavigateSurface?: (nav: SurfaceNavigateTo) => void;
  }) => {
    return (
      <div
        className={`flex flex-col gap-0.5 transition-all duration-300 w-full ${
          view.role === "user" ? "items-end" : "items-start"
        } ${view.marginTop}`}
      >
        <div
          className={`flex items-end gap-2 ${
            view.role === "user"
              ? "justify-end flex-row-reverse"
              : "justify-start"
          }`}
        >
          {view.error && view.retryable && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onRetry(view.id);
              }}
              className="flex-shrink-0 text-red-600 hover:text-red-700 focus:outline-none focus:ring-2 focus:ring-red-300 rounded p-1 transition-colors"
              aria-label="Retry sending message"
              title="Retry sending"
            >
              <ArrowClockwise24Regular className="w-4 h-4" />
            </button>
          )}
          <div
            className={`rounded-lg px-4 py-2.5 shadow-sm ${
              view.role === "user" ? "max-w-[80%]" : "max-w-[80%]"
            } ${
              view.role === "assistant"
                ? "bg-slate-100 text-slate-900 border border-slate-200"
                : view.error
                ? "bg-red-50 text-red-900 border border-red-200"
                : "bg-blue-500 text-white"
            }`}
            style={{
              wordWrap: "break-word",
              overflowWrap: "break-word",
              minWidth: "fit-content",
            }}
          >
            <div
              className="text-sm leading-relaxed"
              style={{ wordBreak: "normal" }}
            >
              {view.role === "assistant" ? (
                <TypingMessageContent
                  content={view.content}
                  id={view.id}
                  shouldAnimate={view.shouldAnimate}
                  animatedRef={animatedRef}
                  startDelayMs={view.startDelayMs}
                  activeAssistantId={activeAssistantId}
                />
              ) : (
                view.content
              )}
            </div>
            {view.error && view.errorMessage && (
              <div className="text-xs text-red-600 mt-1 opacity-75">
                {view.errorMessage}
              </div>
            )}
          </div>
        </div>
        {view.surfaces && view.surfaces.length > 0 && (
          <div className="mt-3 w-full">
            <AssistantSurfacesRenderer
              surfaces={view.surfaces}
              onInvokeOp={onInvokeSurfaceOp}
              onNavigate={onNavigateSurface}
            />
          </div>
        )}
        {/* Render ActionEmbeds after message content */}
        {view.embeds && view.embeds.length > 0 && (
          <div className="mt-2 space-y-2">
            {view.embeds.map((embed: any) => (
              <ActionEmbedComponent
                key={embed.id}
                embed={embed}
                messageId={view.id}
                onUpdate={(updatedEmbed) => {
                  onEmbedUpdate(view.id, updatedEmbed);
                }}
              />
            ))}
          </div>
        )}
        {view.showTimestamp && (
          <span className="text-xs text-slate-500 mt-1">
            {view.timestampLabel}
          </span>
        )}
      </div>
    );
  },
  (prevProps, nextProps) => {
    // Only re-render if view data changes (functions are stable)
    const prev = prevProps.view;
    const next = nextProps.view;
    return (
      prev.id === next.id &&
      prev.content === next.content &&
      prev.role === next.role &&
      prev.error === next.error &&
      prev.retryable === next.retryable &&
      prev.errorMessage === next.errorMessage &&
      prev.marginTop === next.marginTop &&
      prev.timestampLabel === next.timestampLabel &&
      prev.showTimestamp === next.showTimestamp &&
      prev.shouldAnimate === next.shouldAnimate &&
      prev.surfaces === next.surfaces &&
      prevProps.onRetry === nextProps.onRetry &&
      prevProps.onEmbedUpdate === nextProps.onEmbedUpdate &&
      prevProps.animatedRef === nextProps.animatedRef &&
      prevProps.activeAssistantId === nextProps.activeAssistantId &&
      prevProps.onInvokeSurfaceOp === nextProps.onInvokeSurfaceOp &&
      prevProps.onNavigateSurface === nextProps.onNavigateSurface
    );
  }
);
MessageItem.displayName = "MessageItem";

// TypingMessageContent - extracted for use in MessageItem
const TypingMessageContent = memo(
  ({
    content,
    id,
    shouldAnimate,
    animatedRef,
    startDelayMs = 0,
    activeAssistantId,
  }: {
    content: string;
    id: string;
    shouldAnimate: boolean;
    animatedRef: React.MutableRefObject<Set<string>>;
    startDelayMs?: number;
    activeAssistantId: string | null;
  }) => {
    const markAsSeen = useCallback(() => {
      animatedRef.current.add(id);
    }, [id, animatedRef]);

    // Use activeAssistantId as interrupt key - if this message is not the active one, interrupt
    const interruptKey = activeAssistantId === id ? id : null;

    const displayedText = useTypingEffect(
      content,
      15,
      shouldAnimate,
      markAsSeen,
      startDelayMs,
      interruptKey
    );
    return <>{displayedText}</>;
  }
);
TypingMessageContent.displayName = "TypingMessageContent";

// Typing effect hook for assistant messages
function useTypingEffect(
  text: string,
  speed: number = 15,
  enabled: boolean = true,
  onComplete?: () => void,
  startDelayMs: number = 0,
  interruptKey?: string | null
) {
  const [displayedText, setDisplayedText] = useState("");
  const [hasStarted, setHasStarted] = useState(false);

  // Handle interruption: if interruptKey changes and we're mid-animation, complete immediately
  useEffect(() => {
    if (
      interruptKey !== undefined &&
      interruptKey !== null &&
      enabled &&
      hasStarted &&
      displayedText.length < text.length
    ) {
      // Interrupted - show full text immediately
      setDisplayedText(text);
      if (onComplete) {
        onComplete();
      }
    }
  }, [
    interruptKey,
    enabled,
    hasStarted,
    displayedText.length,
    text.length,
    text,
    onComplete,
  ]);

  useEffect(() => {
    if (!enabled) {
      setDisplayedText(text);
      setHasStarted(true);
      // Mark as complete immediately if animation is disabled
      if (onComplete && text.length > 0) {
        onComplete();
      }
      return;
    }

    // Handle initial delay before starting animation
    if (!hasStarted && startDelayMs > 0) {
      const delayTimeout = setTimeout(() => {
        setHasStarted(true);
      }, startDelayMs);
      return () => clearTimeout(delayTimeout);
    }

    // Start typing animation after delay (or immediately if no delay)
    if (hasStarted && displayedText.length < text.length) {
      const timeout = setTimeout(() => {
        const newLength = displayedText.length + 1;
        setDisplayedText(text.slice(0, newLength));

        // Mark as complete when animation finishes
        if (newLength === text.length && onComplete) {
          onComplete();
        }
      }, speed);
      return () => clearTimeout(timeout);
    } else if (
      hasStarted &&
      displayedText.length === text.length &&
      onComplete
    ) {
      // Already complete, mark it
      onComplete();
    }
  }, [
    displayedText,
    text,
    speed,
    enabled,
    onComplete,
    startDelayMs,
    hasStarted,
  ]);

  // Reset when text changes
  useEffect(() => {
    if (text !== displayedText && displayedText.length === text.length) {
      setDisplayedText("");
      setHasStarted(false);
    }
  }, [text, displayedText]);

  return displayedText || "";
}

// MessageList component - memoized to prevent re-renders
const MessageList = memo(
  ({
    messageViews,
    isTyping,
    onRetryMessage,
    onEmbedUpdate,
    animatedRef,
    activeAssistantId,
    onInvokeSurfaceOp,
    onNavigateSurface,
  }: {
    messageViews: MessageView[];
    isTyping: boolean;
    onRetryMessage: (id: string) => void;
    onEmbedUpdate: (messageId: string, embed: any) => void;
    animatedRef: React.MutableRefObject<Set<string>>;
    activeAssistantId: string | null;
    onInvokeSurfaceOp?: (
      opToken: string,
      options?: { confirm?: boolean }
    ) => void;
    onNavigateSurface?: (nav: SurfaceNavigateTo) => void;
  }) => {
    return (
      <>
        {messageViews.length === 0 ? (
          <div className="text-sm text-slate-500 py-4 text-center">
            No messages yet. Start the conversation!
          </div>
        ) : (
          messageViews.map((view) => (
            <MessageItem
              key={view.id}
              view={view}
              onRetry={onRetryMessage}
              onEmbedUpdate={onEmbedUpdate}
              animatedRef={animatedRef}
              activeAssistantId={activeAssistantId}
              onInvokeSurfaceOp={onInvokeSurfaceOp}
              onNavigateSurface={onNavigateSurface}
            />
          ))
        )}
        {isTyping && (
          <div className="flex items-start gap-2 mt-2 fade-in">
            <div className="bg-slate-100 text-slate-900 border border-slate-200 rounded-lg px-4 py-2.5 max-w-[80%] shadow-sm">
              <div className="flex gap-1">
                <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" />
                <div
                  className="w-2 h-2 bg-slate-400 rounded-full animate-bounce"
                  style={{ animationDelay: "0.2s" }}
                />
                <div
                  className="w-2 h-2 bg-slate-400 rounded-full animate-bounce"
                  style={{ animationDelay: "0.4s" }}
                />
              </div>
            </div>
          </div>
        )}
      </>
    );
  },
  (prevProps, nextProps) => {
    // Only re-render if messageViews array reference changes or isTyping changes
    return (
      prevProps.messageViews === nextProps.messageViews &&
      prevProps.isTyping === nextProps.isTyping &&
      prevProps.onRetryMessage === nextProps.onRetryMessage &&
      prevProps.onEmbedUpdate === nextProps.onEmbedUpdate &&
      prevProps.animatedRef === nextProps.animatedRef &&
      prevProps.activeAssistantId === nextProps.activeAssistantId &&
      prevProps.onInvokeSurfaceOp === nextProps.onInvokeSurfaceOp &&
      prevProps.onNavigateSurface === nextProps.onNavigateSurface
    );
  }
);
MessageList.displayName = "MessageList";

export function AssistantChat({
  actionId,
  taskId,
  threadId: initialThreadId,
  projectId,
  projectTitle,
  suggestedTaskId,
  suggestedTaskTitle,
  summary,
  meta,
  onThreadCreated,
  onOpenWorkroom,
  shouldFocus = false,
  mode = "default",
  onAddReference,
  onInputFocus,
  trustMode = "training_wheels",
  onOperationsUpdate,
}: AssistantChatProps) {
  const [threadId, setThreadId] = useState<string | null>(
    initialThreadId || null
  );
  useEffect(() => {
    const resolvedThreadId = initialThreadId ?? null;
    setThreadId((current) =>
      current === resolvedThreadId ? current : resolvedThreadId
    );
  }, [initialThreadId]);
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const [contextExpanded, setContextExpanded] = useState(false);
  const [draftCache, setDraftCache] = useState<Record<string, string>>({});
  const [operationsState, setOperationsState] = useState<OperationsState>({
    applied: [],
    pending: [],
    errors: [],
  });
  const [projectOptions, setProjectOptions] = useState<ProjectOption[]>([]);
  const [projectIndexState, setProjectIndexState] = useState<
    "idle" | "loading" | "ready"
  >("idle");
  const [isReferenceSearchOpen, setReferenceSearchOpen] = useState(false);
  const [referenceQuery, setReferenceQuery] = useState("");
  const [referenceProjectId, setReferenceProjectId] = useState<string | null>(
    projectId ?? null
  );
  const [referenceResults, setReferenceResults] = useState<TaskOption[]>([]);
  const [referenceLoading, setReferenceLoading] = useState(false);
  const [referenceActiveIndex, setReferenceActiveIndex] = useState(0);
  const referenceSearchAbort = useRef<AbortController | null>(null);
  const [showCreateTaskModal, setShowCreateTaskModal] = useState(false);
  const [inlineNotice, setInlineNotice] = useState<string | null>(null);
  const [hasPrefetchedPicker, setHasPrefetchedPicker] = useState(false);
  const [suggestedTaskTitleResolved, setSuggestedTaskTitleResolved] = useState<
    string | null
  >(suggestedTaskTitle || null);
  useEffect(() => {
    if (suggestedTaskTitle) {
      setSuggestedTaskTitleResolved(suggestedTaskTitle);
    } else if (!suggestedTaskId) {
      setSuggestedTaskTitleResolved(null);
    }
  }, [suggestedTaskId, suggestedTaskTitle]);
  const [isSlashMenuOpen, setSlashMenuOpen] = useState(false);
  const [slashMenuPosition, setSlashMenuPosition] = useState({
    top: 0,
    left: 0,
  });
  const forceCurrentProject = mode === "workroom";
  const appliedOps = operationsState.applied;
  const pendingOps = operationsState.pending;
  const hasErrors = operationsState.errors.length > 0;
  const slashCommands = useMemo<SlashCommand[]>(
    () => [
      {
        id: "insert-task",
        label: "/insert task",
        icon: Link24Regular,
        description: "Insert a task reference token",
      },
      {
        id: "create-task-op",
        label: "/create task",
        icon: Add24Regular,
        description: "Insert a create_task operation token",
      },
    ],
    []
  );
  const parsedTokens = useMemo(
    () => extractTokensFromMessage(message),
    [message]
  );
  const suggestionEntry = useMemo<TaskSuggestion | null>(() => {
    if (!suggestedTaskId) {
      return null;
    }
    const resolvedTitle =
      suggestedTaskTitleResolved || suggestedTaskTitle || "Linked task";
    let resolvedProjectTitle = projectTitle;
    if (!resolvedProjectTitle && projectId) {
      const projectMatch = projectOptions.find(
        (project) => project.id === projectId
      );
      resolvedProjectTitle = projectMatch?.title;
    }
    return {
      id: suggestedTaskId,
      title: resolvedTitle,
      projectId: projectId ?? null,
      projectTitle: resolvedProjectTitle ?? null,
      isSuggested: true,
      meta: "Current link",
    };
  }, [
    suggestedTaskId,
    suggestedTaskTitleResolved,
    suggestedTaskTitle,
    projectId,
    projectTitle,
    projectOptions,
  ]);

  const displayReferenceResults = useMemo<TaskSuggestion[]>(() => {
    const map = new Map<string, TaskSuggestion>();
    if (suggestionEntry) {
      map.set(suggestionEntry.id, suggestionEntry);
    }
    referenceResults.forEach((task) => {
      map.set(task.id, task);
    });
    return Array.from(map.values());
  }, [referenceResults, suggestionEntry]);

  const updateMessageValue = useCallback(
    (nextValue: string) => {
      setMessage(nextValue);
      setDraftCache((prev) => ({ ...prev, [actionId]: nextValue }));
    },
    [actionId]
  );

  const showInlineNotice = useCallback((text: string, timeout = 4000) => {
    setInlineNotice(text);
    if (noticeTimeoutRef.current) {
      clearTimeout(noticeTimeoutRef.current);
    }
    noticeTimeoutRef.current = setTimeout(() => {
      setInlineNotice(null);
      noticeTimeoutRef.current = null;
    }, timeout);
  }, []);

  const ensureProjectsIndex = useCallback(async () => {
    if (projectOptions.length > 0 || projectIndexState === "loading") {
      return projectOptions;
    }
    setProjectIndexState("loading");
    try {
      const response = await workroomApi.listProjectsLite();
      const projects = response?.projects ?? [];
      setProjectOptions(projects);
      setProjectIndexState("ready");
      return projects;
    } catch (error) {
      console.error("Failed to load project index:", error);
      setProjectIndexState("idle");
      showInlineNotice("Unable to load projects. Please try again.");
      throw error;
    }
  }, [projectOptions, projectIndexState, showInlineNotice]);

  const closeReferenceSearch = useCallback(() => {
    referenceSearchAbort.current?.abort();
    setReferenceSearchOpen(false);
    setReferenceQuery("");
    setReferenceResults([]);
    setReferenceActiveIndex(0);
    setReferenceLoading(false);
  }, []);

  const openReferenceSearch = useCallback(() => {
    setReferenceProjectId((current) => {
      if (current) {
        return current;
      }
      if (projectId) {
        return projectId;
      }
      return projectOptions[0]?.id ?? null;
    });
    setReferenceQuery("");
    setReferenceResults([]);
    setReferenceActiveIndex(0);
    setReferenceSearchOpen(true);
  }, [projectId, projectOptions]);

  const runTaskSearch = useCallback(
    async (query: string, projectFilter: string | null) => {
      referenceSearchAbort.current?.abort();
      const controller = new AbortController();
      referenceSearchAbort.current = controller;
      setReferenceLoading(true);
      const normalizedQuery = query.trim();
      try {
        const response = await workroomApi.searchTasksLite({
          projectId: projectFilter,
          query: normalizedQuery,
          limit: 25,
          signal: controller.signal,
        });
        if (!controller.signal.aborted) {
          const normalized =
            response?.tasks?.map((task) => {
              const fallbackTitle =
                task.projectTitle ||
                projectOptions.find((project) => project.id === task.projectId)
                  ?.title ||
                null;
              return {
                id: task.id,
                title: task.title,
                projectId: task.projectId ?? null,
                projectTitle: fallbackTitle,
              };
            }) ?? [];
          setReferenceResults(normalized);
        }
      } catch (error) {
        if ((error as any)?.name !== "AbortError") {
          console.error("Failed to search tasks:", error);
          showInlineNotice("Search failed. Please try again.");
        }
      } finally {
        if (!controller.signal.aborted) {
          setReferenceLoading(false);
        }
      }
    },
    [projectOptions, showInlineNotice]
  );

  useEffect(() => {
    if (!suggestedTaskId || suggestedTaskTitle || suggestedTaskTitleResolved) {
      return;
    }
    let mounted = true;
    workroomApi
      .getTask(suggestedTaskId)
      .then((response) => {
        if (mounted && response?.ok) {
          setSuggestedTaskTitleResolved(response.task?.title || null);
        }
      })
      .catch((error) => {
        console.warn("Failed to load suggested task details:", error);
      });
    return () => {
      mounted = false;
    };
  }, [suggestedTaskId, suggestedTaskTitle, suggestedTaskTitleResolved]);

  useEffect(() => {
    if (hasPrefetchedPicker) {
      return;
    }
    const trimmed = message.trim().toLowerCase();
    if (trimmed.endsWith("/ins") || trimmed.includes("/insert task")) {
      ensureProjectsIndex().catch(() => {});
      setHasPrefetchedPicker(true);
    }
  }, [message, hasPrefetchedPicker, ensureProjectsIndex]);

  useEffect(() => {
    if (!isReferenceSearchOpen) {
      return;
    }
    const debounceId = setTimeout(() => {
      runTaskSearch(referenceQuery, referenceProjectId);
    }, 180);
    return () => {
      clearTimeout(debounceId);
    };
  }, [
    isReferenceSearchOpen,
    referenceQuery,
    referenceProjectId,
    runTaskSearch,
  ]);

  useEffect(() => {
    if (!isReferenceSearchOpen) {
      return;
    }
    ensureProjectsIndex().catch(() => {});
  }, [isReferenceSearchOpen, ensureProjectsIndex]);

  useEffect(() => {
    if (!isReferenceSearchOpen) {
      return;
    }
    setReferenceActiveIndex((current) =>
      Math.min(current, Math.max(displayReferenceResults.length - 1, 0))
    );
  }, [displayReferenceResults.length, isReferenceSearchOpen]);

  const insertTokenAtCursor = useCallback(
    (token: string) => {
      const { start, end } = selectionRef.current;
      const nextValue =
        message.slice(0, start) + token + " " + message.slice(end);
      updateMessageValue(nextValue);
      const nextPos = start + token.length + 1;
      requestAnimationFrame(() => {
        if (textareaRef.current) {
          textareaRef.current.focus();
          textareaRef.current.selectionStart = nextPos;
          textareaRef.current.selectionEnd = nextPos;
        }
        selectionRef.current = { start: nextPos, end: nextPos };
      });
    },
    [message, updateMessageValue]
  );

  const handleRemoveToken = useCallback(
    (raw: string) => {
      const idx = message.indexOf(raw);
      if (idx === -1) return;
      const before = message.slice(0, idx);
      const after = message.slice(idx + raw.length);
      const nextValue = (before + after).replace(/\s{2,}/g, " ").trimStart();
      updateMessageValue(nextValue);
      selectionRef.current = { start: idx, end: idx };
      requestAnimationFrame(() => {
        if (textareaRef.current) {
          textareaRef.current.focus();
          textareaRef.current.selectionStart = idx;
          textareaRef.current.selectionEnd = idx;
        }
      });
    },
    [message, updateMessageValue]
  );

  const handleInsertTaskReference = useCallback(
    (task: TaskOption) => {
      const token = `[ref v:1 type:"task" id:${
        task.id
      } name:"${escapeTokenValue(task.title)}"]`;
      insertTokenAtCursor(token);
      onAddReference?.({ type: "task", id: task.id });
      closeReferenceSearch();
    },
    [insertTokenAtCursor, onAddReference, closeReferenceSearch]
  );

  const handleInsertCreateTaskOp = useCallback(
    (payload: { projectId: string; title: string }) => {
      const token = `[op v:1 type:"create_task" project:${
        payload.projectId
      } title:"${escapeTokenValue(payload.title)}"]`;
      insertTokenAtCursor(token);
      setShowCreateTaskModal(false);
    },
    [insertTokenAtCursor]
  );
  const closeSlashMenu = useCallback(() => setSlashMenuOpen(false), []);

  const openSlashMenu = useCallback(() => {
    if (!textareaRef.current || !inputFooterRef.current) {
      return;
    }
    const top = Math.max(
      0,
      (textareaRef.current.offsetTop || 0) -
        textareaRef.current.offsetHeight -
        12
    );
    const left = (textareaRef.current.offsetLeft || 0) + 16;
    setSlashMenuPosition({ top, left });
    setSlashMenuOpen(true);
  }, []);

  const handleSlashCommandSelect = useCallback(
    async (command: SlashCommand) => {
      closeSlashMenu();
      try {
        const projectsList = await ensureProjectsIndex();
        if (command.id === "insert-task" || command.id === "create-task-op") {
          if ((projectsList?.length ?? 0) === 0) {
            showInlineNotice("No projects available. Create one first.");
            return;
          }
          if (command.id === "insert-task") {
            openReferenceSearch();
            return;
          }
          setShowCreateTaskModal(true);
        }
      } catch (error) {
        console.error("Slash command preparation failed:", error);
        showInlineNotice("Failed to load workspace context. Try again.");
      }
    },
    [closeSlashMenu, ensureProjectsIndex, openReferenceSearch, showInlineNotice]
  );

  const operationApi = useMemo<OperationApiGroup | null>(() => {
    if (mode === "workroom" && taskId) {
      return {
        suggest: (body: { message?: string; thread_id?: string }) =>
          api.assistantSuggestForTask(taskId, body),
        approve: (body: { operation: any }) =>
          api.assistantApproveForTask(taskId, body),
        edit: (body: { operation: any; edited_params: any }) =>
          api.assistantEditForTask(taskId, body),
        decline: (body: { operation: any }) =>
          api.assistantDeclineForTask(taskId, body),
        undo: (body: { operation: any; original_state?: any }) =>
          api.assistantUndoForTask(taskId, body),
      };
    }

    if (actionId) {
      return {
        suggest: (body: { message?: string; thread_id?: string }) =>
          api.assistantSuggestForAction(actionId, body),
        approve: (body: { operation: any }) =>
          api.assistantApproveForAction(actionId, body),
        edit: (body: { operation: any; edited_params: any }) =>
          api.assistantEditForAction(actionId, body),
        decline: (body: { operation: any }) =>
          api.assistantDeclineForAction(actionId, body),
        undo: (body: { operation: any; original_state?: any }) =>
          api.assistantUndoForAction(actionId, body),
      };
    }

    return null;
  }, [mode, taskId, actionId]);

  const runOperationApi = useCallback(
    async <T extends keyof OperationApiGroup>(
      action: T,
      payload: Parameters<OperationApiGroup[T]>[0]
    ) => {
      if (!operationApi) {
        console.warn("Assistant operations are unavailable for this chat.");
        return null;
      }
      try {
        const result = await operationApi[action](payload as any);
        return result;
      } catch (error) {
        console.error(`Failed to run operation API action '${action}':`, error);
        return {
          ok: false,
          error: (error as Error).message,
          status: (error as any)?.status,
          detail: (error as any)?.body,
        };
      }
    },
    [operationApi]
  );

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const inputFooterRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const typingStartRef = useRef<number | null>(null);
  const messagesRef = useRef<Message[]>([]);
  const selectionRef = useRef<{ start: number; end: number }>({
    start: 0,
    end: 0,
  });
  const noticeTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const [animatedMessageIds, setAnimatedMessageIds] = useState<Set<string>>(
    new Set()
  );
  const animatedRef = useRef<Set<string>>(new Set());
  const previousMessagesRef = useRef<Message[]>([]);
  const isInitialLoadRef = useRef<boolean>(true);
  const awaitingAssistantAfterTsRef = useRef<string | null>(null);
  const [activeAssistantId, setActiveAssistantId] = useState<string | null>(
    null
  );
  const typingSessionRef = useRef<{
    showTimerId: NodeJS.Timeout | null;
    clearTimerId: NodeJS.Timeout | null;
  }>({ showTimerId: null, clearTimerId: null });
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);

  const MIN_TYPING_DURATION = 500; // ms
  const ASSISTANT_START_DELAY_MS = 100; // ms

  const syncSelectionFromEvent = useCallback(
    (e: React.SyntheticEvent<HTMLTextAreaElement>) => {
      if (!e.currentTarget) return;
      selectionRef.current = {
        start: e.currentTarget.selectionStart ?? 0,
        end: e.currentTarget.selectionEnd ?? 0,
      };
    },
    []
  );

  // Bootstrap thread if needed (only if not provided and shouldFocus is true)
  // Note: ActionCard creates thread on expand, so this is mainly for edge cases
  useEffect(() => {
    if (!threadId && actionId && shouldFocus) {
      const bootstrapThread = async () => {
        try {
          // Get action title from queue or use a default
          const queueData = await api
            .queue()
            .catch(() => ({ ok: true, items: [] }));
          const action = (queueData as any)?.items?.find(
            (item: any) => item.action_id === actionId
          );
          const title = action?.preview || summary || "Action Chat";

          // Create thread with source_action_id
          const response = await api.createThreadFromAction(actionId, title);
          if (response?.ok && response?.thread?.id) {
            const newThreadId = response.thread.id;
            setThreadId(newThreadId);
            onThreadCreated?.(newThreadId);
          }
        } catch (err) {
          console.error("Failed to bootstrap thread:", err);
        }
      };
      bootstrapThread();
    }
  }, [threadId, actionId, onThreadCreated, shouldFocus, summary]);

  // Fetch messages
  const {
    data: threadData,
    mutate: mutateThread,
    isLoading: isLoadingThread,
  } = useSWR<ThreadResponse>(
    threadId ? [`thread`, threadId] : null,
    async () => {
      if (!threadId) {
        throw new Error("No thread ID");
      }
      const response = await api.getThread(threadId);
      if (!response) {
        // Fallback to empty structure if getThread returns null/undefined
        return {
          ok: true,
          thread: {
            id: threadId,
            messages: [],
          },
        } as ThreadResponse;
      }
      return response as ThreadResponse;
    },
    {
      refreshInterval: 5000, // Poll for new messages
      revalidateOnFocus: true,
      onError: (error: any) => {
        // SWR error handler - don't log 404s (expected) but log other errors
        if (error?.status !== 404 && !error?.message?.includes("404")) {
          console.warn("SWR error fetching thread:", error);
        }
      },
    }
  );

  // Reset messages when threadId changes to prevent cross-thread contamination
  useEffect(() => {
    if (threadId) {
      setMessages([]); // Clear messages when switching threads
    }
  }, [threadId]);

  // Helper function to create a normalized fingerprint for message content
  const fingerprintContent = useCallback((content: string): string => {
    return content.toLowerCase().trim().replace(/\s+/g, " "); // Collapse internal whitespace
  }, []);

  // Update messages when thread data changes - merge instead of replace
  // Only process if this is the current thread to prevent cross-thread contamination
  useEffect(() => {
    if (threadData?.thread?.messages && threadData.thread.id === threadId) {
      setMessages((prev) => {
        const backendMessages = threadData.thread.messages;
        // Merge: keep optimistic messages that aren't confirmed yet
        const optimisticMessages = prev.filter((msg) => msg.optimistic);
        const confirmedIds = new Set(backendMessages.map((m) => m.id));

        // Build fingerprint-based deduplication for user messages
        // Count backend user messages by fingerprint
        const backendUserCounts = new Map<string, number>();
        backendMessages.forEach((msg: any) => {
          const content = msg.content || msg.text || "";
          const role = msg.role === "user" ? "user" : "assistant";
          if (role === "user") {
            const fingerprint = fingerprintContent(content);
            backendUserCounts.set(
              fingerprint,
              (backendUserCounts.get(fingerprint) || 0) + 1
            );
          }
        });

        // Group optimistic user messages by fingerprint
        const optimisticUserBuckets = new Map<string, Message[]>();
        optimisticMessages.forEach((msg) => {
          if (msg.role === "user") {
            const fingerprint = fingerprintContent(msg.content);
            if (!optimisticUserBuckets.has(fingerprint)) {
              optimisticUserBuckets.set(fingerprint, []);
            }
            optimisticUserBuckets.get(fingerprint)!.push(msg);
          }
        });

        // Remove matched optimistics: for each fingerprint, remove up to backendUserCounts[fingerprint] messages
        const matchedOptimisticIds = new Set<string>();
        optimisticUserBuckets.forEach((bucket, fingerprint) => {
          const backendCount = backendUserCounts.get(fingerprint) || 0;
          // Sort by timestamp (oldest first) to match oldest optimistics first
          const sortedBucket = [...bucket].sort(
            (a, b) => new Date(a.ts).getTime() - new Date(b.ts).getTime()
          );
          // Mark up to backendCount messages as matched
          for (
            let i = 0;
            i < Math.min(backendCount, sortedBucket.length);
            i++
          ) {
            matchedOptimisticIds.add(sortedBucket[i].id);
          }
        });

        // Filter optimistics: exclude those matched by ID or by fingerprint count
        const stillOptimistic = optimisticMessages.filter((msg) => {
          // Keep if ID is confirmed (already handled by backend)
          if (confirmedIds.has(msg.id)) {
            return false;
          }
          // For user messages, exclude if matched by fingerprint count
          if (msg.role === "user" && matchedOptimisticIds.has(msg.id)) {
            return false;
          }
          // Keep all other optimistics (assistant messages, unmatched user messages)
          return true;
        });

        // Ensure roles are correct - fix any role mismatches
        const correctedBackendMessages = backendMessages.map((msg: any) => {
          // Normalize message structure - ensure it has content, role, id, ts
          const metadata =
            msg.metadata && typeof msg.metadata === "object"
              ? msg.metadata
              : {};
          const surfacesSource =
            msg.surfaces ??
            (Array.isArray(metadata?.surfaces) ? metadata.surfaces : metadata?.surfaces);
          const parsedSurfaces =
            msg.role === "assistant"
              ? parseInteractiveSurfaces(surfacesSource)
              : [];
          const normalizedMsg = {
            id: msg.id || String(Math.random()),
            role: (msg.role === "user" ? "user" : "assistant") as
              | "user"
              | "assistant",
            content: msg.content || msg.text || "",
            ts: msg.ts || msg.created_at || new Date().toISOString(),
            embeds: msg.embeds || [],
            surfaces: parsedSurfaces.length ? parsedSurfaces : undefined,
          };

          // If message was sent by user (check by matching content with optimistic), ensure role is user
          const matchingOptimistic = optimisticMessages.find(
            (opt) =>
              fingerprintContent(opt.content) ===
                fingerprintContent(normalizedMsg.content) && opt.role === "user"
          );
          if (matchingOptimistic) {
            return { ...normalizedMsg, role: "user" as const };
          }
          return normalizedMsg;
        });

        // Combine backend messages with still-optimistic ones
        const merged = [...correctedBackendMessages, ...stillOptimistic];
        // Sort by timestamp
        return merged.sort(
          (a, b) => new Date(a.ts).getTime() - new Date(b.ts).getTime()
        );
      });
    }
  }, [threadData, threadId, fingerprintContent]);

  // Keep messagesRef in sync with messages state
  useEffect(() => {
    messagesRef.current = messages;
  }, [messages]);

  // Track animated message IDs to prevent replay and enforce serial sequencing
  // Only the newest assistant message should animate; older ones are marked complete immediately
  useEffect(() => {
    const previousMessageIds = new Set(
      previousMessagesRef.current.map((m) => m.id)
    );
    const isInitialLoad = previousMessagesRef.current.length === 0;

    // Find all assistant messages
    const assistantMessages = messages.filter((m) => m.role === "assistant");

    // On initial load, mark all messages as seen (don't animate)
    if (isInitialLoad) {
      messages.forEach((m) => {
        if (m.role === "assistant") {
          animatedRef.current.add(m.id);
        }
      });
      isInitialLoadRef.current = false;
      previousMessagesRef.current = messages;
      return;
    }

    // Find the newest assistant message (by timestamp, or last in array if timestamps equal)
    let newestAssistantId: string | null = null;
    if (assistantMessages.length > 0) {
      // Sort by timestamp descending, then by array index descending as tiebreaker
      const sorted = [...assistantMessages].sort((a, b) => {
        const timeDiff = new Date(b.ts).getTime() - new Date(a.ts).getTime();
        if (timeDiff !== 0) return timeDiff;
        // If timestamps equal, use array position (later messages come after)
        const aIndex = messages.findIndex((m) => m.id === a.id);
        const bIndex = messages.findIndex((m) => m.id === b.id);
        return bIndex - aIndex;
      });
      newestAssistantId = sorted[0].id;
    }

    // Enforce serial sequencing: mark all assistant messages except the newest as completed
    messages.forEach((m) => {
      if (m.role === "assistant") {
        // If this is not the newest assistant message, mark it as completed immediately
        if (newestAssistantId && m.id !== newestAssistantId) {
          animatedRef.current.add(m.id);
        }
        // If message was already in previous render, mark it as seen (don't animate)
        else if (previousMessageIds.has(m.id)) {
          animatedRef.current.add(m.id);
        }
      }
    });

    // Update active assistant ID state
    setActiveAssistantId(newestAssistantId);

    // Update previous messages ref for next render
    previousMessagesRef.current = messages;
  }, [messages]);

  const shouldAnimate = useCallback(
    (msg: Message) => {
      // Only animate assistant messages that haven't been seen before
      // User messages always display in full
      if (msg.role === "user") {
        return false;
      }
      // Only animate if this is the active assistant message and hasn't been marked as seen
      return (
        msg.role === "assistant" &&
        !animatedRef.current.has(msg.id) &&
        activeAssistantId === msg.id
      );
    },
    [activeAssistantId]
  );

  const scheduleThreadRefreshForChat = useCallback(() => {
    if (!threadId) {
      return;
    }
    setTimeout(() => {
      mutateThread().catch((err) => {
        console.warn("Failed to refetch thread after ChatOp:", err);
      });
    }, 500);
  }, [threadId, mutateThread]);

  // Helper to clear typing with minimum duration
  const clearTyping = useCallback(() => {
    const elapsed = typingStartRef.current
      ? Date.now() - typingStartRef.current
      : 0;
    const remaining = Math.max(0, MIN_TYPING_DURATION - elapsed);
    setTimeout(() => {
      setIsTyping(false);
      typingStartRef.current = null;
    }, remaining);
  }, []);

  const stampOperations = useCallback(
    (ops?: SummaryOperation[] | OperationRecord[]) =>
      (ops ?? []).map((op) =>
        (op as OperationRecord).localId
          ? (op as OperationRecord)
          : {
              ...(op as SummaryOperation),
              localId: generateOperationLocalId(),
            }
      ),
    []
  );

  const applyOperationsResponse = useCallback(
    (response?: Partial<OperationsState>) => {
      if (!response) return;
      setOperationsState({
        applied: stampOperations(response.applied as SummaryOperation[]),
        pending: stampOperations(response.pending as SummaryOperation[]),
        errors: formatOperationErrors(response.errors),
      });
      clearTyping();
    },
    [stampOperations, clearTyping]
  );

  const updateOperationsState = useCallback(
    (mutator: (prev: OperationsState) => OperationsState) => {
      setOperationsState((prev) => mutator(prev));
    },
    []
  );

  const pushOperationError = useCallback(
    (message: string, meta?: { op?: string; params?: Record<string, any> }) => {
      setOperationsState((prev) => ({
        ...prev,
        errors: [
          ...prev.errors,
          {
            id: generateOperationLocalId(),
            message,
            op: meta?.op,
            params: meta?.params,
          },
        ],
      }));

      setMessages((prev) => [
        ...prev,
        {
          ...createAssistantMessage(message),
          error: true,
          errorMessage: message,
        },
      ]);
    },
    [setMessages]
  );

  const dismissOperationError = useCallback(
    (id: string) => {
      updateOperationsState((prev) => ({
        ...prev,
        errors: prev.errors.filter((err) => err.id !== id),
      }));
    },
    [updateOperationsState]
  );

  useEffect(() => {
    onOperationsUpdate?.(operationsState);
  }, [operationsState, onOperationsUpdate]);

  // Detect first assistant reply after user message and clear typing indicator
  useEffect(() => {
    if (!awaitingAssistantAfterTsRef.current || !isTyping) {
      return;
    }

    const awaitingTs = awaitingAssistantAfterTsRef.current;
    // Find first assistant message after the user message timestamp
    const firstAssistantReply = messages.find(
      (msg) =>
        msg.role === "assistant" &&
        !msg.optimistic &&
        new Date(msg.ts).getTime() > new Date(awaitingTs).getTime() &&
        !animatedRef.current.has(msg.id) // Not yet handled
    );

    if (firstAssistantReply) {
      // Clear typing indicator just before assistant animation starts
      // Schedule clear at max(0, ASSISTANT_START_DELAY_MS - 100) which is usually 0
      const clearDelay = Math.max(0, ASSISTANT_START_DELAY_MS - 100);

      // Cancel any existing clear timer
      if (typingSessionRef.current.clearTimerId) {
        clearTimeout(typingSessionRef.current.clearTimerId);
      }

      typingSessionRef.current.clearTimerId = setTimeout(() => {
        clearTyping();
        awaitingAssistantAfterTsRef.current = null;
        typingSessionRef.current.clearTimerId = null;
      }, clearDelay);

      // Mark this assistant message as handled to avoid re-triggering
      animatedRef.current.add(firstAssistantReply.id);
    }
  }, [messages, isTyping, clearTyping]);

  // Cleanup timers on unmount
  useEffect(() => {
    return () => {
      if (typingSessionRef.current.showTimerId) {
        clearTimeout(typingSessionRef.current.showTimerId);
      }
      if (typingSessionRef.current.clearTimerId) {
        clearTimeout(typingSessionRef.current.clearTimerId);
      }
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, []);

  useEffect(() => {
    return () => {
      if (noticeTimeoutRef.current) {
        clearTimeout(noticeTimeoutRef.current);
      }
    };
  }, []);

  // Load draft from cache
  useEffect(() => {
    if (draftCache[actionId]) {
      updateMessageValue(draftCache[actionId]);
    }
  }, [actionId, draftCache, updateMessageValue]);

  // Auto-scroll to bottom - scroll the messages container, not the page
  useEffect(() => {
    if (messagesContainerRef.current && messagesEndRef.current) {
      const container = messagesContainerRef.current;
      const scrollToBottom = () => {
        container.scrollTop = container.scrollHeight;
      };
      // Use requestAnimationFrame to ensure DOM is updated
      requestAnimationFrame(() => {
        scrollToBottom();
      });
    }
  }, [messages, isTyping]);

  // Focus textarea when shouldFocus is true
  useEffect(() => {
    if (shouldFocus && textareaRef.current) {
      textareaRef.current.focus();
    }
  }, [shouldFocus]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(
        textareaRef.current.scrollHeight,
        96
      )}px`;
    }
  }, [message]);

  const handleSend = useCallback(async () => {
    if (!message.trim()) {
      return;
    }

    // Ensure thread exists before sending
    let currentThreadId: string | null = threadId;
    if (!currentThreadId) {
      console.warn("No thread ID, attempting to create thread before sending");
      try {
        const threadResponse = await api.createThreadFromAction(
          actionId,
          summary || "Action Chat"
        );
        if (threadResponse?.ok && threadResponse?.thread?.id) {
          currentThreadId = threadResponse.thread.id;
          setThreadId(currentThreadId);
          // currentThreadId is guaranteed to be string here after assignment
          if (currentThreadId) {
            onThreadCreated?.(currentThreadId);
          }
        } else {
          throw new Error("Failed to create thread");
        }
      } catch (err) {
        console.error("Failed to create thread:", err);
        return;
      }
    }

    // Double-check threadId is valid before proceeding
    if (!currentThreadId) {
      console.error("Thread ID is still null after creation attempt");
      return;
    }

    // Verify thread exists before sending (proactive check)
    try {
      if (!currentThreadId) {
        throw new Error("Thread ID is null");
      }
      const threadCheck = await api.getThread(currentThreadId);
      if (!threadCheck?.ok || !threadCheck?.thread) {
        console.warn(
          `Thread ${currentThreadId} not found, recreating before send`
        );
        // Recreate thread
        const threadResponse = await api.createThreadFromAction(
          actionId,
          summary || "Action Chat"
        );
        if (threadResponse?.ok && threadResponse?.thread?.id) {
          currentThreadId = threadResponse.thread.id;
          setThreadId(currentThreadId);
          if (currentThreadId) {
            onThreadCreated?.(currentThreadId);
          }
        } else {
          throw new Error("Failed to recreate thread during verification");
        }
      }
    } catch (err: any) {
      // If verification fails, try to recreate thread
      if (
        err?.message?.includes("404") ||
        err?.message?.includes("Not Found")
      ) {
        console.warn(
          `Thread verification failed for ${currentThreadId}, recreating:`,
          err
        );
        try {
          if (!currentThreadId) {
            throw new Error("Thread ID is null");
          }
          const threadResponse = await api.createThreadFromAction(
            actionId,
            summary || "Action Chat"
          );
          if (threadResponse?.ok && threadResponse?.thread?.id) {
            currentThreadId = threadResponse.thread.id;
            setThreadId(currentThreadId);
            if (currentThreadId) {
              onThreadCreated?.(currentThreadId);
            }
          }
        } catch (recreateErr) {
          console.error(
            "Failed to recreate thread during verification:",
            recreateErr
          );
          return;
        }
      } else {
        console.warn("Thread verification error (non-404), proceeding:", err);
        // Continue with send attempt even if verification fails
      }
    }

    const tempId = `temp-${Date.now()}`;
    const messageContent = message.trim();
    const optimisticMessage: Message = {
      id: tempId,
      role: "user",
      content: messageContent,
      ts: new Date().toISOString(),
      optimistic: true,
    };

    // Optimistic update
    setMessages((prev) => [...prev, optimisticMessage]);
    updateMessageValue("");

    // Cancel any existing typing session timers
    if (typingSessionRef.current.showTimerId) {
      clearTimeout(typingSessionRef.current.showTimerId);
      typingSessionRef.current.showTimerId = null;
    }
    if (typingSessionRef.current.clearTimerId) {
      clearTimeout(typingSessionRef.current.clearTimerId);
      typingSessionRef.current.clearTimerId = null;
    }

    // Calculate delay based on message length (500-2000ms)
    // Use word count as proxy for message complexity
    const wordCount = messageContent
      .split(/\s+/)
      .filter((w) => w.length > 0).length;
    const charCount = messageContent.length;
    // Use a combination: base 500ms + ~50ms per word (capped at 2000ms)
    const showDelayMs = Math.min(Math.max(500 + wordCount * 50, 500), 2000);

    // Set awaiting timestamp for assistant reply detection
    awaitingAssistantAfterTsRef.current = optimisticMessage.ts;

    // Schedule typing indicator to show after delay
    typingSessionRef.current.showTimerId = setTimeout(() => {
      setIsTyping(true);
      typingStartRef.current = Date.now();
      typingSessionRef.current.showTimerId = null;
    }, showDelayMs);

    // Restore focus after state update
    requestAnimationFrame(() => {
      textareaRef.current?.focus();
    });

    // Retry logic with exponential backoff
    const MAX_RETRIES = 2;
    let retryCount = 0;
    let lastError: any = null;

    const attemptSend = async (threadIdToUse: string): Promise<boolean> => {
      try {
        if (!api.sendMessage) {
          throw new Error("sendMessage API method not available");
        }

        console.log(`Attempting to send message to thread ${threadIdToUse}`);
        const response = await api.sendMessage(threadIdToUse, {
          role: "user",
          content: messageContent,
        });

        if (response?.ok && response?.message) {
          // Success - replace optimistic message with real one
          console.log(`Message sent successfully to thread ${threadIdToUse}`);
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === tempId
                ? { ...response.message, optimistic: false, role: "user" }
                : msg
            )
          );

          // Debounce assistant-suggest: clear existing timer and set new one
          // This ensures we only trigger after user stops sending messages
          if (debounceTimerRef.current) {
            clearTimeout(debounceTimerRef.current);
            debounceTimerRef.current = null;
          }

          // Set debounced trigger for assistant-suggest (2.5 second delay)
          debounceTimerRef.current = setTimeout(async () => {
            debounceTimerRef.current = null;

            // Only trigger if we have a thread_id
            if (!currentThreadId) {
              return;
            }

            if (operationApi) {
              try {
                const suggestResponse = await operationApi.suggest({
                  thread_id: currentThreadId,
                });
                if (suggestResponse?.ok) {
                  applyOperationsResponse(suggestResponse);

                  const hasChatOp = (suggestResponse.applied || []).some(
                    (op: any) => op.op === "chat"
                  );
                  if (hasChatOp) {
                    scheduleThreadRefreshForChat();
                  }
                }
              } catch (err) {
                console.warn("Failed to get assistant suggestions:", err);
              }
            }
          }, 2500); // 2.5 second debounce

          // Typing indicator already shown, just ensure it's still active
          // Refetch to get assistant response (with error handling)
          setTimeout(() => {
            try {
              mutateThread().catch((err) => {
                console.warn("Failed to refetch thread after send:", err);
                clearTyping();
              });
            } catch (err) {
              console.warn("Error calling mutateThread:", err);
              clearTyping();
            }
          }, 1000);
          return true;
        } else {
          // Structured error response
          console.warn(`Send failed for thread ${threadIdToUse}:`, response);
          lastError = response;
          return false;
        }
      } catch (err: any) {
        console.warn(`Send exception for thread ${threadIdToUse}:`, err);
        lastError = err;
        return false;
      }
    };

    // Initial send attempt
    let sendSuccess = false;
    if (!currentThreadId) {
      console.error("Cannot send: thread ID is null");
      return;
    }
    sendSuccess = await attemptSend(currentThreadId);

    // Retry logic: if 404, recreate thread and retry
    while (!sendSuccess && retryCount < MAX_RETRIES) {
      retryCount++;
      const backoffDelay = Math.min(100 * Math.pow(2, retryCount - 1), 500); // 100ms, 200ms max

      console.log(
        `[Retry ${retryCount}/${MAX_RETRIES}] Message send failed for thread ${currentThreadId}, error:`,
        lastError?.error || lastError?.message,
        `Retrying in ${backoffDelay}ms...`
      );

      // Check if error is 404 (thread not found)
      if (
        lastError?.error === "404 Not Found" ||
        lastError?.message?.includes("404")
      ) {
        // In workroom mode, don't try to recreate threads - they're managed by tasks
        if (mode === "workroom") {
          console.warn(
            `[Retry ${retryCount}/${MAX_RETRIES}] Thread ${currentThreadId} not found in workroom mode - skipping recreation`
          );
          break; // Exit retry loop - thread should be created via task chat creation
        }

        // Recreate thread before retry (only in non-workroom mode)
        try {
          console.log(
            `[Retry ${retryCount}/${MAX_RETRIES}] Recreating thread ${currentThreadId} before retry`
          );
          const threadResponse = await api.createThreadFromAction(
            actionId,
            summary || "Action Chat"
          );
          if (threadResponse?.ok && threadResponse?.thread?.id) {
            const newThreadId = threadResponse.thread.id;
            console.log(
              `[Retry ${retryCount}/${MAX_RETRIES}] Thread recreated: ${newThreadId}`
            );
            currentThreadId = newThreadId;
            setThreadId(newThreadId);
            onThreadCreated?.(newThreadId);

            // Wait for backoff delay
            await new Promise((resolve) => setTimeout(resolve, backoffDelay));

            // Retry send with new thread ID
            sendSuccess = await attemptSend(newThreadId);
            if (sendSuccess) {
              console.log(
                `[Retry ${retryCount}/${MAX_RETRIES}] Retry successful`
              );
              break; // Success, exit retry loop
            }
          } else {
            throw new Error("Failed to recreate thread");
          }
        } catch (err) {
          console.error(
            `[Retry ${retryCount}/${MAX_RETRIES}] Failed to recreate thread:`,
            err
          );
          // Continue to next retry or mark as final failure
        }
      } else {
        // Non-404 error - wait and retry with same thread ID
        await new Promise((resolve) => setTimeout(resolve, backoffDelay));
        if (currentThreadId) {
          sendSuccess = await attemptSend(currentThreadId);
        } else {
          console.error("Thread ID became null during retry");
          break;
        }
      }
    }

    // Final failure handling
    if (!sendSuccess) {
      console.error(
        `[Final Failure] Failed to send message after ${
          retryCount + 1
        } attempts.`,
        `Thread ID: ${currentThreadId},`,
        `Action ID: ${actionId},`,
        `Error:`,
        lastError
      );
      // Mark as error with retry option
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === tempId
            ? {
                ...msg,
                error: true,
                optimistic: false,
                retryable: true,
                errorMessage: lastError?.message || "Failed to send message",
              }
            : msg
        )
      );
      // Clear typing indicator on failure
      if (typingStartRef.current) {
        clearTyping();
      }
      // Clear awaiting timestamp since we're not expecting a reply
      awaitingAssistantAfterTsRef.current = null;
    }
    // Note: Typing indicator remains active on success - it will be cleared when assistant message arrives
  }, [
    message,
    threadId,
    actionId,
    mutateThread,
    summary,
    onThreadCreated,
    clearTyping,
  ]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      e.stopPropagation();
      if (e.key === "/" && !e.shiftKey && !isSlashMenuOpen) {
        openSlashMenu();
      }
      if (isSlashMenuOpen && e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        return;
      }
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSend();
        return;
      }
      if (e.key === "Escape") {
        if (isSlashMenuOpen) {
          e.preventDefault();
          closeSlashMenu();
          return;
        }
        if (contextExpanded) {
          setContextExpanded(false);
        }
      }
    },
    [
      handleSend,
      contextExpanded,
      isSlashMenuOpen,
      openSlashMenu,
      closeSlashMenu,
    ]
  );

  const handleContextToggle = useCallback(() => {
    setContextExpanded((prev) => !prev);
  }, []);

  const handleRetryMessage = useCallback(
    async (messageId: string) => {
      const msgToRetry = messagesRef.current.find((m) => m.id === messageId);
      if (!msgToRetry || !msgToRetry.error || !msgToRetry.retryable) {
        return;
      }

      // Remove error state
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === messageId
            ? {
                ...msg,
                error: false,
                retryable: false,
                errorMessage: undefined,
                optimistic: true,
              }
            : msg
        )
      );

      // Attempt to resend
      const currentThreadId = threadId;
      if (!currentThreadId) {
        console.error("Cannot retry: no thread ID");
        return;
      }

      // Set awaiting timestamp for assistant reply detection
      awaitingAssistantAfterTsRef.current = new Date().toISOString();

      setIsTyping(true);
      typingStartRef.current = Date.now();
      try {
        const response = await api.sendMessage(currentThreadId, {
          role: msgToRetry.role,
          content: msgToRetry.content,
        });

        if (response?.ok && response?.message) {
          // Replace with successful message
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === messageId
                ? {
                    ...response.message,
                    optimistic: false,
                    role: msgToRetry.role,
                  }
                : msg
            )
          );
          // Show typing indicator for assistant response
          setIsTyping(true);
          typingStartRef.current = Date.now();
          // Refetch to get assistant response
          setTimeout(() => {
            mutateThread().catch((err) => {
              console.warn("Failed to refetch thread after retry:", err);
              clearTyping();
            });
          }, 1000);
        } else {
          // Mark as error again
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === messageId
                ? {
                    ...msg,
                    error: true,
                    optimistic: false,
                    retryable: true,
                    errorMessage: response?.message || "Failed to send message",
                  }
                : msg
            )
          );
          clearTyping();
          awaitingAssistantAfterTsRef.current = null;
        }
      } catch (err: any) {
        console.error("Retry failed:", err);
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === messageId
              ? {
                  ...msg,
                  error: true,
                  optimistic: false,
                  retryable: true,
                  errorMessage: err?.message || "Failed to send message",
                }
              : msg
          )
        );
        clearTyping();
        awaitingAssistantAfterTsRef.current = null;
      } finally {
        // clearTyping handles minimum duration, but only if isTyping is still true
        if (isTyping) {
          // If we're still typing, clearTyping will handle it
        } else {
          clearTyping();
        }
      }
    },
    [threadId, mutateThread, isTyping, clearTyping]
  );

  const handleSurfaceInvokeOp = useCallback(
    async (opToken: string, options?: { confirm?: boolean }) => {
      if (options?.confirm && !window.confirm("Are you sure you want to run this action?")) {
        return;
      }
      const operation = convertOpTokenToOperation(opToken);
      if (!operation) {
        showInlineNotice("Couldn't run that action. Please try again.");
        return;
      }
      try {
        const result = await runOperationApi("approve", {
          operation: sanitizeOperationForApi(operation, { forceCurrentProject }),
        });
        if (!result?.ok) {
          const errorDetail =
            result?.detail?.assistant_message ||
            result?.detail?.detail ||
            result?.detail ||
            result?.error ||
            "Failed to run that action.";
          pushOperationError(errorDetail, { op: operation.op, params: operation.params });
          return;
        }
        scheduleThreadRefreshForChat();
      } catch (err: any) {
        pushOperationError(
          err?.message || "Failed to run that action.",
          { op: operation.op, params: operation.params }
        );
      }
    },
    [
      runOperationApi,
      forceCurrentProject,
      showInlineNotice,
      pushOperationError,
      scheduleThreadRefreshForChat,
    ]
  );

  const handleSurfaceNavigate = useCallback(
    (nav: SurfaceNavigateTo) => {
      switch (nav.destination) {
        case "workroom_task":
          onOpenWorkroom?.();
          break;
        case "hub_queue":
          window.location.hash = "#queue";
          break;
        case "hub":
          window.location.hash = `#${nav.section ?? "today"}`;
          break;
        case "calendar_event":
          showInlineNotice("Opening calendar events is not yet supported in this build.");
          break;
        default:
          showInlineNotice("Navigation target not supported yet.");
      }
    },
    [onOpenWorkroom, showInlineNotice]
  );

  const formatTimestamp = useCallback((ts: string) => {
    const date = new Date(ts);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
    return date.toLocaleDateString();
  }, []);

  // Group messages by time delta only (Fluent UI pattern)
  // All messages within 5 minutes are grouped together regardless of sender
  const GROUP_TIME_DELTA_MS = 5 * 60 * 1000; // 5 minutes

  const groupMessages = (
    messages: Message[]
  ): Array<Message & { isGroupStart: boolean; isGroupEnd: boolean }> => {
    if (messages.length === 0) return [];

    return messages.map((msg, index) => {
      const prevMsg = index > 0 ? messages[index - 1] : null;
      const nextMsg = index < messages.length - 1 ? messages[index + 1] : null;

      const msgTime = new Date(msg.ts).getTime();
      const prevTime = prevMsg ? new Date(prevMsg.ts).getTime() : null;
      const nextTime = nextMsg ? new Date(nextMsg.ts).getTime() : null;

      // Start of group if: first message OR time gap > delta
      const isGroupStart =
        !prevMsg ||
        (prevTime !== null && msgTime - prevTime > GROUP_TIME_DELTA_MS);

      // End of group if: last message OR next message gap > delta
      const isGroupEnd =
        !nextMsg ||
        (nextTime !== null && nextTime - msgTime > GROUP_TIME_DELTA_MS);

      return { ...msg, isGroupStart, isGroupEnd };
    });
  };

  const contextSummary = meta
    ? [
        meta.from && `From: ${meta.from}`,
        meta.threadLen !== undefined && `Thread: ${meta.threadLen}`,
        meta.lastAt && `Last: ${formatTimestamp(meta.lastAt)}`,
      ]
        .filter(Boolean)
        .join(" • ")
    : summary || "No context available";

  // Memoize grouped messages to prevent recreation on every render
  const groupedMessages = useMemo(() => groupMessages(messages), [messages]);

  const latestAssistantSurfaces = useMemo(() => {
    for (let i = messages.length - 1; i >= 0; i -= 1) {
      const candidate = messages[i];
      if (candidate.role === "assistant" && candidate.surfaces?.length) {
        return candidate.surfaces;
      }
    }
    return null;
  }, [messages]);

  const hideActionSummaryForSurfaces =
    (latestAssistantSurfaces?.some((surface) => surface.kind === "triage_table_v1") ??
      false) && !hasErrors;

  const shouldShowActionSummary =
    !hideActionSummaryForSurfaces &&
    (appliedOps.length > 0 || pendingOps.length > 0 || hasErrors);

  // Stable callback for embed updates
  const handleEmbedUpdate = useCallback(
    (messageId: string, updatedEmbed: any) => {
      setMessages((prev) =>
        prev.map((m) => {
          if (m.id !== messageId) return m;
          const embedId = updatedEmbed.id;
          return {
            ...m,
            embeds: m.embeds?.map((e: any) =>
              e.id === embedId ? updatedEmbed : e
            ) || [updatedEmbed],
          };
        })
      );
    },
    []
  );

  // Precompute message views with all data needed for rendering
  const messageViews = useMemo(() => {
    if (groupedMessages.length === 0) return [];

    return groupedMessages.map((msg, index) => {
      const isGrouped = !msg.isGroupStart;
      const showTimestamp = msg.isGroupEnd;

      // Check if role changed for visual spacing
      const prevMsg = index > 0 ? groupedMessages[index - 1] : null;
      const roleChanged = prevMsg && prevMsg.role !== msg.role;

      // Add margin-top for spacing: larger gap when role changes, tighter within same role
      const marginTop = roleChanged ? "mt-4" : isGrouped ? "mt-1" : "mt-2";

      // Precompute timestamp label
      const timestampLabel = formatTimestamp(msg.ts);

      // Compute shouldAnimate - only animate if not initial load, not already seen, and is the active assistant message
      const shouldAnimate =
        msg.role === "assistant" &&
        !isInitialLoadRef.current &&
        !animatedRef.current.has(msg.id) &&
        activeAssistantId === msg.id;

      // Set startDelayMs for assistant messages that should animate
      const startDelayMs =
        shouldAnimate && msg.role === "assistant"
          ? ASSISTANT_START_DELAY_MS
          : 0;

      return {
        id: msg.id,
        role: msg.role,
        content: msg.content,
        embeds: msg.embeds,
        surfaces: msg.surfaces,
        marginTop,
        timestampLabel,
        showTimestamp,
        shouldAnimate,
        startDelayMs,
        error: msg.error,
        retryable: msg.retryable,
        errorMessage: msg.errorMessage,
      } as MessageView;
    });
  }, [groupedMessages, formatTimestamp, activeAssistantId]);

  const containerStyle = useMemo(() => {
    return { height: "100%", minHeight: 0 };
  }, []);

  return (
    <>
      <style>{scrollbarStyles}</style>
      <div
        ref={containerRef}
        className="flex flex-col h-full min-h-0 bg-white rounded-lg p-4 relative"
        style={containerStyle}
        onClick={(e) => e.stopPropagation()}
        onMouseDown={(e) => e.stopPropagation()}
      >
        {/* Context Accordion - Header (hidden in workroom mode) */}
        {mode !== "workroom" && (
          <div className="flex-shrink-0 mb-4 bg-white">
            <div className="rounded-lg border border-slate-200 overflow-hidden">
              <div className="flex items-center gap-2">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleContextToggle();
                  }}
                  className="flex-1 flex items-center justify-between gap-1.5 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-slate-300 rounded-md transition-colors"
                  aria-expanded={contextExpanded}
                >
                  <div className="flex items-center gap-1.5">
                    <ChevronDown24Regular
                      className={`w-4 h-4 transition-transform duration-200 ${
                        contextExpanded ? "rotate-180" : ""
                      }`}
                    />
                    <span>Context</span>
                  </div>
                  <div className="flex items-center gap-2 flex-1 ml-2">
                    <span className="text-xs text-slate-500 font-normal truncate">
                      {contextSummary}
                    </span>
                  </div>
                </button>
                {threadId && onOpenWorkroom && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onOpenWorkroom(threadId);
                    }}
                    className="text-xs text-blue-600 hover:text-blue-700 underline focus:outline-none focus:ring-2 focus:ring-blue-300 rounded px-2 py-2 whitespace-nowrap"
                  >
                    Open in Workroom
                  </button>
                )}
              </div>
              <div
                className={`overflow-hidden transition-all duration-200 ease-in-out ${
                  contextExpanded ? "max-h-64 opacity-100" : "max-h-0 opacity-0"
                }`}
              >
                <div className="px-3 py-2 border-t border-slate-200 bg-slate-50">
                  {summary && (
                    <div className="text-sm text-slate-600 mb-2">{summary}</div>
                  )}
                  {meta && (
                    <div className="text-xs text-slate-500 space-y-1">
                      {meta.from && <div>From: {meta.from}</div>}
                      {meta.threadLen !== undefined && (
                        <div>Thread length: {meta.threadLen} messages</div>
                      )}
                      {meta.lastAt && (
                        <div>Last activity: {formatTimestamp(meta.lastAt)}</div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Messages List - Scrollable */}
        <div
          ref={messagesContainerRef}
          role="log"
          aria-live="polite"
          data-testid="chat-messages-container"
          className="flex-1 min-h-0 relative overflow-y-auto overflow-x-hidden bg-white -mx-4 px-4 py-3 chat-scrollbar"
          style={{
            scrollBehavior: "smooth",
            scrollbarWidth: "thin",
            scrollbarColor: "#cbd5e1 #ffffff",
            overscrollBehavior: "contain",
          }}
        >
          {isLoadingThread && messages.length === 0 ? (
            <div className="text-sm text-slate-500 py-4 text-center">
              Loading messages...
            </div>
          ) : messages.length === 0 && !threadId ? (
            <div className="text-sm text-slate-500 py-4 text-center">
              Starting conversation...
            </div>
          ) : (
            <MessageList
              messageViews={messageViews}
              isTyping={isTyping}
              onRetryMessage={handleRetryMessage}
              onEmbedUpdate={handleEmbedUpdate}
              animatedRef={animatedRef}
              activeAssistantId={activeAssistantId}
              onInvokeSurfaceOp={handleSurfaceInvokeOp}
              onNavigateSurface={handleSurfaceNavigate}
            />
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Sticky Footer - Input + Action Summary */}
        <div
          ref={inputFooterRef}
          className="flex-shrink-0 sticky bottom-0 bg-white z-10 border-t border-slate-200 -mx-4 px-4 pt-4 pb-0 relative"
          data-testid="chat-input-footer"
        >
          {isSlashMenuOpen && (
            <SlashMenu
              commands={slashCommands}
              onSelect={handleSlashCommandSelect}
              onClose={closeSlashMenu}
              position={slashMenuPosition}
            />
          )}
          {isReferenceSearchOpen && (
            <ReferenceSearchPanel
              anchorRef={inputFooterRef}
              query={referenceQuery}
              onQueryChange={(value) => {
                setReferenceQuery(value);
                setReferenceActiveIndex(0);
              }}
              projectOptions={projectOptions}
              projectId={referenceProjectId}
              onProjectChange={(value) => {
                setReferenceProjectId(value);
                setReferenceActiveIndex(0);
              }}
              results={displayReferenceResults}
              loading={referenceLoading}
              onSelect={(task) => handleInsertTaskReference(task)}
              onClose={closeReferenceSearch}
              activeIndex={referenceActiveIndex}
              onActiveIndexChange={setReferenceActiveIndex}
            />
          )}
          {parsedTokens.length > 0 && (
            <div className="flex flex-wrap gap-2 pb-2">
              {parsedTokens.map((token, idx) => (
                <span
                  key={`${token.raw}-${idx}`}
                  className="inline-flex items-center gap-1 rounded-full bg-slate-100 text-slate-700 px-2 py-0.5 text-xs"
                >
                  <span>{token.label}</span>
                  <button
                    onClick={() => handleRemoveToken(token.raw)}
                    className="text-slate-500 hover:text-slate-900"
                    aria-label="Remove token"
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          )}
          {inlineNotice && (
            <div className="text-xs text-slate-500 pb-2">{inlineNotice}</div>
          )}
          {/* Input Row */}
          <div className="flex items-end gap-2 pb-4">
            <textarea
              ref={textareaRef}
              value={message}
              onChange={(e) => {
                updateMessageValue(e.target.value);
              }}
              onFocus={() => {
                onInputFocus?.();
              }}
              onMouseDown={(e) => e.stopPropagation()}
              onKeyDown={handleKeyDown}
              onKeyUp={syncSelectionFromEvent}
              onSelect={syncSelectionFromEvent}
              onClick={syncSelectionFromEvent}
              placeholder="Message Assistant"
              aria-label="Message Assistant"
              disabled={!threadId}
              className="w-full resize-none max-h-24 rounded-md border border-slate-300 focus:outline-none focus:ring-2 focus:ring-slate-300 px-3 py-2 text-sm"
              rows={1}
            />
            <button
              onClick={(e) => {
                e.stopPropagation();
                handleSend();
              }}
              disabled={!message.trim() || !threadId}
              className="text-slate-600 hover:text-slate-800 disabled:text-slate-300 disabled:cursor-not-allowed transition-colors focus:outline-none focus:ring-2 focus:ring-slate-300 rounded-md p-1.5"
              aria-label="Send message"
            >
              <Send24Regular className="w-5 h-5" />
            </button>
          </div>

          {/* Action Summary */}
          {shouldShowActionSummary && (
            <div className="border-t border-slate-200">
              {/* TODO(LucidWork Contract): ActionSummary will surface/edit explicit target IDs here. */}
              <ActionSummary
                appliedOps={appliedOps}
                pendingOps={pendingOps}
                trustMode={trustMode}
                errors={operationsState.errors}
                onDismissError={dismissOperationError}
                onApprove={async (op) => {
                  if (!op?.localId) {
                    console.warn(
                      "Cannot approve operation without localId:",
                      op
                    );
                    return;
                  }
                  console.log("Approving operation:", op);
                  try {
                    const sanitizedOp = sanitizeOperationForApi(op, {
                      forceCurrentProject,
                    });
                    console.log("Sanitized operation for API:", sanitizedOp);
                    const result = await runOperationApi("approve", {
                      operation: sanitizedOp,
                    });
                    console.log("Approve API result:", result);
                    if (!result?.ok) {
                      const errorDetail =
                        result?.detail?.detail ||
                        result?.detail ||
                        result?.result;
                      const detailMessage =
                        errorDetail?.assistant_message ||
                        errorDetail?.stock_message ||
                        errorDetail?.error ||
                        result?.error ||
                        "Failed to approve operation. Please try again.";
                      pushOperationError(detailMessage, {
                        op: op.op,
                        params: op.params,
                      });
                      return;
                    }

                    updateOperationsState((prev) => ({
                      ...prev,
                      pending: removeByLocalId(prev.pending, op.localId!),
                      applied: [...prev.applied, op as OperationRecord],
                    }));
                    if (op.op === "chat") {
                      scheduleThreadRefreshForChat();
                    }
                    clearTyping();
                  } catch (error) {
                    console.error("Failed to approve operation:", error);
                    pushOperationError(
                      (error as Error)?.message ||
                        "Failed to approve operation. Please try again.",
                      { op: op.op, params: op.params }
                    );
                  }
                }}
                onEdit={async (op) => {
                  if (!op?.localId) return;
                  // For now, edit is a simple prompt - in future could show a modal
                  const editedParams = prompt(
                    "Edit operation parameters (JSON):",
                    JSON.stringify(op.params, null, 2)
                  );
                  if (!editedParams) return;
                  try {
                    const parsedParams = JSON.parse(editedParams);
                    const result = await runOperationApi("edit", {
                      operation: sanitizeOperationForApi(op, {
                        forceCurrentProject,
                      }),
                      edited_params: parsedParams,
                    });
                    if (result?.ok) {
                      const editedOp = {
                        ...(op as OperationRecord),
                        params: parsedParams,
                      };
                      updateOperationsState((prev) => ({
                        ...prev,
                        pending: removeByLocalId(prev.pending, op.localId!),
                        applied: [...prev.applied, editedOp],
                      }));
                      if (op.op === "chat") {
                        scheduleThreadRefreshForChat();
                      }
                      clearTyping();
                    }
                  } catch (error) {
                    console.error("Failed to edit operation:", error);
                    alert("Invalid JSON. Please try again.");
                  }
                }}
                onDecline={async (op) => {
                  if (!op?.localId) return;
                  try {
                    await runOperationApi("decline", {
                      operation: sanitizeOperationForApi(op, {
                        forceCurrentProject,
                      }),
                    });
                    updateOperationsState((prev) => ({
                      ...prev,
                      pending: removeByLocalId(prev.pending, op.localId!),
                    }));
                    clearTyping();
                  } catch (error) {
                    console.error("Failed to decline operation:", error);
                  }
                }}
                onUndo={async (op) => {
                  if (!op?.localId) return;
                  try {
                    // Try to get original state from the operation result if available
                    const originalState = op.original_state;
                    const result = await runOperationApi("undo", {
                      operation: sanitizeOperationForApi(op, {
                        forceCurrentProject,
                      }),
                      original_state: originalState,
                    });
                    if (result?.ok) {
                      updateOperationsState((prev) => ({
                        ...prev,
                        applied: removeByLocalId(prev.applied, op.localId!),
                      }));
                      clearTyping();
                    }
                  } catch (error) {
                    console.error("Failed to undo operation:", error);
                  }
                }}
              />
            </div>
          )}
        </div>
      </div>
      {showCreateTaskModal && (
        <CreateTaskOpModal
          projects={projectOptions}
          initialProjectId={projectId}
          onSubmit={handleInsertCreateTaskOp}
          onClose={() => setShowCreateTaskModal(false)}
        />
      )}
    </>
  );
}

type ModalShellProps = {
  title: string;
  onClose: () => void;
  children: React.ReactNode;
};

function ModalShell({ title, onClose, children }: ModalShellProps) {
  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onClose();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 px-4"
      onClick={onClose}
    >
      <div
        role="dialog"
        aria-modal="true"
        className="bg-white rounded-xl shadow-xl w-full max-w-md p-4 relative"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-slate-900">{title}</h3>
          <button
            onClick={onClose}
            aria-label="Close"
            className="text-slate-500 hover:text-slate-900"
          >
            ×
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}

type ReferenceSearchPanelProps = {
  anchorRef: React.RefObject<HTMLDivElement | null>;
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

function ReferenceSearchPanel({
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
              {query
                ? "No matches yet. Keep typing."
                : "Start typing to search tasks."}
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

type CreateTaskOpModalProps = {
  projects: ProjectOption[];
  initialProjectId?: string | null;
  onSubmit: (payload: { projectId: string; title: string }) => void;
  onClose: () => void;
};

function CreateTaskOpModal({
  projects,
  initialProjectId,
  onSubmit,
  onClose,
}: CreateTaskOpModalProps) {
  const [projectId, setProjectId] = useState<string>(
    initialProjectId && projects.some((p) => p.id === initialProjectId)
      ? initialProjectId
      : projects[0]?.id || ""
  );
  const [title, setTitle] = useState("");

  useEffect(() => {
    if (
      initialProjectId &&
      projects.some((project) => project.id === initialProjectId)
    ) {
      setProjectId(initialProjectId);
    }
  }, [initialProjectId, projects]);

  return (
    <ModalShell title="Create task operation" onClose={onClose}>
      {projects.length === 0 ? (
        <p className="text-sm text-slate-600">
          No projects available. Create a project first.
        </p>
      ) : (
        <>
          <label className="text-xs text-slate-500 uppercase tracking-wide">
            Project
          </label>
          <select
            value={projectId}
            onChange={(e) => setProjectId(e.target.value)}
            className="mt-1 w-full border border-slate-300 rounded-md px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-slate-300"
          >
            {projects.map((project) => (
              <option key={project.id} value={project.id}>
                {project.title}
              </option>
            ))}
          </select>
          <label className="text-xs text-slate-500 uppercase tracking-wide mt-4 block">
            Task title
          </label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="mt-1 w-full border border-slate-300 rounded-md px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-slate-300"
            placeholder="e.g., Draft launch brief"
          />
          <button
            onClick={() => {
              if (!projectId || !title.trim()) return;
              onSubmit({ projectId, title: title.trim() });
            }}
            disabled={!projectId || !title.trim()}
            className="mt-4 inline-flex justify-center items-center px-3 py-2 rounded-md bg-slate-900 text-white text-sm disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Insert operation
          </button>
        </>
      )}
    </ModalShell>
  );
}
