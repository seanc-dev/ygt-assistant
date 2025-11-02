import { useEffect, useState } from "react";
import { Heading, Panel, Stack, Text } from "@ygt-assistant/ui";
import { Layout } from "../../components/Layout";
import { api } from "../../lib/api";

export default function SettingsPage() {
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.settings()
      .then(() => setLoading(false))
      .catch(() => setLoading(false));
  }, []);

  return (
    <Layout>
      <Stack gap="lg">
        <div className="flex flex-col gap-2">
          <Heading as="h1" variant="display">
            Settings
          </Heading>
          <Text variant="muted">
            Work hours, translation rules, trust level, and UI preferences.
          </Text>
        </div>

        <Panel>
          {loading ? (
            <Text variant="muted">Loading settings...</Text>
          ) : (
            <Text variant="muted">Settings stub - Phase 0</Text>
          )}
        </Panel>
      </Stack>
    </Layout>
  );
}

