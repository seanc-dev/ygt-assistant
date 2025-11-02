import { useEffect, useState } from "react";
import { Heading, Panel, Stack, Text } from "@ygt-assistant/ui";
import { Layout } from "../../components/Layout";
import { api } from "../../lib/api";

export default function WorkroomPage() {
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.workroomTree()
      .then(() => setLoading(false))
      .catch(() => setLoading(false));
  }, []);

  return (
    <Layout>
      <Stack gap="lg">
        <div className="flex flex-col gap-2">
          <Heading as="h1" variant="display">
            Workroom
          </Heading>
          <Text variant="muted">
            Chat-first workspace with Project → Task → Threads hierarchy.
          </Text>
        </div>

        <Panel>
          {loading ? (
            <Text variant="muted">Loading workroom...</Text>
          ) : (
            <Text variant="muted">Workroom stub - Phase 0</Text>
          )}
        </Panel>
      </Stack>
    </Layout>
  );
}

