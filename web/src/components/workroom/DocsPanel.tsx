import { Text } from "@lucid-work/ui";
import { useWorkroomContext } from "../../hooks/useWorkroomContext";

export function DocsPanel() {
  const { workroomContext, loading, error } = useWorkroomContext();
  const docs = workroomContext?.neighborhood?.docs || [];

  if (loading) {
    return (
      <Text variant="caption" className="text-xs text-slate-500">
        Loading docs...
      </Text>
    );
  }

  if (error) {
    return (
      <Text variant="caption" className="text-xs text-red-600">
        Docs unavailable.
      </Text>
    );
  }

  if (docs.length === 0) {
    return (
      <Text variant="caption" className="text-xs text-slate-500">
        No docs linked yet.
      </Text>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      <Text variant="body" className="text-sm font-semibold text-slate-800">
        Docs
      </Text>
      <div className="flex flex-col gap-2">
        {docs.map((doc) => (
          <div
            key={doc.id}
            className="flex items-center justify-between rounded-lg border border-slate-200 bg-slate-50 px-3 py-2"
          >
            <div className="text-sm font-medium text-slate-800">{doc.title}</div>
            <button
              type="button"
              className="rounded-md border border-slate-300 px-3 py-1 text-xs font-medium text-slate-700 transition hover:bg-slate-100"
              onClick={() => console.debug("Open doc", doc.id)}
            >
              Open
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
