import { useEffect, useState } from "react";
import { api } from "../../lib/api";

type Draft = { id: string; to: string[]; subject: string; body: string; status?: string };

export default function DraftsPage() {
  const [items, setItems] = useState<Draft[]>([]);
  const [to, setTo] = useState<string>("");
  const [subject, setSubject] = useState<string>("");
  const [body, setBody] = useState<string>("");

  const load = async () => {
    const res = await apiGetDrafts();
    setItems(res || []);
  };

  useEffect(() => {
    load();
  }, []);

  const apiGetDrafts = async () => {
    const res = await fetch(`${process.env.NEXT_PUBLIC_ADMIN_API_BASE || "https://api.coachflow.nz"}/drafts`, { credentials: "include" });
    if (!res.ok) return [];
    return res.json();
  };

  const createDraft = async () => {
    await fetch(`${process.env.NEXT_PUBLIC_ADMIN_API_BASE || "https://api.coachflow.nz"}/email/drafts`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ to: to.split(",").map((s) => s.trim()).filter(Boolean), subject, body }),
    });
    setTo("");
    setSubject("");
    setBody("");
    await load();
  };

  const sendDraft = async (id: string) => {
    await fetch(`${process.env.NEXT_PUBLIC_ADMIN_API_BASE || "https://api.coachflow.nz"}/email/send/${encodeURIComponent(id)}`, {
      method: "POST",
      credentials: "include",
    });
    await load();
  };

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Drafts</h1>
        <p className="text-gray-600 mt-2">Create and send email drafts</p>
      </div>

      <div className="rounded border p-4 space-y-3">
        <div className="text-sm font-medium">New draft</div>
        <input value={to} onChange={(e) => setTo(e.target.value)} placeholder="To (comma-separated)" className="w-full rounded border px-2 py-1" />
        <input value={subject} onChange={(e) => setSubject(e.target.value)} placeholder="Subject" className="w-full rounded border px-2 py-1" />
        <textarea value={body} onChange={(e) => setBody(e.target.value)} placeholder="Body" className="w-full rounded border px-2 py-1" rows={6} />
        <button onClick={createDraft} className="rounded bg-slate-900 px-3 py-1 text-white text-sm">Create</button>
      </div>

      <div className="space-y-3">
        {items.length === 0 ? (
          <p className="text-sm text-gray-500">No drafts.</p>
        ) : (
          items.map((d) => (
            <div key={d.id} className="rounded border p-4">
              <div className="flex items-start justify-between">
                <div>
                  <div className="text-sm text-gray-500">{d.to.join(", ")}</div>
                  <div className="text-lg font-medium">{d.subject}</div>
                  <div className="text-xs text-gray-500">{d.status || "draft"}</div>
                </div>
                <div className="flex gap-2">
                  <button onClick={() => sendDraft(d.id)} className="rounded bg-green-600 px-2 py-1 text-white text-sm">Send</button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
