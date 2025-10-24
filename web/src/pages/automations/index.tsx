import { useState } from "react";
import {
  ActionBar,
  Badge,
  Button,
  Heading,
  Panel,
  Stack,
  Text,
} from "@ygt-assistant/ui";
import { Layout } from "../../components/Layout";
import { Toast } from "../../components/Toast";

type Automation = {
  key: string;
  title: string;
  description: string;
  status: "running" | "paused" | "draft";
  metric?: string;
  lastRun?: string;
};

const AUTOMATIONS: Automation[] = [
  {
    key: "holdInvoices",
    title: "Hold invoice emails for review",
    description: "Pause invoice-related emails so you can double-check before sending.",
    status: "running",
    metric: "7 held this week",
    lastRun: "7m ago",
  },
  {
    key: "scheduleMeetings",
    title: "Suggest meeting slots",
    description: "Flag emails asking to schedule time and queue them for quick suggestions.",
    status: "running",
    metric: "4 suggestions delivered",
    lastRun: "18m ago",
  },
  {
    key: "handoffTeams",
    title: "Draft Teams updates",
    description: "Send digest-ready updates to Teams channels when key projects move.",
    status: "paused",
    metric: "Awaiting setup",
    lastRun: "Not run",
  },
];

export default function AutomationsPage() {
  const [state, setState] = useState<Record<string, boolean>>({
    holdInvoices: true,
    scheduleMeetings: true,
    handoffTeams: false,
  });
  const [toast, setToast] = useState("");

  return (
    <Layout>
      <Stack gap="lg">
        <div className="flex flex-col gap-2">
          <Heading as="h1" variant="display">
            Automations
          </Heading>
          <Text variant="muted">
            Keep high-signal flows running while demoting busywork. Toggle automations on or off and inspect their recent wins.
          </Text>
        </div>

        <Panel
          kicker="Overview"
          title="Guided actions"
          description="Enable the automations that match your current workflow."
        >
          <ActionBar
            helperText="Automations run after every Graph sync"
            primaryAction={<Button onClick={() => setToast("New automation wizard coming soon")}>Create automation</Button>}
            secondaryActions={[<span key="docs">Review run logs in History</span>]}
          />
        </Panel>

        <Stack gap="md">
          {AUTOMATIONS.map((automation) => {
            const enabled = state[automation.key];
            return (
              <Panel
                key={automation.key}
                kicker={enabled ? "Active" : "Dormant"}
                title={automation.title}
                description={automation.description}
                tone={enabled ? "default" : "soft"}
                actions={
                  <Badge tone={enabled ? "success" : "warning"}>
                    {enabled ? automation.status : "Paused"}
                  </Badge>
                }
                footer={
                  <Stack direction="horizontal" justify="between" align="center">
                    <Text variant="caption">
                      {automation.metric} • Last run {automation.lastRun}
                    </Text>
                    <Button
                      variant="ghost"
                      onClick={() => {
                        setState((prev) => ({ ...prev, [automation.key]: !enabled }));
                        setToast(`${enabled ? "Paused" : "Enabled"} ${automation.title}`);
                      }}
                    >
                      {enabled ? "Pause" : "Enable"}
                    </Button>
                  </Stack>
                }
              >
                <Stack direction="horizontal" gap="sm" wrap>
                  <Button variant="secondary" onClick={() => setToast("Syncing automation now")}>Run now</Button>
                  <Button variant="ghost" onClick={() => setToast("Opening metrics")}>View metrics</Button>
                  <Button variant="ghost" onClick={() => setToast("Undo via history")}>Undo</Button>
                </Stack>
              </Panel>
            );
          })}
        </Stack>
      </Stack>

      {toast ? <Toast message={toast} onClose={() => setToast("")} /> : null}
    </Layout>
  );
}
