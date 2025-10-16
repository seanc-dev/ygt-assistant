import { useState } from "react";
import { Layout } from "../components/Layout";
import { Card } from "../components/Card";

export default function ChatPage() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<{ role: string; content: string }[]>([]);
  const [approvals, setApprovals] = useState<any[]>([]);

  async function send() {
    const res = await fetch(
      `${process.env.NEXT_PUBLIC_ADMIN_API_BASE || "http://localhost:8000"}/chat`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: input }),
      }
    );
    const data = await res.json();
    setMessages((prev) => [...prev, { role: "user", content: input }, ...(data.messages || [])]);
    setApprovals(data.approvals || []);
    setInput("");
  }

  return (
    <Layout>
      <h1 className="mb-4 text-2xl font-semibold">Chat</h1>
      <div className="grid gap-3 md:grid-cols-3">
        <Card
          title="Assistant"
          subtitle="Type 'scan', 'approve <id>', or 'skip <id>'"
          actions={
            <div className="flex gap-2">
              <input
                className="w-full rounded border px-3 py-2 text-sm"
                placeholder="Type a message..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") send();
                }}
              />
              <button
                onClick={send}
                className="rounded bg-slate-900 px-3 py-1 text-sm text-white dark:bg-slate-100 dark:text-slate-900"
              >
                Send
              </button>
            </div>
          }
        >
          <div className="space-y-2">
            {messages.map((m, i) => (
              <div key={i} className="text-sm">
                <span className="font-semibold">{m.role}:</span> {m.content}
              </div>
            ))}
          </div>
        </Card>
        <Card title="Approvals" subtitle="Latest proposals">
          <div className="space-y-2">
            {approvals.map((a) => (
              <div key={a.id} className="rounded border p-2 text-sm">
                <div className="font-medium">{a.title || a.summary}</div>
                <div className="text-xs text-slate-500">{a.id} · {a.kind} · {a.status}</div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </Layout>
  );
}


