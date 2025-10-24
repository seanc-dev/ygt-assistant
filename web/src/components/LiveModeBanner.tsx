import React from "react";
import { Panel, Text } from "@ygt-assistant/ui";

export default function LiveModeBanner() {
  const live =
    (process.env.NEXT_PUBLIC_LIVE_MODE_BANNER || "true").toLowerCase() ===
    "true";
  if (!live) return null;
  return (
    <Panel tone="calm" kicker="Live mode">
      <Text variant="body">
        Live Mode flags are off by default. Enable per-action live gates in
        Connections to test against Microsoft Graph. CI runs in mock mode only.
      </Text>
    </Panel>
  );
}


