import { useEffect, useState, useMemo } from "react";
import { Heading, Panel, Stack, Text, Button } from "@ygt-assistant/ui";
import { Layout } from "../../components/Layout";
import { api } from "../../lib/api";

interface AuditEntry {
  id: string;
  timestamp: string;
  request_id: string;
  action: string;
  details: {
    user_id?: string;
    action_id?: string;
    [key: string]: any;
  };
}

interface AuditLogResponse {
  ok: boolean;
  entries: AuditEntry[];
  total: number;
  limit: number;
}

const ACTION_TYPES = [
  "all",
  "defer",
  "add_to_today",
  "schedule_alternatives_generated",
  "create_thread",
  "update_task_status",
  "update_settings",
  "reply_action",
] as const;

type ActionFilter = typeof ACTION_TYPES[number];

export default function HistoryPage() {
  const [loading, setLoading] = useState(true);
  const [auditLog, setAuditLog] = useState<AuditLogResponse | null>(null);
  const [filter, setFilter] = useState<ActionFilter>("all");
  const [limit, setLimit] = useState(100);

  const loadAuditLog = async () => {
    try {
      const actionType = filter === "all" ? undefined : filter;
      const data = await api.auditLog(limit, actionType);
      setAuditLog(data as AuditLogResponse);
      setLoading(false);
    } catch (err) {
      console.error("Failed to load audit log:", err);
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAuditLog();
  }, [filter, limit]);

  const filteredEntries = useMemo(() => {
    if (!auditLog) return [];
    if (filter === "all") return auditLog.entries;
    return auditLog.entries.filter((e) => e.action === filter);
  }, [auditLog, filter]);

  const formatTimestamp = (iso: string) => {
    const date = new Date(iso);
    return date.toLocaleString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  };

  const formatAction = (action: string) => {
    return action
      .split("_")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ");
  };

  return (
    <Layout>
      <Stack gap="lg">
        <div className="flex flex-col gap-2">
          <Heading as="h1" variant="display">
            History
          </Heading>
          <Text variant="muted">
            Audit log of all actions taken in the system.
          </Text>
        </div>

        {/* Filters */}
        <Panel>
          <div className="flex flex-wrap gap-2 items-center">
            <Text variant="label" className="text-sm">
              Filter:
            </Text>
            {ACTION_TYPES.map((actionType) => (
              <Button
                key={actionType}
                variant={filter === actionType ? "primary" : "outline"}
                onClick={() => setFilter(actionType)}
                className="text-xs"
              >
                {actionType === "all" ? "All" : formatAction(actionType)}
              </Button>
            ))}
          </div>
          <div className="mt-2 flex items-center gap-2">
            <Text variant="label" className="text-sm">
              Limit:
            </Text>
            <select
              value={limit}
              onChange={(e) => setLimit(parseInt(e.target.value))}
              className="border rounded px-2 py-1 text-sm"
            >
              <option value={50}>50</option>
              <option value={100}>100</option>
              <option value={200}>200</option>
              <option value={500}>500</option>
            </select>
          </div>
        </Panel>

        {/* Audit Log Entries */}
        {loading && !auditLog ? (
          <Panel>
            <Text variant="muted">Loading audit log...</Text>
          </Panel>
        ) : filteredEntries.length === 0 ? (
          <Panel>
            <Text variant="muted">No audit log entries found.</Text>
          </Panel>
        ) : (
          <Stack gap="md">
            <div className="text-sm text-gray-600">
              Showing {filteredEntries.length} of {auditLog?.total || 0} entries
            </div>
            {filteredEntries.map((entry) => (
              <Panel key={entry.id}>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <div>
                      <Text variant="label" className="text-sm font-medium">
                        {formatAction(entry.action)}
                      </Text>
                      <Text variant="caption" className="text-xs text-gray-500 ml-2">
                        {formatTimestamp(entry.timestamp)}
                      </Text>
                    </div>
                    <Text variant="caption" className="text-xs text-gray-400">
                      {entry.request_id.slice(0, 8)}
                    </Text>
                  </div>
                  
                  <div className="text-xs text-gray-600">
                    {Object.entries(entry.details).map(([key, value]) => {
                      if (key === "user_id") return null; // Skip user_id
                      return (
                        <div key={key} className="mt-1">
                          <span className="font-medium capitalize">{key.replace("_", " ")}:</span>{" "}
                          {typeof value === "object" ? JSON.stringify(value) : String(value)}
                        </div>
                      );
                    })}
                  </div>
                </div>
              </Panel>
            ))}
          </Stack>
        )}
      </Stack>
    </Layout>
  );
}
