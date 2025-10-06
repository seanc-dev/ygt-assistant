import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/router";
import useSWR from "swr";
import { api } from "../../../lib/api";
import { Button } from "../../../components/Button";
import { Textarea } from "../../../components/Form/Textarea";
import { Badge } from "../../../components/Badge";

export default function Rules() {
  const router = useRouter();
  const { id: rawId } = router.query;
  const id = typeof rawId === "string" ? rawId : "";
  const { data, mutate } = useSWR(id ? ["rules", id] : null, () => api.getRules(id));
  const [yaml, setYaml] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    if (data?.yaml !== undefined) {
      setYaml(data.yaml ?? "");
    }
  }, [data]);

  const handleSave = async () => {
    if (!id) return;
    setIsSaving(true);
    setMessage(null);
    try {
      await api.setRules(id, yaml);
      await mutate();
      setMessage("Rules saved");
    } catch (error) {
      const text =
        error instanceof Error ? error.message : "Save failed. Please try again.";
      setMessage(text);
    } finally {
      setIsSaving(false);
    }
  };

  if (!id) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-50">
        <p className="text-sm text-slate-500">Loading…</p>
      </main>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <main className="mx-auto max-w-5xl px-4 py-10 sm:px-6">
        <div className="flex flex-col gap-6">
          <header className="space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="text-3xl font-semibold text-slate-900">Rules — {id}</h1>
              <Badge tone="info">YAML</Badge>
            </div>
            <p className="text-sm text-slate-600">
              Edit the automation rules for this tenant. Changes apply immediately after you
              save.
            </p>
          </header>

          {message ? (
            <div className="rounded-lg border border-slate-200 bg-white p-4 text-sm text-slate-700 shadow-sm">
              {message}
            </div>
          ) : null}

          <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
            <Textarea
              value={yaml}
              onChange={(event) => setYaml(event.target.value)}
              className="h-96 font-mono"
              placeholder="Paste YAML here"
            />
            <div className="mt-4 flex flex-wrap items-center gap-3">
              <Button onClick={handleSave} disabled={isSaving}>
                {isSaving ? "Saving…" : "Save"}
              </Button>
              <Link
                href={`/tenant/${id}/setup`}
                className="focus-outline inline-flex items-center rounded-md border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 shadow-sm transition hover:border-primary-300 hover:text-primary-700"
              >
                Back to setup
              </Link>
              <Link
                href="/"
                className="focus-outline inline-flex items-center rounded-md border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 shadow-sm transition hover:border-primary-300 hover:text-primary-700"
              >
                Back to tenants
              </Link>
            </div>
          </section>
        </div>
      </main>
    </div>
  );
}
