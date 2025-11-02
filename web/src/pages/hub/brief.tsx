import { useEffect, useState } from "react";
import { Heading, Panel, Stack, Text } from "@ygt-assistant/ui";
import { Layout } from "../../components/Layout";
import { api } from "../../lib/api";

export default function BriefPage() {
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.briefToday()
      .then(() => setLoading(false))
      .catch(() => setLoading(false));
  }, []);

  return (
    <Layout>
      <Stack gap="lg">
        <div className="flex flex-col gap-2">
          <Heading as="h1" variant="display">
            Brief
          </Heading>
          <Text variant="muted">
            Daily orientation with optional weather and news.
          </Text>
        </div>

        <Panel>
          {loading ? (
            <Text variant="muted">Loading brief...</Text>
          ) : (
            <Text variant="muted">Brief stub - Phase 0</Text>
          )}
        </Panel>
      </Stack>
    </Layout>
  );
}

