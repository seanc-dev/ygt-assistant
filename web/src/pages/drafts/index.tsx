import { useEffect, useState } from "react";
import { api } from "../../lib/api";
import { Layout } from "../../components/Layout";
import { Card } from "../../components/Card";

type Draft = { id: string; to: string[]; subject: string; body: string; status?: string };

export default function DraftsPage() {
  const [items, setItems] = useState<Draft[]>([]);
  const [to, setTo] = useState<string>("");
  const [subject, setSubject] = useState<string>("");
  const [body, setBody] = useState<string>("");
  const [waNumber, setWaNumber] = useState<string>("");

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
    <Layout>
      <h1 className="mb-4 text-2xl font-semibold">Drafts</h1>
      <Card title="New draft" subtitle="Compose and send">
        <div className="space-y-3">
          <input value={to} onChange={(e) => setTo(e.target.value)} placeholder="To (comma-separated)" className="w-full rounded border px-3 py-2" />
          <input value={subject} onChange={(e) => setSubject(e.target.value)} placeholder="Subject" className="w-full rounded border px-3 py-2" />
          <textarea value={body} onChange={(e) => setBody(e.target.value)} placeholder="Body" className="w-full rounded border px-3 py-2" rows={6} />
          <div className="flex gap-2">
            <button onClick={createDraft} className="rounded bg-slate-900 px-3 py-2 text-white text-sm dark:bg-slate-100 dark:text-slate-900">Create</button>
          </div>
        </div>
      </Card>
      <div className="mt-4 space-y-3">
        {items.length === 0 ? (
          <Card title="No drafts" subtitle="Create a draft to get started" />
        ) : (
          items.map((d) => (
            <Card
              key={d.id}
              title={d.subject}
              subtitle={d.to.join(", ")}
              actions={
                <div className="flex items-center gap-2">
                  <button onClick={() => sendDraft(d.id)} className="rounded bg-green-600 px-3 py-2 text-white text-sm">Send</button>
                  <input value={waNumber} onChange={(e) => setWaNumber(e.target.value)} placeholder="WhatsApp number" className="rounded border px-2 py-1 text-sm" />
                  <button
                    onClick={async () => {
                      if (!waNumber) return;
                      await fetch(`${process.env.NEXT_PUBLIC_ADMIN_API_BASE || "https://api.coachflow.nz"}/whatsapp/send/draft`, {
                        method: "POST",
                        credentials: "include",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ to: waNumber, draft_id: d.id }),
                      });
                    }}
                    className="rounded bg-slate-200 px-3 py-2 text-sm"
                  >
                    Send via WhatsApp
                  </button>
                </div>
              }
            >
              <p className="text-sm text-slate-600 dark:text-slate-400 line-clamp-3">{d.body}</p>
            </Card>
          ))
        )}
      </div>
    </Layout>
  );
}
