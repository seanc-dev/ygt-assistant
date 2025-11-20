import type {
  TriageTableV1Surface,
  SurfaceNavigateTo,
} from "../../lib/llm/surfaces";

type TriageTableSurfaceProps = {
  surface: TriageTableV1Surface;
  onInvokeOp?: (opToken: string, options?: { confirm?: boolean }) => void;
  onNavigate?: (nav: SurfaceNavigateTo) => void;
};

/**
 * Inbox triage surface that groups queue items with approve/decline controls.
 */
export function TriageTableSurface({
  surface,
  onInvokeOp,
  onNavigate,
}: TriageTableSurfaceProps) {
  const { title, payload } = surface;

  return (
    <div className="rounded-2xl border border-slate-200 bg-white shadow-sm p-5">
      <div className="text-xs uppercase tracking-wide text-slate-500 mb-2">
        {title}
      </div>
      <div className="flex flex-col gap-4">
        {payload.groups.map((group) => (
          <section
            key={group.groupId}
            className="rounded-2xl border border-slate-100 bg-slate-50/80 p-4"
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="font-semibold text-sm text-slate-900">
                  {group.label}
                </p>
                {group.summary && (
                  <p className="text-xs text-slate-500">{group.summary}</p>
                )}
              </div>
              <div className="flex gap-2">
                {group.groupActions?.approveAllOp && (
                  <button
                    type="button"
                    className="text-xs font-medium text-slate-700 hover:text-slate-900"
                    onClick={() => {
                      const opToken = group.groupActions?.approveAllOp;
                      if (opToken && onInvokeOp) {
                        onInvokeOp(opToken, { confirm: false });
                      }
                    }}
                  >
                    Approve all
                  </button>
                )}
                {group.groupActions?.declineAllOp && (
                  <button
                    type="button"
                    className="text-xs font-medium text-slate-700 hover:text-slate-900"
                    onClick={() => {
                      const opToken = group.groupActions?.declineAllOp;
                      if (opToken && onInvokeOp) {
                        onInvokeOp(opToken, { confirm: false });
                      }
                    }}
                  >
                    Decline all
                  </button>
                )}
              </div>
            </div>

            <div className="mt-3 space-y-3">
              {group.items.map((item) => (
                <div
                  key={item.queueItemId}
                  className="rounded-xl border border-white bg-white p-3 shadow-sm"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-sm font-semibold text-slate-900">
                        {item.subject}
                      </p>
                      <p className="text-xs text-slate-500">
                        {item.from ? `${item.from} • ` : ""}
                        {item.source}
                      </p>
                      {item.receivedAt && (
                        <p className="text-[11px] text-slate-400">
                          {new Date(item.receivedAt).toLocaleString()}
                        </p>
                      )}
                    </div>
                    {item.suggestedTask && (
                      <button
                        type="button"
                        className="text-xs text-slate-700 underline decoration-dotted"
                        onClick={() =>
                          onNavigate?.({
                            destination: "workroom_task",
                            taskId: item.suggestedTask!.taskId,
                          })
                        }
                      >
                        Open task
                      </button>
                    )}
                  </div>

                  {item.suggestedAction && (
                    <p className="text-xs text-slate-600 mt-2">
                      Suggested: {item.suggestedAction}
                    </p>
                  )}

                  <div className="flex gap-2 mt-3">
                    <button
                      type="button"
                      className="flex-1 rounded-full bg-slate-900 text-white text-sm py-1.5"
                      onClick={() => onInvokeOp?.(item.approveOp, { confirm: false })}
                    >
                      Approve
                    </button>
                    <button
                      type="button"
                      className="flex-1 rounded-full border border-slate-300 text-sm py-1.5 text-slate-700"
                      onClick={() => onInvokeOp?.(item.declineOp, { confirm: false })}
                    >
                      Decline
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}

