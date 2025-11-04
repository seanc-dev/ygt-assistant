import { useState, useRef, useEffect, useCallback } from "react";
import { Send24Regular, ChevronDown24Regular } from "@fluentui/react-icons";
import { api } from "../../lib/api";
import useSWR from "swr";

type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  ts: string;
  optimistic?: boolean;
  error?: boolean;
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
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Bootstrap thread if needed
  useEffect(() => {
    if (!threadId && actionId) {
      const bootstrapThread = async () => {
        try {
          // Get action title from queue or use a default
          const queueData = await api
            .queue()
            .catch(() => ({ ok: true, items: [] }));
          const action = (queueData as any)?.items?.find(
            (item: any) => item.action_id === actionId
          );
          const title = action?.preview || "Action Chat";

          // Create thread with source_action_id
          const response = await api.createThreadFromAction?.(actionId, title);
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
  }, [threadId, actionId, onThreadCreated]);

  // Fetch messages
  const { data: threadData, mutate: mutateThread } = useSWR<ThreadResponse>(
    threadId ? [`thread`, threadId] : null,
    async () => {
      if (!threadId) {
        throw new Error("No thread ID");
      }
      const response = await api.getThread?.(threadId);
      if (!response) {
        throw new Error("Failed to fetch thread");
      }
      return response as ThreadResponse;
    },
    {
      refreshInterval: 5000, // Poll for new messages
      revalidateOnFocus: true,
    }
  );

  // Update messages when thread data changes
  useEffect(() => {
    if (threadData?.thread?.messages) {
      setMessages(threadData.thread.messages);
    }
  }, [threadData]);

  // Load draft from cache
  useEffect(() => {
    if (draftCache[actionId]) {
      setMessage(draftCache[actionId]);
    }
  }, [actionId, draftCache]);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
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
    if (!message.trim() || !threadId) return;

    const tempId = `temp-${Date.now()}`;
    const optimisticMessage: Message = {
      id: tempId,
      role: "user",
      content: message.trim(),
      ts: new Date().toISOString(),
      optimistic: true,
    };

    // Optimistic update
    setMessages((prev) => [...prev, optimisticMessage]);
    setMessage("");
    setDraftCache((prev) => ({ ...prev, [actionId]: "" }));
    setIsTyping(true);

    try {
      const response = await api.sendMessage?.(threadId, {
        role: "user",
        content: optimisticMessage.content,
      });

      if (response?.ok && response?.message) {
        // Replace optimistic message with real one
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === tempId ? { ...response.message, optimistic: false } : msg
          )
        );
        // Refetch to get assistant response
        setTimeout(() => {
          mutateThread();
        }, 1000);
      } else {
        // Mark as error
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === tempId ? { ...msg, error: true, optimistic: false } : msg
          )
        );
      }
    } catch (err) {
      console.error("Failed to send message:", err);
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === tempId ? { ...msg, error: true, optimistic: false } : msg
        )
      );
    } finally {
      setIsTyping(false);
    }
  }, [message, threadId, actionId, mutateThread]);

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
    <div
      className="space-y-3"
      onClick={(e) => e.stopPropagation()}
      onMouseDown={(e) => e.stopPropagation()}
    >
      {/* Context Accordion */}
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

      {/* Chat Panel */}
      <div className="bg-white rounded-lg border border-slate-200 p-3 md:p-4 shadow-sm">
        {/* Title */}
        <div className="mb-3 text-sm font-medium text-slate-700">Assistant</div>

        {/* Messages List */}
        <div
          role="log"
          aria-live="polite"
          className="max-h-[44vh] md:max-h-[52vh] overflow-y-auto pr-1 space-y-2 mb-3"
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
            messages.map((msg) => (
              <div
                key={msg.id}
                className={`group flex flex-col gap-1 ${
                  msg.role === "user" ? "items-end" : "items-start"
                }`}
              >
                <div
                  className={`rounded-xl px-3 py-2 max-w-[85%] ${
                    msg.role === "assistant"
                      ? "bg-slate-50 text-slate-800"
                      : msg.error
                      ? "bg-red-50 text-red-900 border border-red-200"
                      : "bg-blue-50 text-blue-900"
                  }`}
                >
                  <div className="text-sm whitespace-pre-wrap break-words">
                    {msg.content}
                  </div>
                  {msg.role === "user" && (
                    <div className="text-xs text-blue-600 mt-1 opacity-60">
                      Sent by LucidWork
                    </div>
                  )}
                </div>
                <span className="text-xs text-slate-400 opacity-0 group-hover:opacity-100 group-focus-within:opacity-100 transition-opacity duration-200">
                  {formatTimestamp(msg.ts)}
                </span>
              </div>
            ))
          )}
          {isTyping && (
            <div className="flex items-start gap-2">
              <div className="bg-slate-50 text-slate-800 rounded-xl px-3 py-2 max-w-[85%]">
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

        {/* Input Wrapper */}
        <div className="sticky bottom-0 z-10 bg-white pt-2 mt-2 border-t border-slate-200">
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
    </div>
  );
}
