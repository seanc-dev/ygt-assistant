import { useEffect } from "react";
import { Button } from "./Button";

interface ToastProps {
  message: string;
  onDismiss: () => void;
  autoDismiss?: number;
}

export function Toast({ message, onDismiss, autoDismiss = 5000 }: ToastProps) {
  useEffect(() => {
    if (!autoDismiss) return;
    const id = window.setTimeout(onDismiss, autoDismiss);
    return () => window.clearTimeout(id);
  }, [autoDismiss, onDismiss]);

  return (
    <div
      role="status"
      aria-live="assertive"
      className="pointer-events-auto flex max-w-sm items-start gap-3 rounded-md border border-slate-200 bg-white p-4 shadow-lg dark:border-slate-700 dark:bg-slate-900"
    >
      <span className="flex-1 text-sm text-slate-900 dark:text-slate-100">{message}</span>
      <Button variant="ghost" onClick={onDismiss} className="px-2 py-1 text-xs">
        Dismiss
      </Button>
    </div>
  );
}
