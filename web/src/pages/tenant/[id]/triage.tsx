import Link from "next/link";
import { useRouter } from "next/router";
import { useState } from "react";
import { api } from "../../../lib/api";
import { Button } from "../../../components/Button";
import { Field } from "../../../components/Form/Field";
import { Label } from "../../../components/Form/Label";
import { Textarea } from "../../../components/Form/Textarea";
import { Badge } from "../../../components/Badge";

const defaultForm = {
  message_id: "",
  sender: "",
  subject: "",
  body_text: "",
  received_at: "",
};

type DryRunResponse = {
  triage?: unknown;
  [key: string]: unknown;
};

export default function Triage() {
  const router = useRouter();
  const { id: rawId } = router.query;
  const id = typeof rawId === "string" ? rawId : "";
  const [form, setForm] = useState(defaultForm);
  const [result, setResult] = useState<DryRunResponse | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleChange = (key: keyof typeof defaultForm, value: string) => {
    setForm((previous) => ({ ...previous, [key]: value }));
  };

  const handleSubmit = async () => {
    if (!id) return;
    setIsSubmitting(true);
    setResult(null);
    try {
      const response = await api.triageDryRun(id, form);
      setResult(response);
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Request failed. Please try again.";
      setResult({ error: message });
    } finally {
      setIsSubmitting(false);
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
              <h1 className="text-3xl font-semibold text-slate-900">Triage dry-run — {id}</h1>
              <Badge tone="info">Preview</Badge>
            </div>
            <p className="text-sm text-slate-600">
              Test how incoming email metadata will be triaged before enabling it for clients.
            </p>
          </header>

          <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              {["message_id", "sender", "subject", "received_at"].map((key) => (
                <div key={key} className="space-y-2">
                  <Label htmlFor={key}>{key.replace(/_/g, " ")}</Label>
                  <Field
                    id={key}
                    value={form[key as keyof typeof defaultForm]}
                    onChange={(event) =>
                      handleChange(key as keyof typeof defaultForm, event.target.value)
                    }
                  />
                </div>
              ))}
            </div>
            <div className="mt-4 space-y-2">
              <Label htmlFor="body_text">Body text</Label>
              <Textarea
                id="body_text"
                className="h-48 font-mono"
                value={form.body_text}
                onChange={(event) => handleChange("body_text", event.target.value)}
                placeholder="Paste the plain-text email body"
              />
            </div>
            <div className="mt-4 flex flex-wrap items-center gap-3">
              <Button onClick={handleSubmit} disabled={isSubmitting}>
                {isSubmitting ? "Running…" : "Run dry-run"}
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setForm(defaultForm);
                  setResult(null);
                }}
              >
                Reset form
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

          {result ? (
            <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
              <h2 className="text-lg font-semibold text-slate-900">Result</h2>
              <p className="mt-1 text-sm text-slate-600">
                Review the response from the triage service to understand how the email will be
                handled.
              </p>
              <pre className="mt-4 max-h-[480px] overflow-auto rounded border border-slate-200 bg-slate-950/90 p-4 text-xs text-slate-100">
{JSON.stringify(result.triage ?? result, null, 2)}
              </pre>
            </section>
          ) : null}
        </div>
      </main>
    </div>
  );
}
