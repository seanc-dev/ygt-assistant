import { Stack } from "@ygt-assistant/ui";
import { Layout } from "../../components/Layout";
import { HubSummary } from "../../components/hub/HubSummary";
import { TodayOverview } from "../../components/hub/TodayOverview";
import { ActionQueue } from "../../components/hub/ActionQueue";
import { QuickReview } from "../../components/hub/QuickReview";
import { useQueue, useToday, useSettings, useSyncStatus } from "../../hooks/useHubData";

export default function HubPage() {
  const { data: queue } = useQueue({ pollMs: 30000 });
  const { data: schedule } = useToday();
  const { data: settings } = useSettings();
  const { data: syncStatus } = useSyncStatus();

  // Calculate derived stats for HubSummary
  const actionCount = (queue as any)?.total || 0;
  const meetingsToday = schedule?.events?.length || 0;
  const syncState: "synced" | "syncing" | "error" = syncStatus?.state || "synced";
  const trustMode = settings?.trust_level;

  return (
    <Layout>
      <Stack gap="lg">
        <HubSummary
          actionCount={actionCount}
          meetingsToday={meetingsToday}
          syncState={syncState}
          trustMode={trustMode}
        />

        <TodayOverview />

        <ActionQueue />

        <QuickReview />
      </Stack>
    </Layout>
  );
}
