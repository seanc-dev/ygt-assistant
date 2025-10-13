import { useEffect, useState } from "react";
import { api } from "../../lib/api";

type Approval = {
  id: string;
  kind?: string;
  title?: string;
  summary?: string;
  status?: string;
};

export default function ReviewPage() {
  const [filter, setFilter] = useState<string>("all");
  const [items, setItems] = useState<Approval[]>([]);
  const [loading, setLoading] = useState<boolean>(false);

  const load = async (f: string) => {
    setLoading(true);
    try {
      const res = await api.approvals(f);
      setItems(res || []);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load(filter);
  }, [filter]);

  const onApprove = async (id: string) => {
    await api.approve(id);
    await load(filter);
  };
  const onEdit = async (id: string) => {
    await api.edit(id, "tweak");
    await load(filter);
  };
  const onSkip = async (id: string) => {
    await api.skip(id);
    await load(filter);
  };
  const onUndo = async (id: string) => {
    await api.undo(id);
    await load(filter);
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-semibold">To review</h1>
      <div className="mt-4 flex items-center gap-3">
        {[
          { k: "all", label: "All" },
          { k: "email", label: "Email" },
          { k: "calendar", label: "Calendar" },
        ].map((t) => (
          <button
            key={t.k}
            onClick={() => setFilter(t.k)}
            className={`rounded px-3 py-1 text-sm ${
              filter === t.k ? "bg-slate-900 text-white" : "bg-slate-100"
            }`}
          >
            {t.label}
          </button>
        ))}
        <button
          onClick={async () => {
            await api.scan(["email", "calendar"]);
            await load(filter);
          }}
          className="ml-auto rounded bg-primary-600 px-3 py-1 text-sm text-white"
        >
          Scan
        </button>
      </div>

      <div className="mt-6 space-y-3">
        {loading ? (
          <p className="text-sm text-gray-500">Loading…</p>
        ) : items.length === 0 ? (
          <p className="text-sm text-gray-500">No approvals.</p>
        ) : (
          items.map((a) => (
            <div key={a.id} className="rounded border p-4">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <div className="text-sm text-gray-500">{a.kind || "proposal"}</div>
                  <div className="text-lg font-medium">{a.title || a.summary || a.id}</div>
                  <div className="text-xs text-gray-500">{a.status}</div>
                </div>
                <div className="flex gap-2">
                  <button onClick={() => onApprove(a.id)} className="rounded bg-green-600 px-2 py-1 text-white text-sm">Approve</button>
                  <button onClick={() => onEdit(a.id)} className="rounded bg-amber-600 px-2 py-1 text-white text-sm">Edit</button>
                  <button onClick={() => onSkip(a.id)} className="rounded bg-gray-300 px-2 py-1 text-sm">Skip</button>
                  <button onClick={() => onUndo(a.id)} className="rounded bg-slate-200 px-2 py-1 text-sm">Undo</button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
