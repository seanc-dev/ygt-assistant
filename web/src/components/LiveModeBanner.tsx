import React from "react";

export default function LiveModeBanner() {
  const live =
    (process.env.NEXT_PUBLIC_LIVE_MODE_BANNER || "true").toLowerCase() ===
    "true";
  if (!live) return null;
  return (
    <div className="mb-3 rounded bg-yellow-50 p-2 text-xs text-yellow-900">
      Live Mode flags are off by default. Enable per-action live gates in
      Connections to test against Microsoft Graph. CI runs in mock mode only.
    </div>
  );
}


