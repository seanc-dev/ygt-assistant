import { useEffect, useState } from "react";
import { Heading, Panel, Stack, Text } from "@ygt-assistant/ui";
import { Layout } from "../../components/Layout";
import { api } from "../../lib/api";

export default function SchedulePage() {
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.scheduleToday()
      .then(() => setLoading(false))
      .catch(() => setLoading(false));
  }, []);

  return (
    <Layout>
      <Stack gap="lg">
        <div className="flex flex-col gap-2">
          <Heading as="h1" variant="display">
            Schedule
          </Heading>
          <Text variant="muted">
            Today-first schedule merged with existing calendar events.
          </Text>
        </div>

        <Panel>
          {loading ? (
            <Text variant="muted">Loading schedule...</Text>
          ) : (
            <Text variant="muted">Schedule stub - Phase 0</Text>
          )}
        </Panel>
      </Stack>
    </Layout>
  );
}

