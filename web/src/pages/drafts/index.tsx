import { FormEvent, useCallback, useEffect, useState } from "react";
import {
  ActionBar,
  Badge,
  Button,
  Heading,
  Panel,
  Stack,
  Text,
} from "@lucid-work/ui";
import { Layout } from "../../components/Layout";
import { Field } from "../../components/Form/Field";
import { Textarea } from "../../components/Form/Textarea";
import { Toast } from "../../components/Toast";
import { buildApiUrl } from "../../lib/apiBase";

type Draft = {
  id: string;
  to: string[];
  subject: string;
  body: string;
  status?: string;
};

export default function DraftsPage() {
  const [items, setItems] = useState<Draft[]>([]);
  const [to, setTo] = useState("");
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [toast, setToast] = useState("");
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    const res = await fetch(buildApiUrl("/drafts"), {
      credentials: "include",
    });
    if (!res.ok) {
      setItems([]);
      return;
    }
    const data = await res.json();
    setItems(data || []);
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const createDraft = async (event: FormEvent) => {
    event.preventDefault();
    setLoading(true);
    try {
      await fetch(buildApiUrl("/email/drafts"), {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          to: to
            .split(",")
            .map((s) => s.trim())
            .filter(Boolean),
          subject,
          body,
        }),
      });
      setTo("");
      setSubject("");
      setBody("");
      setToast("Draft created");
      await load();
    } finally {
      setLoading(false);
    }
  };

  const sendViaOutlook = async (id: string) => {
    setToast("Sending via Outlook…");
    await fetch(buildApiUrl(`/email/send/${encodeURIComponent(id)}`), {
      method: "POST",
      credentials: "include",
    });
    setToast("Sent via Outlook");
    await load();
  };

  const sendViaTeams = async (id: string) => {
    setToast("Handing off to Teams…");
    await fetch(buildApiUrl("/teams/send/draft"), {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ draft_id: id }),
    }).catch(() => setToast("Teams handoff failed"));
    await load();
  };

  return (
    <Layout>
      <Stack gap="lg">
        <div className="flex flex-col gap-2">
          <Heading as="h1" variant="display">
            Drafts
          </Heading>
          <Text variant="muted">
            Compose once and ship anywhere. Copilot will surface Outlook and Teams ready states.
          </Text>
        </div>

        <Panel
          kicker="New draft"
          title="Compose"
          description="Provide recipients, subject, and body. Copilot keeps the same draft for every channel."
        >
          <form className="space-y-4" onSubmit={createDraft}>
            <Field
              value={to}
              onChange={(event) => setTo(event.target.value)}
              placeholder="Recipients (comma separated email addresses)"
            />
            <Field
              value={subject}
              onChange={(event) => setSubject(event.target.value)}
              placeholder="Subject"
            />
            <Textarea
              value={body}
              onChange={(event) => setBody(event.target.value)}
              placeholder="Add context for Copilot to personalize"
              rows={6}
            />
            <ActionBar
              helperText="Primary destination is Outlook. Teams stays one click away."
              primaryAction={
                <Button type="submit" disabled={loading || !subject.trim()}>
                  {loading ? "Creating…" : "Save draft"}
                </Button>
              }
              secondaryActions={[<span key="kb">Ctrl + Enter</span>]}
            />
          </form>
        </Panel>

        <Panel
          kicker="Workspace"
          title="Draft library"
          description="Send directly or open in your preferred client."
        >
          {items.length === 0 ? (
            <Text variant="muted">No drafts yet. Create one to see Outlook and Teams options.</Text>
          ) : (
            <Stack gap="md">
              {items.map((draft) => (
                <div
                  key={draft.id}
                  className="rounded-xl border border-[color:var(--ds-border-subtle)] bg-[color:var(--ds-surface)] p-4"
                >
                  <Stack gap="sm">
                    <div className="flex items-center justify-between gap-2">
                      <Text variant="label" className="text-[color:var(--ds-text-primary)]">
                        {draft.subject}
                      </Text>
                      <Badge tone="calm">Draft</Badge>
                    </div>
                    <Text variant="caption">To: {draft.to.join(", ") || "None"}</Text>
                    <Text variant="body" className="line-clamp-3">
                      {draft.body}
                    </Text>
                    <Stack direction="horizontal" gap="sm" wrap>
                      <Button onClick={() => sendViaOutlook(draft.id)}>Send via Outlook</Button>
                      <Button variant="outline" onClick={() => sendViaTeams(draft.id)}>
                        Share to Teams
                      </Button>
                      <Button variant="ghost" onClick={() => setToast("Undo via history")}>Undo</Button>
                    </Stack>
                  </Stack>
                </div>
              ))}
            </Stack>
          )}
        </Panel>
      </Stack>

      {toast ? <Toast message={toast} onClose={() => setToast("")} /> : null}
    </Layout>
  );
}
