import { useState, useRef, useEffect, KeyboardEvent } from "react";
import { api } from "../../lib/api";
import { applyDelta, deferTo } from "../../lib/schedule";

interface SmartCommandInputProps {
  itemId: string;
  start: string;
  end: string;
  onUpdate: (
    id: string,
    updates: { start?: string; end?: string; title?: string; note?: string }
  ) => Promise<void>;
  onOpenChat: () => void;
  onClose: () => void;
  centered?: boolean;
}

export function SmartCommandInput({
  itemId,
  start,
  end,
  onUpdate,
  onOpenChat,
  onClose,
  centered = false,
}: SmartCommandInputProps) {
  const [command, setCommand] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    // Focus input when component mounts
    inputRef.current?.focus();
  }, []);

  useEffect(() => {
    if (confirmation) {
      const timer = setTimeout(() => {
        setConfirmation("");
      }, 2500);
      return () => clearTimeout(timer);
    }
  }, [confirmation]);

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    // Allow keyboard shortcuts to pass through
    if (e.key === "[" || e.key === "]" || e.key === "-" || e.key === "=") {
      // Let parent handle these shortcuts
      return;
    }

    if (e.key === "Escape") {
      e.preventDefault();
      setCommand("");
      onClose();
    } else if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    } else if (e.key === "Enter" && e.shiftKey) {
      e.preventDefault();
      // Convert Shift+Enter to space
      setCommand((prev) => prev + " ");
    }
  };

  const handleSubmit = async () => {
    if (!command.trim() || isSubmitting) return;

    setIsSubmitting(true);
    try {
      const response = await api.interpretScheduleCommand({
        eventId: itemId,
        text: command.trim(),
      });

      if (response.action === "open_chat" || response.action === "unknown") {
        // Show hint to open full chat
        onOpenChat();
        setCommand("");
        setIsSubmitting(false);
        return;
      }

      // Apply structural changes
      const updates: {
        start?: string;
        end?: string;
        title?: string;
        note?: string;
      } = {};

      if (response.action === "shift" && response.deltaMinutes !== undefined) {
        const delta = applyDelta({ start, end }, response.deltaMinutes);
        updates.start = delta.start;
        updates.end = delta.end;
      } else if (
        response.action === "resize" &&
        response.start &&
        response.end
      ) {
        updates.start = response.start;
        updates.end = response.end;
      } else if (response.action === "defer") {
        const period =
          response.period === "afternoon" ? "afternoon" : "tomorrow_morning";
        const deferred = deferTo({ start, end }, period);
        updates.start = deferred.start;
        updates.end = deferred.end;
      } else if (response.action === "rename" && response.title) {
        updates.title = response.title;
      } else if (response.action === "note" && response.note) {
        updates.note = response.note;
      }

      if (Object.keys(updates).length > 0) {
        await onUpdate(itemId, updates);
        setConfirmation(response.confirmation || "Updated");
      } else {
        setConfirmation(response.confirmation || "No changes needed");
      }

      setCommand("");
    } catch (error) {
      console.error("Failed to interpret command:", error);
      setConfirmation(
        "Sorry, I didn't understand that. Try 'Open full chat' for help."
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className={`mt-2 w-full ${centered ? "mx-auto max-w-[52ch]" : ""}`}>
      <div
        className="group relative w-full rounded-lg border border-slate-300 bg-white px-3 py-2 shadow-sm focus-within:border-blue-500 focus-within:ring-2 focus-within:ring-blue-500 focus-within:ring-offset-2 transition cursor-text"
        onClick={(e) => {
          // Focus input when clicking container
          e.stopPropagation();
          inputRef.current?.focus();
        }}
      >
        <div className="relative flex items-center">
          <input
            ref={inputRef}
            type="text"
            value={command}
            onChange={(e) => setCommand(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Message Assistant about this block…"
            className="w-full bg-transparent outline-none placeholder:text-slate-400 text-slate-800 text-sm overflow-x-auto whitespace-nowrap focus:shadow-none focus-visible:ring-0 focus-visible:shadow-none"
            style={{ minWidth: 0 }}
            aria-label="Message Assistant about this block"
            disabled={isSubmitting}
          />
          <button
            onClick={(e) => {
              e.stopPropagation();
              onOpenChat();
            }}
            className="absolute right-3 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 transition-opacity text-xs text-sky-700 hover:text-sky-900 whitespace-nowrap bg-white/90 px-2 py-0.5 rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
            aria-label="Open full chat for this block"
          >
            Open full chat ↩︎
          </button>
        </div>
      </div>
      {confirmation && (
        <div
          className="mt-1 text-sm text-slate-600"
          aria-live="polite"
          role="status"
        >
          {confirmation}
        </div>
      )}
    </div>
  );
}
