import { ReactNode, useEffect } from "react";

type ModalShellProps = {
  title: string;
  onClose: () => void;
  children: ReactNode;
};

export function ModalShell({ title, onClose, children }: ModalShellProps) {
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

