import { useEffect, useState } from "react";

export function Toast({ message, onClose, duration = 3000 }: { message: string; onClose: () => void; duration?: number }) {
  const [open, setOpen] = useState(true);
  useEffect(() => {
    const t = setTimeout(() => {
      setOpen(false);
      onClose();
    }, duration);
    return () => clearTimeout(t);
  }, [duration, onClose]);
  if (!open) return null;
  return (
    <div className="fixed bottom-4 left-1/2 z-50 -translate-x-1/2 rounded bg-slate-900 px-4 py-2 text-sm text-white shadow-lg dark:bg-slate-100 dark:text-slate-900">
      {message}
    </div>
  );
}
