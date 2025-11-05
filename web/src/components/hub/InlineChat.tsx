import { useState, useRef, useEffect, useCallback, memo } from "react";
import {
  Send24Regular,
  ChevronDown24Regular,
  ArrowClockwise24Regular,
} from "@fluentui/react-icons";
import { api } from "../../lib/api";
import useSWR from "swr";

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
};

export function InlineChat({
  actionId,
  threadId: initialThreadId,
  summary,
  meta,
  onThreadCreated,
  onOpenWorkroom,
  shouldFocus = false,
}: InlineChatProps) {
  const [threadId, setThreadId] = useState<string | null>(
    initialThreadId || null
  );
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const [contextExpanded, setContextExpanded] = useState(false);
  const [draftCache, setDraftCache] = useState<Record<string, string>>({});
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const typingStartRef = useRef<number | null>(null);
  const [animatedMessageIds, setAnimatedMessageIds] = useState<Set<string>>(
    new Set()
  );
  const animatedRef = useRef<Set<string>>(new Set());

  const MIN_TYPING_DURATION = 500; // ms

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
  const { data: threadData, mutate: mutateThread } = useSWR<ThreadResponse>(
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

  // Update messages when thread data changes - merge instead of replace
  useEffect(() => {
    if (threadData?.thread?.messages) {
      setMessages((prev) => {
        const backendMessages = threadData.thread.messages;
        // Merge: keep optimistic messages that aren't confirmed yet
        const optimisticMessages = prev.filter((msg) => msg.optimistic);
        const confirmedIds = new Set(backendMessages.map((m) => m.id));
        const stillOptimistic = optimisticMessages.filter(
          (msg) => !confirmedIds.has(msg.id)
        );

        // Ensure roles are correct - fix any role mismatches
        const correctedBackendMessages = backendMessages.map((msg) => {
          // If message was sent by user (check by matching content with optimistic), ensure role is user
          const matchingOptimistic = optimisticMessages.find(
            (opt) => opt.content === msg.content && opt.role === "user"
          );
          if (matchingOptimistic) {
            return { ...msg, role: "user" as const };
          }
          // Ensure role is either user or assistant
          return {
            ...msg,
            role: (msg.role === "user" ? "user" : "assistant") as
              | "user"
              | "assistant",
          };
        });

        // Combine backend messages with still-optimistic ones
        const merged = [...correctedBackendMessages, ...stillOptimistic];
        // Sort by timestamp
        return merged.sort(
          (a, b) => new Date(a.ts).getTime() - new Date(b.ts).getTime()
        );
      });
    }
  }, [threadData]);

  // Track animated message IDs to prevent replay
  useEffect(() => {
    messages.forEach((m) => {
      if (m.role === "assistant") {
        animatedRef.current.add(m.id);
      }
    });
  }, [messages]);

  const shouldAnimate = useCallback((msg: Message) => {
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

  // Clear typing indicator when assistant message arrives
  useEffect(() => {
    const hasAssistantMessage = messages.some(
      (msg) => msg.role === "assistant" && !msg.optimistic
    );
    if (hasAssistantMessage && isTyping && typingStartRef.current) {
      clearTyping();
    }
  }, [messages, isTyping, clearTyping]);

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
    // Don't set typing immediately - wait for user message to be confirmed before showing typing indicator
    // This prevents flicker on first message

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
          // Now show typing indicator for assistant response (with minimum duration)
          setIsTyping(true);
          typingStartRef.current = Date.now();
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
        // Recreate thread before retry
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
    }

    // Clear typing indicator if it was set (with minimum duration)
    if (typingStartRef.current) {
      clearTyping();
    }
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
      const msgToRetry = messages.find((m) => m.id === messageId);
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
      } finally {
        // clearTyping handles minimum duration, but only if isTyping is still true
        if (isTyping) {
          // If we're still typing, clearTyping will handle it
        } else {
          clearTyping();
        }
      }
    },
    [messages, threadId, mutateThread, isTyping, clearTyping]
  );

  const formatTimestamp = (ts: string) => {
    const date = new Date(ts);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
    return date.toLocaleDateString();
  };

  // Typing effect hook for assistant messages
  const useTypingEffect = (
    text: string,
    speed: number = 30,
    enabled: boolean = true
  ) => {
    const [displayedText, setDisplayedText] = useState("");

    useEffect(() => {
      if (!enabled) {
        setDisplayedText(text);
        return;
      }

      if (displayedText.length < text.length) {
        const timeout = setTimeout(() => {
          setDisplayedText(text.slice(0, displayedText.length + 1));
        }, speed);
        return () => clearTimeout(timeout);
      }
    }, [displayedText, text, speed, enabled]);

    // Reset when text changes
    useEffect(() => {
      if (text !== displayedText && displayedText.length === text.length) {
        setDisplayedText("");
      }
    }, [text]);

    return displayedText || "";
  };

  // Component for typing message
  const TypingMessage = memo(
    ({
      content,
      id,
      shouldAnimate,
    }: {
      content: string;
      id: string;
      shouldAnimate: boolean;
    }) => {
      const displayedText = useTypingEffect(content, 30, shouldAnimate);
      return <>{displayedText}</>;
    }
  );
  TypingMessage.displayName = "TypingMessage";

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

  // Memoized message component to prevent re-renders
  const ChatMessage = memo(
    ({
      msg,
      marginTop,
      showTimestamp,
      formatTimestamp,
      handleRetryMessage,
      shouldAnimate,
    }: {
      msg: Message & { isGroupStart: boolean; isGroupEnd: boolean };
      marginTop: string;
      showTimestamp: boolean;
      formatTimestamp: (ts: string) => string;
      handleRetryMessage: (id: string) => void;
      shouldAnimate: boolean;
    }) => {
      const isUserMessage = msg.role === "user";
      return (
        <div
          className={`flex flex-col gap-0.5 transition-all duration-300 w-full ${
            msg.role === "user" ? "items-end" : "items-start"
          } ${marginTop}`}
        >
          <div
            className={`flex items-end gap-2 ${
              msg.role === "user"
                ? "justify-end flex-row-reverse"
                : "justify-start"
            }`}
          >
            {msg.error && msg.retryable && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleRetryMessage(msg.id);
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
                msg.role === "user" ? "max-w-[80%]" : "max-w-[80%]"
              } ${
                msg.role === "assistant"
                  ? "bg-slate-100 text-slate-900 border border-slate-200"
                  : msg.error
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
                {msg.role === "assistant" ? (
                  <TypingMessage
                    content={msg.content}
                    id={msg.id}
                    shouldAnimate={shouldAnimate}
                  />
                ) : (
                  msg.content
                )}
              </div>
              {msg.error && msg.errorMessage && (
                <div className="text-xs text-red-600 mt-1 opacity-75">
                  {msg.errorMessage}
                </div>
              )}
            </div>
          </div>
          {showTimestamp && (
            <span className="text-xs text-slate-500 mt-1">
              {formatTimestamp(msg.ts)}
            </span>
          )}
        </div>
      );
    },
    (prevProps, nextProps) => {
      // Only re-render if message content, error state, or animation state changes
      return (
        prevProps.msg.id === nextProps.msg.id &&
        prevProps.msg.content === nextProps.msg.content &&
        prevProps.msg.error === nextProps.msg.error &&
        prevProps.shouldAnimate === nextProps.shouldAnimate &&
        prevProps.showTimestamp === nextProps.showTimestamp
      );
    }
  );
  ChatMessage.displayName = "ChatMessage";

  const contextSummary = meta
    ? [
        meta.from && `From: ${meta.from}`,
        meta.threadLen !== undefined && `Thread: ${meta.threadLen}`,
        meta.lastAt && `Last: ${formatTimestamp(meta.lastAt)}`,
      ]
        .filter(Boolean)
        .join(" • ")
    : summary || "No context available";

  return (
    <>
      <style>{scrollbarStyles}</style>
      <div
        className="flex flex-col bg-white rounded-lg p-4"
        style={{ height: "100%", minHeight: 0 }}
        onClick={(e) => e.stopPropagation()}
        onMouseDown={(e) => e.stopPropagation()}
      >
        {/* Context Accordion - Sticky at top, always visible */}
        <div className="flex-shrink-0 mb-4 sticky top-0 bg-white z-10 -mx-4 px-4 pt-0">
          <div className="rounded-lg border border-slate-200 overflow-hidden">
            <button
              onClick={(e) => {
                e.stopPropagation();
                handleContextToggle();
              }}
              className="w-full flex items-center justify-between gap-1.5 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-slate-300 rounded-md transition-colors"
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
                {threadId && onOpenWorkroom && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onOpenWorkroom(threadId);
                    }}
                    className="text-xs text-blue-600 hover:text-blue-700 underline focus:outline-none focus:ring-2 focus:ring-blue-300 rounded ml-auto"
                  >
                    Open in Workroom
                  </button>
                )}
              </div>
            </button>
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

        {/* Messages List - Scrollable */}
        <div
          ref={messagesContainerRef}
          role="log"
          aria-live="polite"
          className="flex-1 overflow-y-auto overflow-x-hidden bg-white -mx-4 px-4 py-3 chat-scrollbar"
          style={{
            scrollBehavior: "smooth",
            scrollbarWidth: "thin",
            scrollbarColor: "#cbd5e1 #ffffff",
          }}
        >
          {messages.length === 0 && !threadId ? (
            <div className="text-sm text-slate-500 py-4 text-center">
              Starting conversation...
            </div>
          ) : messages.length === 0 ? (
            <div className="text-sm text-slate-500 py-4 text-center">
              No messages yet. Start the conversation!
            </div>
          ) : (
            (() => {
              const groupedMessages = groupMessages(messages);
              return groupedMessages.map((msg, index) => {
                const isGrouped = !msg.isGroupStart;
                const showTimestamp = msg.isGroupEnd;

                // Check if role changed for visual spacing
                const prevMsg = index > 0 ? groupedMessages[index - 1] : null;
                const roleChanged = prevMsg && prevMsg.role !== msg.role;

                // Add margin-top for spacing: larger gap when role changes, tighter within same role
                const marginTop = roleChanged
                  ? "mt-4"
                  : isGrouped
                  ? "mt-1"
                  : "mt-2";

                return (
                  <ChatMessage
                    key={msg.id}
                    msg={msg}
                    marginTop={marginTop}
                    showTimestamp={showTimestamp}
                    formatTimestamp={formatTimestamp}
                    handleRetryMessage={handleRetryMessage}
                    shouldAnimate={shouldAnimate(msg)}
                  />
                );
              });
            })()
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
          <div ref={messagesEndRef} />
        </div>

        {/* Input Wrapper - Sticky at bottom */}
        <div className="sticky bottom-0 z-10 bg-white pt-4 pb-0 flex-shrink-0 border-t border-slate-200 -mx-4 px-4">
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
