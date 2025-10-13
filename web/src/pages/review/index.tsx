import { useEffect, useState, useCallback } from "react";
import { api } from "../../lib/api";
import { Layout } from "../../components/Layout";
import { Card } from "../../components/Card";
import { Toast } from "../../components/Toast";

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
  const [toast, setToast] = useState<string>("");

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

  // Optimistic action helpers
  const optimistic = (id: string, status: string) => {
    setItems((prev) => prev.map((a) => (a.id === id ? { ...a, status } : a)));
  };

  const onApprove = async (id: string) => {
    optimistic(id, "approved");
    setToast("Approved. Press U to Undo");
    try {
      await api.approve(id);
    } catch {
      await load(filter);
    }
  };
  const onEdit = async (id: string) => {
    optimistic(id, "edited");
    setToast("Edited");
    try {
      await api.edit(id, "tweak");
    } catch {
      await load(filter);
    }
  };
  const onSkip = async (id: string) => {
    optimistic(id, "skipped");
    setToast("Skipped");
    try {
      await api.skip(id);
    } catch {
      await load(filter);
    }
  };
  const onUndo = async (id: string) => {
    optimistic(id, "proposed");
    setToast("Undone");
    try {
      await api.undo(id);
    } catch {
      await load(filter);
    }
  };

  // Keyboard shortcuts for first item (A/E/S/U)
  const keyHandler = useCallback(
    (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement)?.tagName;
      if (["INPUT", "TEXTAREA"].includes(tag || "")) return;
      const first = items[0];
      if (!first) return;
      if (e.key.toLowerCase() === "a") onApprove(first.id);
      if (e.key.toLowerCase() === "e") onEdit(first.id);
      if (e.key.toLowerCase() === "s") onSkip(first.id);
      if (e.key.toLowerCase() === "u") onUndo(first.id);
    },
    [items]
  );

  useEffect(() => {
    window.addEventListener("keydown", keyHandler);
    return () => window.removeEventListener("keydown", keyHandler);
  }, [keyHandler]);

  return (
    <Layout>
      <h1 className="mb-4 text-2xl font-semibold">To review</h1>
      <Card
        title="Approvals"
        subtitle="Review the most important suggestions"
        actions={
          <button
            onClick={async () => {
              await api.scan(["email", "calendar"]);
              await load(filter);
            }}
            className="rounded bg-slate-900 px-3 py-1 text-sm text-white dark:bg-slate-100 dark:text-slate-900"
          >
            Scan
          </button>
        }
      >
        <div className="mb-4 flex items-center gap-2">
          {[
            { k: "all", label: "All" },
            { k: "email", label: "Email" },
            { k: "calendar", label: "Calendar" },
          ].map((t) => (
            <button
              key={t.k}
              onClick={() => setFilter(t.k)}
              className={`rounded px-3 py-1 text-sm ${
                filter === t.k
                  ? "bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900"
                  : "bg-slate-100 dark:bg-slate-800"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        <div className="space-y-3">
          {loading ? (
            <p className="text-sm text-gray-500">Loading…</p>
          ) : items.length === 0 ? (
            <p className="text-sm text-gray-500">No approvals.</p>
          ) : (
            items.map((a) => (
              <Card
                key={a.id}
                title={a.title || a.summary || a.id}
                subtitle={a.kind || "proposal"}
                actions={
                  <div className="flex gap-2">
                    <button
                      onClick={() => onApprove(a.id)}
                      className="rounded bg-green-600 px-2 py-1 text-white text-sm"
                    >
                      Approve
                    </button>
                    <button
                      onClick={() => onEdit(a.id)}
                      className="rounded bg-amber-600 px-2 py-1 text-white text-sm"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => onSkip(a.id)}
                      className="rounded bg-slate-200 px-2 py-1 text-sm"
                    >
                      Skip
                    </button>
                    <button
                      onClick={() => onUndo(a.id)}
                      className="rounded bg-slate-100 px-2 py-1 text-sm"
                    >
                      Undo
                    </button>
                  </div>
                }
              />
            ))
          )}
        </div>
      </Card>
      {toast && <Toast message={toast} onClose={() => setToast("")} />}
    </Layout>
  );
}
