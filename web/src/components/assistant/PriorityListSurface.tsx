import type {
  PriorityListV1Surface,
  SurfaceNavigateTo,
  SurfaceOpTrigger,
} from "../../lib/llm/surfaces";

type PriorityListSurfaceProps = {
  surface: PriorityListV1Surface;
  onInvokeOp?: (opToken: string, options?: { confirm?: boolean }) => void;
  onNavigate?: (nav: SurfaceNavigateTo) => void;
};

const isOpTrigger = (
  action: SurfaceOpTrigger | undefined
): action is SurfaceOpTrigger => Boolean(action && action.opToken);

/**
 * Ordered list of the assistant's prioritized tasks with quick actions.
 */
export function PriorityListSurface({
  surface,
  onInvokeOp,
  onNavigate,
}: PriorityListSurfaceProps) {
  const { title, payload } = surface;
  return (
    <div className="rounded-2xl border border-slate-200 bg-white shadow-sm p-5">
      <div className="text-xs uppercase tracking-wide text-slate-500 mb-2">
        {title}
      </div>
      <ol className="space-y-3 list-none">
        {payload.items.map((item) => {
          const handleNavigate = () =>
            item.navigateTo && onNavigate?.(item.navigateTo);

          return (
            <li
              key={`${item.rank}-${item.taskId}`}
              className="rounded-xl border border-slate-100 bg-slate-50/80 p-3"
            >
              <div className="flex items-start gap-3">
                <div className="text-2xl font-semibold text-slate-300 leading-none">
                  {item.rank}
                </div>
                <div className="flex-1">
                  <button
                    type="button"
                    onClick={handleNavigate}
                    disabled={!item.navigateTo}
                    className="text-left w-full disabled:cursor-default"
                  >
                    <p className="font-semibold text-sm text-slate-900">
                      {item.label}
                    </p>
                    {item.reason && (
                      <p className="text-xs text-slate-500">{item.reason}</p>
                    )}
                    {item.timeEstimateMinutes !== undefined && (
                      <p className="text-[11px] text-slate-400 mt-1">
                        ~{item.timeEstimateMinutes} min
                      </p>
                    )}
                  </button>
                </div>
                {item.quickActions?.length ? (
                  <div className="flex flex-col gap-1">
                    {item.quickActions.map((action) => (
                      <button
                        type="button"
                        key={action.label}
                        className="text-xs font-medium text-slate-700 hover:text-slate-900"
                        onClick={() =>
                          isOpTrigger(action) &&
                          onInvokeOp?.(action.opToken, { confirm: action.confirm })
                        }
                      >
                        {action.label}
                      </button>
                    ))}
                  </div>
                ) : null}
              </div>
            </li>
          );
        })}
      </ol>
    </div>
  );
}

