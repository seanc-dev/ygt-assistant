import { useState } from "react";
import { Button } from "@ygt-assistant/ui/primitives/Button";
import { Dismiss24Regular, Pin24Regular } from "@fluentui/react-icons";
import type { ChatMeta } from "../../hooks/useWorkroomStore";

interface ChatTabsProps {
  chats: ChatMeta[];
  activeChatId: string | null;
  onSelectChat: (chatId: string) => void;
  onCloseChat: (chatId: string) => void;
  onPinChat?: (chatId: string) => void;
  onCreateChat?: () => void;
  loading?: boolean;
  creating?: boolean;
}

export function ChatTabs({
  chats,
  activeChatId,
  onSelectChat,
  onCloseChat,
  onPinChat,
  onCreateChat,
  loading = false,
  creating = false,
}: ChatTabsProps) {
  const sortedChats = [...chats].sort((a, b) => {
    if (a.pinned && !b.pinned) return -1;
    if (!a.pinned && b.pinned) return 1;
    const aTime = a.lastMessageAt ? new Date(a.lastMessageAt).getTime() : 0;
    const bTime = b.lastMessageAt ? new Date(b.lastMessageAt).getTime() : 0;
    return bTime - aTime;
  });

  return (
    <div className="flex items-center gap-1 border-b border-slate-200 bg-slate-50 overflow-x-auto flex-shrink-0">
      {loading && chats.length === 0 ? (
        <div className="px-3 py-2 text-xs text-slate-500">
          Loading chats...
        </div>
      ) : (
        sortedChats.map((chat) => (
        <div
          key={chat.id}
          className={`flex items-center gap-1 px-3 py-2 text-sm border-b-2 cursor-pointer transition-colors ${
            activeChatId === chat.id
              ? "border-blue-500 bg-white text-blue-600"
              : "border-transparent text-slate-600 hover:text-slate-900"
          }`}
          onClick={() => onSelectChat(chat.id)}
        >
          {chat.pinned && <Pin24Regular className="w-3 h-3 text-slate-400" />}
          <span className="truncate max-w-[120px]">{chat.title}</span>
          <button
            onClick={(e) => {
              e.stopPropagation();
              onCloseChat(chat.id);
            }}
            className="ml-1 text-slate-400 hover:text-slate-600"
          >
            <Dismiss24Regular className="w-3 h-3" />
          </button>
        </div>
      )))}
      {onCreateChat && (
        <button
          onClick={onCreateChat}
          disabled={creating}
          className="px-3 py-2 text-sm text-slate-600 hover:text-slate-900 border-b-2 border-transparent disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {creating ? "Creating..." : "+ New Chat"}
        </button>
      )}
    </div>
  );
}
