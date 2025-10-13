import { Layout } from "../../components/Layout";
import { Card } from "../../components/Card";
import { useState } from "react";

export default function AutomationsPage() {
  const [enabled, setEnabled] = useState<Record<string, boolean>>({
    holdInvoices: true,
    scheduleMeetings: true,
  });
  const items = [
    {
      key: "holdInvoices",
      title: "Hold invoice emails for review",
      desc: "Pause invoice-related emails so you can double-check before sending.",
    },
    {
      key: "scheduleMeetings",
      title: "Suggest meeting slots",
      desc: "Flag emails asking to schedule time and queue them for quick suggestions.",
    },
  ];
  return (
    <Layout>
      <h1 className="mb-4 text-2xl font-semibold">Automations</h1>
      <div className="space-y-3">
        {items.map((it) => (
          <Card
            key={it.key}
            title={it.title}
            subtitle={it.desc}
            actions={
              <label className="inline-flex cursor-pointer items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={!!enabled[it.key]}
                  onChange={(e) => setEnabled((s) => ({ ...s, [it.key]: e.target.checked }))}
                />
                <span>{enabled[it.key] ? "On" : "Off"}</span>
              </label>
            }
          />
        ))}
      </div>
    </Layout>
  );
}
