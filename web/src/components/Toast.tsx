import { useEffect, useState } from "react";
import { Panel, Text } from "@ygt-assistant/ui";

type ToastProps = {
  message: string;
  onClose: () => void;
  duration?: number;
};

export function Toast({ message, onClose, duration = 3000 }: ToastProps) {
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
    <div className="pointer-events-none fixed inset-x-0 bottom-4 z-50 flex justify-center px-4">
      <div className="pointer-events-auto w-full max-w-sm">
        <Panel tone="soft">
          <Text variant="body" className="text-[color:var(--ds-text-primary)]">
            {message}
          </Text>
        </Panel>
      </div>
    </div>
  );
}
