import { useState } from "react";
import { Button, Stack, Text, TextInput } from "@ygt-assistant/ui";
import { api } from "../lib/api";

interface Thread {
  id: string;
  task_id: string;
  title: string;
  messages: any[];
}

interface WorkroomChatProps {
  thread: Thread;
  onTaskStatusChange: (taskId: string, status: string) => void;
}

export function WorkroomChat({ thread, onTaskStatusChange }: WorkroomChatProps) {
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState(thread.messages || []);

  // Get task status from thread (we'll need to fetch this)
  const taskStatus = "todo"; // TODO: Get from thread context

  const handleSend = async () => {
    if (!message.trim()) return;

    // TODO: Send message via API
    const newMessage = {
      id: Date.now().toString(),
      role: "user",
      content: message,
      timestamp: new Date().toISOString(),
    };
    setMessages([...messages, newMessage]);
    setMessage("");
  };

  const handleStatusChange = (newStatus: string) => {
    onTaskStatusChange(thread.task_id, newStatus);
  };

  return (
    <div className="rounded-lg border flex flex-col h-[600px]">
      {/* Header with task controls */}
      <div className="border-b p-4 flex items-center justify-between">
        <div>
          <Text variant="label" className="text-sm font-medium">
            {thread.title}
          </Text>
        </div>
        <div className="flex gap-2">
          <select
            value={taskStatus}
            onChange={(e) => handleStatusChange(e.target.value)}
            className="text-xs border rounded px-2 py-1"
          >
            <option value="todo">To Do</option>
            <option value="doing">Doing</option>
            <option value="done">Done</option>
            <option value="blocked">Blocked</option>
          </select>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <Text variant="muted" className="text-sm">
            No messages yet. Start a conversation!
          </Text>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`p-2 rounded ${
                msg.role === "user" ? "bg-blue-50 ml-8" : "bg-gray-50 mr-8"
              }`}
            >
              <Text variant="body" className="text-sm">
                {msg.content}
              </Text>
              {msg.timestamp && (
                <Text variant="caption" className="text-xs text-gray-500 mt-1">
                  {new Date(msg.timestamp).toLocaleTimeString()}
                </Text>
              )}
            </div>
          ))
        )}
      </div>

      {/* Input */}
      <div className="border-t p-4">
        <div className="flex gap-2">
          <TextInput
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            placeholder="Type a message..."
            className="flex-1"
          />
          <Button onClick={handleSend}>Send</Button>
        </div>
      </div>
    </div>
  );
}
