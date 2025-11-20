import type {
  TodayScheduleV1Surface,
  SurfaceNavigateTo,
} from "../../lib/llm/surfaces";

type TodayScheduleSurfaceProps = {
  surface: TodayScheduleV1Surface;
  onInvokeOp?: (opToken: string, options?: { confirm?: boolean }) => void;
  onNavigate?: (nav: SurfaceNavigateTo) => void;
};

const formatRange = (start: string, end: string) => {
  const formatter = new Intl.DateTimeFormat(undefined, {
    hour: "numeric",
    minute: "2-digit",
  });
  const startDate = new Date(start);
  const endDate = new Date(end);
  return `${formatter.format(startDate)} – ${formatter.format(endDate)}`;
};

/**
 * Display today's schedule blocks plus LLM suggestions for adjustments.
 */
export function TodayScheduleSurface({
  surface,
  onInvokeOp,
}: TodayScheduleSurfaceProps) {
  const {
    title,
    payload: { blocks, suggestions, controls },
  } = surface;

  return (
    <div className="rounded-2xl border border-slate-200 bg-gradient-to-b from-white to-slate-50 shadow-sm p-5">
      <div className="text-xs uppercase tracking-wide text-slate-500 mb-3">
        {title}
      </div>
      <div className="space-y-3">
        {blocks.map((block) => (
          <div
            key={block.blockId}
            className="rounded-xl border border-slate-200 bg-white p-3 flex flex-col gap-1"
          >
            <div className="flex items-center justify-between">
              <p className="text-sm font-semibold text-slate-900">
                {block.label}
              </p>
              <span className="text-xs font-medium text-slate-500">
                {block.type === "event" ? "Event" : "Focus"}
              </span>
            </div>
            <p className="text-xs text-slate-500">
              {formatRange(block.start, block.end)}
            </p>
            {block.isLocked && (
              <span className="text-[11px] text-amber-600 font-medium">
                Locked block
              </span>
            )}
          </div>
        ))}
      </div>

      {suggestions?.length ? (
        <div className="mt-4 space-y-2">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">
            Suggestions
          </p>
          {suggestions.map((suggestion) => (
            <div
              key={suggestion.suggestionId ?? suggestion.previewChange}
              className="flex items-center justify-between rounded-xl border border-slate-200 bg-white px-3 py-2"
            >
              <p className="text-sm text-slate-700">{suggestion.previewChange}</p>
              <button
                type="button"
                className="text-sm font-medium text-slate-900 hover:text-slate-700"
                onClick={() =>
                  onInvokeOp?.(suggestion.acceptOp, { confirm: false })
                }
              >
                Accept
              </button>
            </div>
          ))}
        </div>
      ) : null}

      {controls?.suggestAlternativesOp && (
        <button
          type="button"
          className="mt-4 text-sm text-slate-600 underline decoration-dotted decoration-slate-400 hover:text-slate-800"
          onClick={() => {
            const opToken = controls.suggestAlternativesOp;
            if (opToken && onInvokeOp) {
              onInvokeOp(opToken, { confirm: false });
            }
          }}
        >
          Suggest 3 alternatives
        </button>
      )}

      <p className="text-[11px] text-slate-400 mt-4 italic">
        TODO: Drag-and-drop adjustments for blocks (v1 follow-up).
      </p>
    </div>
  );
}

