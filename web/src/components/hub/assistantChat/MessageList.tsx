import { memo, useCallback, useEffect, useState } from "react";
import type { MutableRefObject } from "react";
import { ArrowClockwise24Regular } from "@fluentui/react-icons";
import type { SurfaceNavigateTo } from "../../../lib/llm/surfaces";
import type { MessageView } from "./types";
import { AssistantSurfacesRenderer } from "../../assistant/AssistantSurfacesRenderer";
import { ActionEmbedComponent } from "../../workroom/ActionEmbed";

type MessageListProps = {
  messageViews: MessageView[];
  isTyping: boolean;
  onRetryMessage: (id: string) => void;
  onEmbedUpdate: (messageId: string, embed: any) => void;
  animatedRef: MutableRefObject<Set<string>>;
  activeAssistantId: string | null;
  onInvokeSurfaceOp?: (opToken: string, options?: { confirm?: boolean }) => void;
  onNavigateSurface?: (nav: SurfaceNavigateTo) => void;
};

export const MessageList = memo((props: MessageListProps) => {
  const {
    messageViews,
    isTyping,
    onRetryMessage,
    onEmbedUpdate,
    animatedRef,
    activeAssistantId,
    onInvokeSurfaceOp,
    onNavigateSurface,
  } = props;

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
});
MessageList.displayName = "MessageList";

type MessageItemProps = {
  view: MessageView;
  onRetry: (id: string) => void;
  onEmbedUpdate: (messageId: string, embed: any) => void;
  animatedRef: MutableRefObject<Set<string>>;
  activeAssistantId: string | null;
  onInvokeSurfaceOp?: (opToken: string, options?: { confirm?: boolean }) => void;
  onNavigateSurface?: (nav: SurfaceNavigateTo) => void;
};

const MessageItem = memo((props: MessageItemProps) => {
  const {
    view,
    onRetry,
    onEmbedUpdate,
    animatedRef,
    activeAssistantId,
    onInvokeSurfaceOp,
    onNavigateSurface,
  } = props;

  return (
    <div
      className={`flex flex-col gap-0.5 transition-all duration-300 w-full ${
        view.role === "user" ? "items-end" : "items-start"
      } ${view.marginTop}`}
    >
      <div
        className={`flex items-end gap-2 ${
          view.role === "user" ? "justify-end flex-row-reverse" : "justify-start"
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
            view.role === "assistant"
              ? "bg-slate-100 text-slate-900 border border-slate-200"
              : view.error
              ? "bg-red-50 text-red-900 border border-red-200"
              : "bg-blue-500 text-white"
          } max-w-[80%]`}
          style={{
            wordWrap: "break-word",
            overflowWrap: "break-word",
            minWidth: "fit-content",
          }}
        >
          <div className="text-sm leading-relaxed" style={{ wordBreak: "normal" }}>
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
        <span className="text-xs text-slate-500 mt-1">{view.timestampLabel}</span>
      )}
    </div>
  );
}, areMessageItemPropsEqual);
MessageItem.displayName = "MessageItem";

function areMessageItemPropsEqual(
  prevProps: MessageItemProps,
  nextProps: MessageItemProps
) {
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

type TypingMessageContentProps = {
  content: string;
  id: string;
  shouldAnimate: boolean;
    animatedRef: MutableRefObject<Set<string>>;
  startDelayMs?: number;
  activeAssistantId: string | null;
};

const TypingMessageContent = memo((props: TypingMessageContentProps) => {
  const {
    content,
    id,
    shouldAnimate,
    animatedRef,
    startDelayMs = 0,
    activeAssistantId,
  } = props;

  const markAsSeen = useCallback(() => {
    animatedRef.current.add(id);
  }, [id, animatedRef]);

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
});
TypingMessageContent.displayName = "TypingMessageContent";

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

  // Handle interruption
  useEffect(() => {
    if (
      interruptKey !== undefined &&
      interruptKey !== null &&
      enabled &&
      hasStarted &&
      displayedText.length < text.length
    ) {
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
      if (onComplete && text.length > 0) {
        onComplete();
      }
      return;
    }

    if (!hasStarted && startDelayMs > 0) {
      const delayTimeout = setTimeout(() => {
        setHasStarted(true);
      }, startDelayMs);
      return () => clearTimeout(delayTimeout);
    }

    if (hasStarted && displayedText.length < text.length) {
      const timeout = setTimeout(() => {
        const newLength = displayedText.length + 1;
        setDisplayedText(text.slice(0, newLength));

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

  useEffect(() => {
    if (text !== displayedText && displayedText.length === text.length) {
      setDisplayedText("");
      setHasStarted(false);
    }
  }, [text, displayedText]);

  return displayedText || "";
}

