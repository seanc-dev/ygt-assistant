import { Integration } from "../lib/types";
import { Button } from "./Button";

interface IntegrationCardProps {
  integration: Integration;
  onConnect: (provider: string) => void;
}

export function IntegrationCard({ integration, onConnect }: IntegrationCardProps) {
  const { provider, status } = integration;
  const providerName = provider.charAt(0).toUpperCase() + provider.slice(1);
  const statusLabel = status === "connected" ? "Connected" : "Not connected";
  const statusIndicatorClass =
    status === "connected"
      ? "bg-emerald-500 dark:bg-emerald-400"
      : "bg-slate-300 dark:bg-slate-600";
  return (
    <div className="flex flex-col justify-between rounded-lg border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-700 dark:bg-slate-900">
      <div>
        <h3 className="text-base font-semibold text-slate-900 dark:text-slate-100">{providerName}</h3>
        <p className="mt-2 flex items-center gap-2 text-sm text-slate-600 dark:text-slate-400">
          <span className={`inline-flex h-2.5 w-2.5 rounded-full ${statusIndicatorClass}`} aria-hidden="true" />
          <span className="font-medium">{statusLabel}</span>
        </p>
      </div>
      <Button
        type="button"
        variant={status === "connected" ? "secondary" : "primary"}
        className="mt-4"
        onClick={() => onConnect(provider)}
      >
        {status === "connected" ? "Reconnect" : "Connect"}
      </Button>
    </div>
  );
}
