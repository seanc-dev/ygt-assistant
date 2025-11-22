import { useState, useRef, useEffect, useCallback, memo, useMemo } from "react";
import {
  Send24Regular,
  ChevronDown24Regular,
  Add24Regular,
  Link24Regular,
  Note24Regular,
  Lightbulb24Regular,
  ShieldAdd24Regular,
  DocumentAdd24Regular,
} from "@fluentui/react-icons";
import { api } from "../../lib/api";
import { workroomApi } from "../../lib/workroomApi";
import { ActionEmbedComponent } from "../workroom/ActionEmbed";
import { ActionSummary } from "../shared/ActionSummary";
import type { LlmOperation as SummaryOperation } from "../shared/ActionSummary";
import { SlashMenu, SlashCommand } from "../ui/SlashMenu";
import { MessageList } from "./assistantChat/MessageList";
import { TokenOverlay } from "./assistantChat/TokenOverlay";
import { ReferenceSearchPanel } from "./assistantChat/ReferenceSearchPanel";
import { CreateTaskOpModal } from "./assistantChat/CreateTaskOpModal";
import { useChatThread } from "./assistantChat/useChatThread";
import {
  applyContextCommand,
  createEmptyContextSpace,
  type ContextSpace,
  type ContextCommandId,
  type UpdateContextSpace,
} from "./assistantChat/contextCommands";
import {
  parseInteractiveSurfaces,
  type InteractiveSurface,
  type ContextAddEntry,
  type SurfaceNavigateTo,
  type SurfaceKind,
} from "../../lib/llm/surfaces";
import type { WorkroomContext } from "../../lib/workroomContext";
import { filterSurfacesByWorkroomContext } from "../../lib/workroomSurfaceValidation";
import type {
  Message,
  MessageView,
  ParsedTokenChip,
  TokenSegment,
  ProjectOption,
  TaskOption,
  TaskSuggestion,
} from "./assistantChat/types";

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

type OperationRecord = SummaryOperation & {
  localId: string;
};

type OperationError = {
  id: string;
  message: string;
  op?: string;
  params?: Record<string, any>;
};

type OperationsState = {
  applied: OperationRecord[];
  pending: OperationRecord[];
  errors: OperationError[];
};

type AssistantChatMode = "workroom" | "default" | "hub_orientation";

const HUB_ALLOWED_SURFACES: SurfaceKind[] = ["what_next_v1", "priority_list_v1"];
const MAX_WORKROOM_SURFACES = 2;

export const shouldAllowSurfaces = (
  mode: AssistantChatMode,
  surfaceRenderAllowed?: boolean
) => surfaceRenderAllowed ?? mode !== "hub_orientation";

export function filterSurfacesForMode(
  surfaces: InteractiveSurface[] | undefined,
  mode: AssistantChatMode
): InteractiveSurface[] | undefined {
  if (!surfaces) return undefined;
  if (mode === "hub_orientation") {
    return surfaces.filter((surface) => HUB_ALLOWED_SURFACES.includes(surface.kind)).slice(0, 1);
  }
  return surfaces;
}

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

const convertOpTokenToOperation = (token: string): SummaryOperation | null => {
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

export const extractTokensFromMessage = (
  text: string
): ParsedTokenChip[] => {
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
    const start = match.index ?? 0;
    const end = start + raw.length;
    if (!raw) continue;
    if (kind === "ref") {
      const refType = data.type || "ref";
      const name = data.name || data.id || "";
      tokens.push({
        raw,
        kind,
        label: `${refType}: ${name || "unnamed"}`,
        start,
        end,
        data,
      });
    } else {
      const opType = data.type || "op";
      const hint = data.title || data.status || data.project || "";
      tokens.push({
        raw,
        kind,
        label: hint ? `${opType} • ${hint}` : opType,
        start,
        end,
        data,
      });
    }
  }
  return tokens;
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
  mode?: AssistantChatMode;
  onAddReference?: (ref: any) => void;
  onInputFocus?: () => void;
  trustMode?: "training_wheels" | "supervised" | "autonomous";
  onOperationsUpdate?: (ops: {
    applied: any[];
    pending: any[];
    errors: any[];
  }) => void;
  /**
   * When false, interactive surfaces will be suppressed from rendering
   * (but still retained in message state) so Workroom can gate by mode.
   */
  surfaceRenderAllowed?: boolean;
  /**
   * Optional override to handle surface navigation (used by Workroom to push focus).
   */
  onSurfaceNavigateOverride?: (nav: SurfaceNavigateTo) => void;
  workroomContext?: WorkroomContext | null;
};

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
  surfaceRenderAllowed,
  onSurfaceNavigateOverride,
  workroomContext = null,
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
  const [isTyping, setIsTyping] = useState(false);
  const [contextExpanded, setContextExpanded] = useState(false);
  const [draftCache, setDraftCache] = useState<Record<string, string>>({});
  const [operationsState, setOperationsState] = useState<OperationsState>({
    applied: [],
    pending: [],
    errors: [],
  });
  const allowSurfaces = useMemo(
    () => shouldAllowSurfaces(mode, surfaceRenderAllowed),
    [mode, surfaceRenderAllowed]
  );
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
  const [contextSpace, setContextSpace] = useState<ContextSpace>(
    createEmptyContextSpace()
  );
  // Stored for future context-aware UI surfaces
  void contextSpace;
  useEffect(() => {
    if (suggestedTaskTitle) {
      setSuggestedTaskTitleResolved(suggestedTaskTitle);
    } else if (!suggestedTaskId) {
      setSuggestedTaskTitleResolved(null);
    }
  }, [suggestedTaskId, suggestedTaskTitle]);
  useEffect(() => {
    setContextSpace(createEmptyContextSpace());
  }, [threadId]);
  const [isSlashMenuOpen, setSlashMenuOpen] = useState(false);
  const [slashMenuPosition, setSlashMenuPosition] = useState({
    top: 0,
    left: 0,
  });
  const updateContextSpace = useCallback<UpdateContextSpace>((updater) => {
    setContextSpace((current) => updater(current));
  }, []);
  const forceCurrentProject = mode === "workroom";
  const appliedOps = operationsState.applied;
  const pendingOps = operationsState.pending;
  const hasErrors = operationsState.errors.length > 0;
  const slashCommands = useMemo<SlashCommand[]>(
    () => [
      {
        id: "note",
        label: "/note",
        icon: Note24Regular,
        description: "Add a note to the context",
      },
      {
        id: "decision",
        label: "/decision",
        icon: Lightbulb24Regular,
        description: "Capture a decision in context",
      },
      {
        id: "constraint",
        label: "/constraint",
        icon: ShieldAdd24Regular,
        description: "Add a constraint to consider",
      },
      {
        id: "doc",
        label: "/doc",
        icon: DocumentAdd24Regular,
        description: "Attach a placeholder document",
      },
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
  const tokenSegments = useMemo<TokenSegment[]>(() => {
    if (!message) {
      return [{ type: "text", text: "" }];
    }
    if (parsedTokens.length === 0) {
      return [{ type: "text", text: message }];
    }
    const segments: TokenSegment[] = [];
    const sortedTokens = [...parsedTokens].sort((a, b) => a.start - b.start);
    let cursor = 0;
    sortedTokens.forEach((token) => {
      if (token.start > cursor) {
        segments.push({
          type: "text",
          text: message.slice(cursor, token.start),
        });
      }
      segments.push({ type: "token", token });
      cursor = token.end;
    });
    if (cursor < message.length) {
      segments.push({ type: "text", text: message.slice(cursor) });
    }
    return segments.length ? segments : [{ type: "text", text: message }];
  }, [message, parsedTokens]);
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

  useEffect(() => {
    draftCacheRef.current = draftCache;
  }, [draftCache]);

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
      if (typeof requestAnimationFrame !== "undefined") {
        requestAnimationFrame(() => {
          if (textareaRef.current) {
            textareaRef.current.focus();
            textareaRef.current.selectionStart = nextPos;
            textareaRef.current.selectionEnd = nextPos;
          }
          selectionRef.current = { start: nextPos, end: nextPos };
        });
      } else {
        // Fallback for test environments
        setTimeout(() => {
          if (textareaRef.current) {
            textareaRef.current.focus();
            textareaRef.current.selectionStart = nextPos;
            textareaRef.current.selectionEnd = nextPos;
          }
          selectionRef.current = { start: nextPos, end: nextPos };
        }, 0);
      }
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
      if (typeof requestAnimationFrame !== "undefined") {
        requestAnimationFrame(() => {
          if (textareaRef.current) {
            textareaRef.current.focus();
            textareaRef.current.selectionStart = idx;
            textareaRef.current.selectionEnd = idx;
          }
        });
      } else {
        setTimeout(() => {
          if (textareaRef.current) {
            textareaRef.current.focus();
            textareaRef.current.selectionStart = idx;
            textareaRef.current.selectionEnd = idx;
          }
        }, 0);
      }
    },
    [message, updateMessageValue]
  );

  const handleTokenDetailToggle = useCallback((tokenId: string) => {
    setActiveTokenDetailId((current) => (current === tokenId ? null : tokenId));
    if (typeof requestAnimationFrame !== "undefined") {
      requestAnimationFrame(() => {
        textareaRef.current?.focus();
      });
    } else {
      setTimeout(() => {
        textareaRef.current?.focus();
      }, 0);
    }
  }, []);

  const handleOverlayRemoveToken = useCallback(
    (tokenId: string, rawToken: string) => {
      setActiveTokenDetailId((current) =>
        current === tokenId ? null : current
      );
      handleRemoveToken(rawToken);
    },
    [handleRemoveToken]
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

      const handledContextCommand = applyContextCommand({
        commandId: command.id as ContextCommandId,
        inputValue: message,
        updateContextSpace,
      });

      if (handledContextCommand) {
        setMessage("");
        return;
      }

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
    [
      closeSlashMenu,
      ensureProjectsIndex,
      message,
      openReferenceSearch,
      showInlineNotice,
      updateContextSpace,
    ]
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
  const tokenOverlayRef = useRef<HTMLDivElement | null>(null);
  const inputFooterRef = useRef<HTMLDivElement | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const typingStartRef = useRef<number | null>(null);
  const messagesRef = useRef<Message[]>([]);
  const selectionRef = useRef<{ start: number; end: number }>({
    start: 0,
    end: 0,
  });
  const draftCacheRef = useRef<Record<string, string>>({});
  const previousActionIdRef = useRef<string | null>(actionId);
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
  const [activeTokenDetailId, setActiveTokenDetailId] = useState<string | null>(
    null
  );
  const typingSessionRef = useRef<{
    showTimerId: NodeJS.Timeout | null;
    clearTimerId: NodeJS.Timeout | null;
  }>({ showTimerId: null, clearTimerId: null });
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Adaptive polling state
  const [isTabVisible, setIsTabVisible] = useState(true);
  const [isThreadActive, setIsThreadActive] = useState(true);
  const lastActivityRef = useRef<number>(Date.now());
  const mutateDebounceTimerRef = useRef<NodeJS.Timeout | null>(null);
  const pendingMutateRef = useRef<(() => Promise<any>) | null>(null);

  const MIN_TYPING_DURATION = 500; // ms
  const ASSISTANT_START_DELAY_MS = 100; // ms

  const applySurfaceFilters = useCallback(
    (surfaces?: InteractiveSurface[] | null) => {
      if (!surfaces || !Array.isArray(surfaces)) return undefined;
      let scopedSurfaces = surfaces;
      if (mode === "workroom") {
        scopedSurfaces =
          filterSurfacesByWorkroomContext(
            surfaces,
            workroomContext ?? null
          )?.slice(0, MAX_WORKROOM_SURFACES) || [];
      }
      const gated = filterSurfacesForMode(scopedSurfaces, mode);
      return gated && gated.length > 0 ? gated : undefined;
    },
    [mode, workroomContext]
  );

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

  const syncOverlayScroll = useCallback(() => {
    if (tokenOverlayRef.current && textareaRef.current) {
      tokenOverlayRef.current.scrollTop = textareaRef.current.scrollTop;
    }
  }, []);

  // Bootstrap thread if needed (only if not provided and shouldFocus is true)
  // Note: ActionCard creates thread on expand, so this is mainly for edge cases
  useEffect(() => {
    if (!threadId && !initialThreadId && actionId && shouldFocus) {
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
  }, [threadId, initialThreadId, actionId, onThreadCreated, shouldFocus, summary]);

  // Adaptive polling: pause when tab hidden or thread inactive
  const shouldPoll = isTabVisible && isThreadActive;
  const POLL_INTERVAL = 5000;
  const INACTIVITY_THRESHOLD_MS = 30000; // 30 seconds
  const MUTATE_DEBOUNCE_MS = 500; // 500ms debounce for rapid refetches

  // Track activity: update last activity time on user interaction
  // Use ref-based callback to avoid recreating on every render
  const markActivityRef = useRef(() => {
    lastActivityRef.current = Date.now();
    setIsThreadActive(true);
  });
  const markActivity = markActivityRef.current;

  const {
    messages,
    setMessages,
    threadData,
    mutateThreadRaw,
    isLoadingThread,
  } = useChatThread({ threadId });

  // Fetch messages
  // Debounced mutateThread wrapper to coalesce rapid refetches
  const debouncedMutateThread = useCallback(async () => {
    // Clear existing debounce timer
    if (mutateDebounceTimerRef.current) {
      clearTimeout(mutateDebounceTimerRef.current);
      mutateDebounceTimerRef.current = null;
    }

    // Store the mutate function to call
    pendingMutateRef.current = async () => {
      if (mutateThreadRaw) {
        return mutateThreadRaw();
      }
    };

    // Set debounce timer
    mutateDebounceTimerRef.current = setTimeout(() => {
      mutateDebounceTimerRef.current = null;
      const fn = pendingMutateRef.current;
      pendingMutateRef.current = null;
      if (fn) {
        fn().catch((err) => {
          console.warn("Debounced mutateThread failed:", err);
        });
      }
    }, MUTATE_DEBOUNCE_MS);
  }, [mutateThreadRaw]);

  // Wrapped mutateThread that uses debouncing and marks activity
  const mutateThread = useCallback(async () => {
    markActivity();
    return debouncedMutateThread();
  }, [debouncedMutateThread, markActivity]);

  // Visibility change handler
  useEffect(() => {
    if (typeof document === "undefined") return; // Guard for SSR/test environments

    const handleVisibilityChange = () => {
      setIsTabVisible(!document.hidden);
    };
    document.addEventListener("visibilitychange", handleVisibilityChange);
    setIsTabVisible(!document.hidden);
    return () => {
      document.removeEventListener("visibilitychange", handleVisibilityChange);
    };
  }, []);

  // Inactivity detection: check every 5 seconds if thread should be considered inactive
  useEffect(() => {
    if (!shouldPoll) {
      return; // Skip if already paused
    }

    const checkInactivity = () => {
      const now = Date.now();
      const timeSinceActivity = now - lastActivityRef.current;
      if (timeSinceActivity > INACTIVITY_THRESHOLD_MS) {
        setIsThreadActive(false);
      }
    };

    const interval = setInterval(checkInactivity, 5000);
    return () => {
      clearInterval(interval);
    };
  }, [shouldPoll]);

  // Mark activity on user interactions
  // Use stable callback to avoid recreating listeners on every render
  useEffect(() => {
    if (typeof window === "undefined") return; // Guard for SSR/test environments

    const handleUserActivity = () => {
      markActivity();
    };
    // Listen to various user events
    window.addEventListener("mousedown", handleUserActivity);
    window.addEventListener("keydown", handleUserActivity);
    window.addEventListener("scroll", handleUserActivity);
    return () => {
      window.removeEventListener("mousedown", handleUserActivity);
      window.removeEventListener("keydown", handleUserActivity);
      window.removeEventListener("scroll", handleUserActivity);
    };
  }, []); // Empty deps - markActivity is stable via ref

  // Reset messages when threadId changes to prevent cross-thread contamination
  useEffect(() => {
    if (threadId) {
      setMessages([]); // Clear messages when switching threads
    }
  }, [threadId]);

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

  // Load draft only when switching actions
  useEffect(() => {
    if (!actionId) {
      previousActionIdRef.current = actionId;
      setMessage("");
      return;
    }
    if (previousActionIdRef.current === actionId) {
      return;
    }
    const cachedValue = draftCacheRef.current[actionId];
    setMessage(cachedValue ?? "");
    previousActionIdRef.current = actionId;
  }, [actionId]);

  // Auto-scroll to bottom - scroll the messages container, not the page
  useEffect(() => {
    if (messagesContainerRef.current && messagesEndRef.current) {
      const container = messagesContainerRef.current;
      const scrollToBottom = () => {
        container.scrollTop = container.scrollHeight;
      };
      // Use requestAnimationFrame to ensure DOM is updated
      if (typeof requestAnimationFrame !== "undefined") {
        requestAnimationFrame(() => {
          scrollToBottom();
        });
      } else {
        setTimeout(() => {
          scrollToBottom();
        }, 0);
      }
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
    markActivity(); // Mark activity when user sends a message
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
    if (typeof requestAnimationFrame !== "undefined") {
      requestAnimationFrame(() => {
        textareaRef.current?.focus();
      });
    } else {
      setTimeout(() => {
        textareaRef.current?.focus();
      }, 0);
    }

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

                  // Optimistic surfaces: store surfaces immediately if present
                  if (
                    suggestResponse.surfaces &&
                    Array.isArray(suggestResponse.surfaces)
                  ) {
                    const parsedSurfaces = parseInteractiveSurfaces(
                      suggestResponse.surfaces
                    );
                    const filteredSurfaces = applySurfaceFilters(parsedSurfaces);
                    if (filteredSurfaces && filteredSurfaces.length > 0) {
                      // Create or update optimistic assistant message with surfaces
                      setMessages((prev) => {
                        // Find existing optimistic assistant message or create new one
                        const existingOptimistic = prev.find(
                          (msg) => msg.role === "assistant" && msg.optimistic
                        );
                        if (existingOptimistic) {
                          // Update existing optimistic message with surfaces
                          return prev.map((msg) =>
                            msg.id === existingOptimistic.id
                              ? { ...msg, surfaces: filteredSurfaces }
                              : msg
                          );
                        } else {
                          // Create new optimistic assistant message with surfaces
                          const optimisticMsg: Message = {
                            ...createAssistantMessage(""),
                            optimistic: true,
                            surfaces: filteredSurfaces,
                          };
                          return [...prev, optimisticMsg];
                        }
                      });
                    }
                  }

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
      if (
        options?.confirm &&
        !window.confirm("Are you sure you want to run this action?")
      ) {
        return;
      }
      const operation = convertOpTokenToOperation(opToken);
      if (!operation) {
        showInlineNotice("Couldn't run that action. Please try again.");
        return;
      }
      try {
        const result = await runOperationApi("approve", {
          operation: sanitizeOperationForApi(operation, {
            forceCurrentProject,
          }),
        });
        if (!result?.ok) {
          const errorDetail =
            result?.detail?.assistant_message ||
            result?.detail?.detail ||
            result?.detail ||
            result?.error ||
            "Failed to run that action.";
          pushOperationError(errorDetail, {
            op: operation.op,
            params: operation.params,
          });
          return;
        }
        scheduleThreadRefreshForChat();
      } catch (err: any) {
        pushOperationError(err?.message || "Failed to run that action.", {
          op: operation.op,
          params: operation.params,
        });
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
      if (onSurfaceNavigateOverride) {
        onSurfaceNavigateOverride(nav);
        return;
      }
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
          showInlineNotice(
            "Opening calendar events is not yet supported in this build."
          );
          break;
        default:
          showInlineNotice("Navigation target not supported yet.");
      }
    },
    [onOpenWorkroom, onSurfaceNavigateOverride, showInlineNotice]
  );

  const handleSurfaceContextUpdate = useCallback(
    async (entries: ContextAddEntry[]) => {
      if (!entries?.length) return;
      try {
        await workroomApi.updateContextSpace({ entries });
        showInlineNotice("Context updated");
      } catch (err) {
        console.error("Failed to update context space", err);
        showInlineNotice("Couldn't update context. Please try again.");
      }
    },
    [showInlineNotice]
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
    (latestAssistantSurfaces?.some(
      (surface) => surface.kind === "triage_table_v1"
    ) ??
      false) &&
    !hasErrors;

  const shouldShowActionSummary =
    !hideActionSummaryForSurfaces &&
    (appliedOps.length > 0 || pendingOps.length > 0 || hasErrors);

  // Memoize ActionSummary props to prevent unnecessary re-renders
  // Create a hash of ops to use as memo key
  const opsHash = useMemo(() => {
    if (!shouldShowActionSummary) {
      return "hidden";
    }
    // Create deterministic hash from ops state
    const opsString = JSON.stringify({
      applied: appliedOps.map((op) => ({ op: op.op, params: op.params })),
      pending: pendingOps.map((op) => ({ op: op.op, params: op.params })),
      errors: operationsState.errors.map((err) => ({
        id: err.id,
        message: err.message,
      })),
    });
    return opsString;
  }, [shouldShowActionSummary, appliedOps, pendingOps, operationsState.errors]);

  // Memoized ActionSummary component props
  const actionSummaryProps = useMemo(() => {
    if (!shouldShowActionSummary) {
      return null;
    }
    return {
      appliedOps,
      pendingOps,
      trustMode,
      errors: operationsState.errors,
    };
  }, [
    shouldShowActionSummary,
    appliedOps,
    pendingOps,
    trustMode,
    operationsState.errors,
  ]);

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

      const validatedSurfaces =
        allowSurfaces && msg.surfaces
          ? applySurfaceFilters(msg.surfaces as InteractiveSurface[] | undefined)
          : undefined;

      return {
        id: msg.id,
        role: msg.role,
        content: msg.content,
        embeds: msg.embeds,
        surfaces: validatedSurfaces,
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
  }, [
    groupedMessages,
    formatTimestamp,
    activeAssistantId,
    allowSurfaces,
    applySurfaceFilters,
  ]);

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
              onUpdateContextSpace={handleSurfaceContextUpdate}
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
          {inlineNotice && (
            <div className="text-xs text-slate-500 pb-2">{inlineNotice}</div>
          )}
          {/* Input Row */}
          <div className="flex items-end gap-2 pb-4">
            <div className="relative flex-1">
              <TokenOverlay
                message={message}
                tokenSegments={tokenSegments}
                activeTokenDetailId={activeTokenDetailId}
                tokenOverlayRef={tokenOverlayRef}
                onToggleDetail={handleTokenDetailToggle}
                onRemoveToken={handleOverlayRemoveToken}
              />
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
                onScroll={syncOverlayScroll}
                placeholder="Message Assistant"
                aria-label="Message Assistant"
                disabled={!threadId}
                className="w-full resize-none max-h-24 rounded-md border border-slate-300 focus:outline-none focus:ring-2 focus:ring-slate-300 px-3 py-2 text-sm bg-transparent relative z-10 text-transparent caret-slate-900 placeholder:text-transparent selection:bg-slate-200/60"
                rows={1}
              />
            </div>
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

          {/* Action Summary - Memoized to prevent unnecessary re-renders */}
          {shouldShowActionSummary && actionSummaryProps && (
            <div className="border-t border-slate-200" key={opsHash}>
              {/* TODO(LucidWork Contract): ActionSummary will surface/edit explicit target IDs here. */}
              <ActionSummary
                appliedOps={actionSummaryProps.appliedOps}
                pendingOps={actionSummaryProps.pendingOps}
                trustMode={actionSummaryProps.trustMode}
                errors={actionSummaryProps.errors}
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
