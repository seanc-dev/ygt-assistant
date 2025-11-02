import { useState } from "react";

interface CompactChatProps {
  threadId?: string;
  onOpenInWorkroom?: () => void;
}

export function CompactChat({ threadId, onOpenInWorkroom }: CompactChatProps) {
  const [message, setMessage] = useState("");

  return (
    <div className="rounded-lg border p-4">
      <div className="mb-2 text-sm font-medium">Inline Chat</div>
      <div className="mb-2 text-xs text-gray-500">Stub - Phase 0</div>
      {threadId && <div className="text-xs">Thread: {threadId}</div>}
      {onOpenInWorkroom && (
        <button
          onClick={onOpenInWorkroom}
          className="mt-2 text-xs text-blue-600"
        >
          Open in Workroom
        </button>
      )}
    </div>
  );
}

