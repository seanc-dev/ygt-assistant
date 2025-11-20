import type {
  WhatNextV1Surface,
  SurfaceNavigateTo,
  SurfaceAction,
  SurfaceOpTrigger,
} from "../../lib/llm/surfaces";

type WhatNextSurfaceProps = {
  surface: WhatNextV1Surface;
  onInvokeOp?: (opToken: string, options?: { confirm?: boolean }) => void;
  onNavigate?: (nav: SurfaceNavigateTo) => void;
};

const isOpAction = (action?: SurfaceAction): action is SurfaceOpTrigger =>
  Boolean(action && "opToken" in action);

/**
 * Compact card summarizing the assistant's recommended next action.
 */
export function WhatNextSurface({
  surface,
  onInvokeOp,
  onNavigate,
}: WhatNextSurfaceProps) {
  const {
    title,
    payload: { primary, secondaryNotes },
  } = surface;

  const handleAction = (action?: SurfaceAction) => {
    if (!action) return;
    if (isOpAction(action)) {
      onInvokeOp?.(action.opToken, { confirm: action.confirm });
    } else if (action.navigateTo) {
      onNavigate?.(action.navigateTo);
    }
  };

  return (
    <div className="rounded-2xl border border-slate-200 bg-white shadow-sm p-5 text-slate-900">
      <div className="text-xs uppercase tracking-wide text-slate-500 mb-1">
        {title}
      </div>
      <h3 className="font-semibold text-lg leading-tight">
        {primary.headline}
      </h3>
      {primary.body && (
        <p className="text-sm text-slate-600 mt-1">{primary.body}</p>
      )}

      {(primary.primaryAction || primary.secondaryActions?.length) && (
        <div className="flex flex-wrap gap-2 mt-4">
          {primary.primaryAction && (
            <button
              type="button"
              onClick={() => handleAction(primary.primaryAction)}
              className="px-3 py-1.5 rounded-full bg-slate-900 text-white text-sm font-medium hover:bg-slate-800 transition"
            >
              {primary.primaryAction.label}
            </button>
          )}
          {primary.secondaryActions?.map((action) => (
            <button
              type="button"
              key={action.label}
              onClick={() => handleAction(action)}
              className="px-3 py-1.5 rounded-full border border-slate-300 text-sm text-slate-700 hover:bg-slate-50 transition"
            >
              {action.label}
            </button>
          ))}
        </div>
      )}

      {secondaryNotes?.length ? (
        <ul className="mt-4 space-y-1 text-sm text-slate-500">
          {secondaryNotes.map((note, idx) => (
            <li key={`${note.text}-${idx}`} className="flex gap-2 items-start">
              {note.icon && (
                <span className="text-slate-400" aria-hidden="true">
                  {note.icon}
                </span>
              )}
              <span>{note.text}</span>
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}

