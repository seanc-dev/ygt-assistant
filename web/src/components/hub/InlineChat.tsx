import { useState, useRef, useEffect, useCallback, memo, useMemo } from "react";
import {
  Send24Regular,
  ChevronDown24Regular,
  ArrowClockwise24Regular,
} from "@fluentui/react-icons";
import { api } from "../../lib/api";
import useSWR from "swr";
import { ActionEmbedComponent } from "../workroom/ActionEmbed";

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
};

type MessageView = {
  id: string;
  role: "user" | "assistant";
  content: string;
  embeds?: any[];
  marginTop: string;
  timestampLabel: string;
  showTimestamp: boolean;
  shouldAnimate: boolean;
  startDelayMs?: number;
  error?: boolean;
  retryable?: boolean;
  errorMessage?: string;
};

type ThreadResponse = {
  ok: boolean;
  thread: {
    id: string;
    messages: Message[];
  };
};

type InlineChatProps = {
  actionId: string;
  threadId?: string | null;
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
};

// MessageItem component - only accepts data props, no functions
const MessageItem = memo(
  ({
    view,
    onRetry,
    onEmbedUpdate,
    animatedRef,
  }: {
    view: MessageView;
    onRetry: (id: string) => void;
    onEmbedUpdate: (messageId: string, embed: any) => void;
    animatedRef: React.MutableRefObject<Set<string>>;
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
      prevProps.onRetry === nextProps.onRetry &&
      prevProps.onEmbedUpdate === nextProps.onEmbedUpdate &&
      prevProps.animatedRef === nextProps.animatedRef
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
  }: {
    content: string;
    id: string;
    shouldAnimate: boolean;
    animatedRef: React.MutableRefObject<Set<string>>;
    startDelayMs?: number;
  }) => {
    const markAsSeen = useCallback(() => {
      animatedRef.current.add(id);
    }, [id, animatedRef]);

    const displayedText = useTypingEffect(
      content,
      30,
      shouldAnimate,
      markAsSeen,
      startDelayMs
    );
    return <>{displayedText}</>;
  }
);
TypingMessageContent.displayName = "TypingMessageContent";

// Typing effect hook for assistant messages
function useTypingEffect(
  text: string,
  speed: number = 30,
  enabled: boolean = true,
  onComplete?: () => void,
  startDelayMs: number = 0
) {
  const [displayedText, setDisplayedText] = useState("");
  const [hasStarted, setHasStarted] = useState(false);

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
  }: {
    messageViews: MessageView[];
    isTyping: boolean;
    onRetryMessage: (id: string) => void;
    onEmbedUpdate: (messageId: string, embed: any) => void;
    animatedRef: React.MutableRefObject<Set<string>>;
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
            />
          ))
        )}
        {isTyping && (
          <div className="flex items-start gap-2 mt-2">
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
      prevProps.animatedRef === nextProps.animatedRef
    );
  }
);
MessageList.displayName = "MessageList";

export function InlineChat({
  actionId,
  threadId: initialThreadId,
  summary,
  meta,
  onThreadCreated,
  onOpenWorkroom,
  shouldFocus = false,
  mode = "default",
  onAddReference,
  onInputFocus,
}: InlineChatProps) {
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
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const typingStartRef = useRef<number | null>(null);
  const messagesRef = useRef<Message[]>([]);
  const [animatedMessageIds, setAnimatedMessageIds] = useState<Set<string>>(
    new Set()
  );
  const animatedRef = useRef<Set<string>>(new Set());
  const previousMessagesRef = useRef<Message[]>([]);
  const isInitialLoadRef = useRef<boolean>(true);
  const awaitingAssistantAfterTsRef = useRef<string | null>(null);
  const typingSessionRef = useRef<{
    showTimerId: NodeJS.Timeout | null;
    clearTimerId: NodeJS.Timeout | null;
  }>({ showTimerId: null, clearTimerId: null });

  const MIN_TYPING_DURATION = 500; // ms
  const ASSISTANT_START_DELAY_MS = 100; // ms

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
  const { data: threadData, mutate: mutateThread, isLoading: isLoadingThread } = useSWR<ThreadResponse>(
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
          const normalizedMsg = {
            id: msg.id || String(Math.random()),
            role: (msg.role === "user" ? "user" : "assistant") as
              | "user"
              | "assistant",
            content: msg.content || msg.text || "",
            ts: msg.ts || msg.created_at || new Date().toISOString(),
            embeds: msg.embeds || [],
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

  // Track animated message IDs to prevent replay
  // Only animate assistant messages that are newly added (not in previous render)
  useEffect(() => {
    const previousMessageIds = new Set(
      previousMessagesRef.current.map((m) => m.id)
    );
    const isInitialLoad = previousMessagesRef.current.length === 0;

    messages.forEach((m) => {
      if (m.role === "assistant") {
        // On initial load, mark all messages as seen (don't animate)
        // If message was already in previous render, mark it as seen (don't animate)
        // If it's a new message, it will animate until marked as seen
        if (isInitialLoad || previousMessageIds.has(m.id)) {
        animatedRef.current.add(m.id);
      }
      }
    });

    // Mark initial load as complete after first messages pass
    if (isInitialLoad && messages.length > 0) {
      isInitialLoadRef.current = false;
    }

    // Update previous messages ref for next render
    previousMessagesRef.current = messages;
  }, [messages]);

  const shouldAnimate = useCallback((msg: Message) => {
    // Only animate assistant messages that haven't been seen before
    // User messages always display in full
    if (msg.role === "user") {
      return false;
    }
    return msg.role === "assistant" && !animatedRef.current.has(msg.id);
  }, []);

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
    };
  }, []);

  // Load draft from cache
  useEffect(() => {
    if (draftCache[actionId]) {
      setMessage(draftCache[actionId]);
    }
  }, [actionId, draftCache]);

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
    setMessage("");
    setDraftCache((prev) => ({ ...prev, [actionId]: "" }));

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
      // Stop propagation to prevent card handlers from catching these events
      e.stopPropagation();

      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
      // Shift+Enter naturally creates a new line, no need to handle
      // Space works normally, no need to handle
      if (e.key === "Escape" && contextExpanded) {
        setContextExpanded(false);
      }
    },
    [handleSend, contextExpanded]
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

      // Compute shouldAnimate - only animate if not initial load and not already seen
      const shouldAnimate =
        msg.role === "assistant" &&
        !isInitialLoadRef.current &&
        !animatedRef.current.has(msg.id);

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
  }, [groupedMessages, formatTimestamp]);

  const containerStyle = useMemo(() => {
    return { height: "100%", minHeight: 0 };
  }, []);

  return (
    <>
      <style>{scrollbarStyles}</style>
      <div
        ref={containerRef}
        className="grid grid-rows-[auto,minmax(0,1fr),auto] bg-white rounded-lg p-4 h-full min-h-0"
        style={containerStyle}
        onClick={(e) => e.stopPropagation()}
        onMouseDown={(e) => e.stopPropagation()}
      >
        {/* Context Accordion - Row 1 (hidden in workroom mode) */}
        {mode !== "workroom" && (
          <div className="flex-shrink-0 mb-4 bg-white -mx-4 px-4 pt-0">
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
          className="min-h-0 overflow-y-auto overflow-x-hidden bg-white -mx-4 px-4 py-3 chat-scrollbar"
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
                  />
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Wrapper */}
        <div className="flex-shrink-0 bg-white pt-4 pb-0 border-t border-slate-200 -mx-4 px-4">
          <div className="flex items-end gap-2">
            <textarea
              ref={textareaRef}
              value={message}
              onChange={(e) => {
                setMessage(e.target.value);
                setDraftCache((prev) => ({
                  ...prev,
                  [actionId]: e.target.value,
                }));
              }}
              onFocus={() => {
                onInputFocus?.();
              }}
              onMouseDown={(e) => e.stopPropagation()}
              onKeyDown={handleKeyDown}
              placeholder="Message Assistant"
              aria-label="Message Assistant"
              disabled={!threadId || isTyping}
              className="w-full resize-none max-h-24 rounded-md border border-slate-300 focus:outline-none focus:ring-2 focus:ring-slate-300 px-3 py-2 text-sm"
              rows={1}
            />
            <button
              onClick={(e) => {
                e.stopPropagation();
                handleSend();
              }}
              disabled={!message.trim() || !threadId || isTyping}
              className="text-slate-600 hover:text-slate-800 disabled:text-slate-300 disabled:cursor-not-allowed transition-colors focus:outline-none focus:ring-2 focus:ring-slate-300 rounded-md p-1.5"
              aria-label="Send message"
            >
              <Send24Regular className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
