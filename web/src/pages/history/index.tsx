import { useEffect, useState } from "react";
import { api } from "../../lib/api";
import { Layout } from "../../components/Layout";
import { Card } from "../../components/Card";

type Event = {
  ts: string;
  verb: string;
  object: string;
  id: string;
  [k: string]: any;
};

export default function HistoryPage() {
  const [events, setEvents] = useState<Event[]>([]);

  useEffect(() => {
    api
      .history(100)
      .then(setEvents)
      .catch(() => setEvents([]));
  }, []);

  return (
    <Layout>
      <h1 className="mb-4 text-2xl font-semibold">History</h1>
      <Card>
        <div className="space-y-3">
          {events.length === 0 ? (
            <p className="text-sm text-gray-500">No recent actions.</p>
          ) : (
            events.map((e, idx) => (
              <div
                key={idx}
                className="rounded border border-slate-200 p-3 text-sm dark:border-slate-800"
              >
                <div className="text-slate-500">
                  {new Date(e.ts).toLocaleString()}
                </div>
                <div className="text-slate-900 dark:text-slate-100">
                  {e.verb} {e.object} {e.id}
                </div>
              </div>
            ))
          )}
        </div>
      </Card>
    </Layout>
  );
}
