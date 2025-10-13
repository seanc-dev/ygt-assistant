import { useEffect, useState } from "react";
import { api } from "../../lib/api";

type Event = { ts: string; verb: string; object: string; id: string; [k: string]: any };

export default function HistoryPage() {
  const [events, setEvents] = useState<Event[]>([]);

  useEffect(() => {
    api.history(100).then(setEvents).catch(() => setEvents([]));
  }, []);

  return (
    <div className="p-6">
      <h1 className="text-2xl font-semibold">History</h1>
      <div className="mt-4 space-y-3">
        {events.length === 0 ? (
          <p className="text-sm text-gray-500">No recent actions.</p>
        ) : (
          events.map((e, idx) => (
            <div key={idx} className="rounded border p-3">
              <div className="text-sm text-gray-500">{new Date(e.ts).toLocaleString()}</div>
              <div className="text-slate-900">
                {e.verb} {e.object} {e.id}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
