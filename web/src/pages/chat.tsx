import { FormEvent, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/router";
import {
  ActionBar,
  Badge,
  Button,
  Heading,
  Panel,
  Stack,
  Text,
} from "@lucid-work/ui";
import { api } from "../lib/api";
import { Layout } from "../components/Layout";
import { Toast } from "../components/Toast";
import { Textarea } from "../components/Form/Textarea";

type MessageEntry = {
  id: string;
  type: "message";
  role: "user" | "assistant" | "system";
  content: string;
};

type ApprovalEntry = {
  id: string;
  type: "approval";
  approvalId: string;
  title?: string;
  summary?: string;
  status?: string;
};

type DraftEntry = {
  id: string;
  type: "draft";
  draftId: string;
  subject: string;
  to: string[];
  status?: string;
};

type TimelineEntry = MessageEntry | ApprovalEntry | DraftEntry;

function createId() {
  return Math.random().toString(36).slice(2);
}

export default function ChatPage() {
  const router = useRouter();
  const [input, setInput] = useState("");
  const [timeline, setTimeline] = useState<TimelineEntry[]>([]);
  const [pending, setPending] = useState(false);
  const [toast, setToast] = useState("");

  const send = async (event?: FormEvent) => {
    event?.preventDefault();
    if (!input.trim()) return;
    const text = input.trim();
    const userEntry: MessageEntry = {
      id: createId(),
      type: "message",
      role: "user",
      content: text,
    };
    setTimeline((prev) => [...prev, userEntry]);
    setInput("");
    setPending(true);

    try {
      const res = await fetch(
        `${
          process.env.NEXT_PUBLIC_ADMIN_API_BASE || "http://localhost:8000"
        }/chat`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text }),
        }
      );
      const data = await res.json();
      const entries: TimelineEntry[] = [];

      (data.messages || []).forEach((message: any) => {
        entries.push({
          id: createId(),
          type: "message",
          role: message.role || "assistant",
          content: message.content || "",
        });
      });

      (data.approvals || []).forEach((item: any) => {
        entries.push({
          id: createId(),
          type: "approval",
          approvalId: item.id,
          title: item.title || item.summary || item.id,
          summary: item.summary,
          status: item.status || "proposed",
        });
      });

      (data.drafts || []).forEach((draft: any) => {
        entries.push({
          id: createId(),
          type: "draft",
          draftId: draft.id,
          subject: draft.subject || "Untitled draft",
          to: draft.to || [],
          status: draft.status,
        });
      });

      setTimeline((prev) => [...prev, ...entries]);
    } catch (error) {
      const failure: MessageEntry = {
        id: createId(),
        type: "message",
        role: "system",
        content: `Failed to reach assistant: ${String(error)}`,
      };
      setTimeline((prev) => [...prev, failure]);
    } finally {
      setPending(false);
    }
  };

  const updateEntryStatus = (id: string, status: string) => {
    setTimeline((prev) =>
      prev.map((entry) =>
        entry.id === id
          ? entry.type === "approval"
            ? { ...entry, status }
            : entry.type === "draft"
            ? { ...entry, status }
            : entry
          : entry
      )
    );
  };

  const handleApprove = async (entry: ApprovalEntry) => {
    updateEntryStatus(entry.id, "approved");
    setToast("Approved. Tap undo if needed.");
    try {
      await api.approve(entry.approvalId);
    } catch {
      updateEntryStatus(entry.id, entry.status || "proposed");
      setToast("Approval failed");
    }
  };

  const handleSkip = async (entry: ApprovalEntry) => {
    updateEntryStatus(entry.id, "skipped");
    setToast("Skipped. Undo available in history.");
    try {
      await api.skip(entry.approvalId);
    } catch {
      updateEntryStatus(entry.id, entry.status || "proposed");
      setToast("Skip failed");
    }
  };

  const handleUndoApproval = async (entry: ApprovalEntry) => {
    setToast("Undoing approval");
    try {
      await api.undo(entry.approvalId);
      updateEntryStatus(entry.id, "proposed");
      setToast("Approval undone");
    } catch {
      setToast("Unable to undo");
    }
  };

  const microsoftCue = useMemo(
    () => ({
      message: "Connected to Microsoft Graph",
      detail: "Sync freshness under 2 minutes",
    }),
    []
  );

  return (
    <Layout>
      <Stack gap="lg">
        <div className="flex flex-col gap-2">
          <Heading as="h1" variant="display">
            Copilot timeline
          </Heading>
          <Text variant="muted">
            Ask questions, approve inline, and keep context flowing without leaving this page.
          </Text>
        </div>

        <Panel tone="calm" kicker="Microsoft Graph">
          <Stack direction="horizontal" justify="between" align="center" wrap>
            <div>
              <Text variant="label" className="text-[color:var(--ds-text-primary)]">
                {microsoftCue.message}
              </Text>
              <Text variant="caption">{microsoftCue.detail}</Text>
            </div>
            <Badge tone="success">Healthy</Badge>
          </Stack>
        </Panel>

        <Panel title="Conversation" description="Newest interactions appear at the end." tone="soft">
          {timeline.length === 0 ? (
            <Text variant="muted">No messages yet. Ask Copilot to scan, summarize, or draft.</Text>
          ) : (
            <Stack gap="md">
              {timeline.map((entry) => {
                if (entry.type === "message") {
                  return (
                    <div
                      key={entry.id}
                      className="rounded-lg border border-[color:var(--ds-border-subtle)] bg-[color:var(--ds-surface)] p-4"
                    >
                      <div className="flex items-center justify-between">
                        <Badge tone={entry.role === "user" ? "neutral" : entry.role === "assistant" ? "calm" : "warning"}>
                          {entry.role === "assistant" ? "Copilot" : entry.role.charAt(0).toUpperCase() + entry.role.slice(1)}
                        </Badge>
                        <Text variant="caption">{entry.role === "user" ? "You" : "Assistant"}</Text>
                      </div>
                      <Text variant="body" className="mt-2">
                        {entry.content}
                      </Text>
                    </div>
                  );
                }

                if (entry.type === "approval") {
                  return (
                    <div
                      key={entry.id}
                      className="rounded-xl border border-[color:var(--ds-border-prominent)] bg-[color:var(--ds-surface)] p-4 shadow-sm"
                    >
                      <Stack gap="sm">
                        <div className="flex items-center justify-between gap-2">
                          <Text variant="label">Approval • {entry.title}</Text>
                          <Badge tone={entry.status === "approved" ? "success" : entry.status === "skipped" ? "warning" : "calm"}>
                            {entry.status || "proposed"}
                          </Badge>
                        </div>
                        <Text variant="caption">
                          {entry.summary || "Copilot detected a decision to review."}
                        </Text>
                        <Stack direction="horizontal" gap="sm" wrap>
                          <Button onClick={() => handleApprove(entry)}>Approve</Button>
                          <Button variant="ghost" onClick={() => handleSkip(entry)}>
                            Skip
                          </Button>
                          <Button variant="ghost" onClick={() => handleUndoApproval(entry)}>
                            Undo
                          </Button>
                          <Button variant="ghost" onClick={() => router.push("/review")}>
                            Open in focus view
                          </Button>
                        </Stack>
                      </Stack>
                    </div>
                  );
                }

                return (
                  <div
                    key={entry.id}
                    className="rounded-xl border border-[color:var(--ds-border-subtle)] bg-[color:var(--ds-surface-muted)] p-4"
                  >
                    <Stack gap="sm">
                      <div className="flex items-center justify-between gap-2">
                        <Text variant="label">Draft • {entry.subject}</Text>
                        <Badge tone="info">Draft</Badge>
                      </div>
                      <Text variant="caption">
                        To: {entry.to.length ? entry.to.join(", ") : "Not set"}
                      </Text>
                      <Stack direction="horizontal" gap="sm" wrap>
                        <Button variant="outline" onClick={() => setToast("Draft opened in editor") }>
                          Open draft
                        </Button>
                        <Button variant="ghost" onClick={() => setToast("Undo via drafts history") }>
                          Undo send
                        </Button>
                      </Stack>
                    </Stack>
                  </div>
                );
              })}
            </Stack>
          )}
        </Panel>

        <Panel title="Compose" description="Ask Copilot what you need next.">
          <form className="space-y-3" onSubmit={send}>
            <Textarea
              value={input}
              onChange={(event) => setInput(event.target.value)}
              placeholder="Summarize the last approvals, draft a response, or ask for a sync."
              rows={4}
              disabled={pending}
            />
            <ActionBar
              helperText={pending ? "Working…" : "Copilot is ready"}
              primaryAction={
                <Button type="submit" disabled={pending || !input.trim()}>
                  {pending ? "Sending" : "Send to Copilot"}
                </Button>
              }
              secondaryActions={[
                <span key="ms">Ctrl + Enter to send</span>,
                <Link key="shortcuts" href="/history">
                  View activity
                </Link>,
              ]}
            />
          </form>
        </Panel>
      </Stack>

      {toast ? <Toast message={toast} onClose={() => setToast("")} /> : null}
    </Layout>
  );
}
