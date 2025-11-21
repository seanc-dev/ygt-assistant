import type {
  ContextAddV1Surface,
  SurfaceNavigateTo,
} from "../../lib/llm/surfaces";
import { ArrowRight12Regular, Add16Regular } from "@fluentui/react-icons";

type ContextAddSurfaceProps = {
  surface: ContextAddV1Surface;
  onInvokeOp?: (opToken: string) => void;
  onNavigate?: (nav: SurfaceNavigateTo) => void;
};

export function ContextAddSurface({ surface, onInvokeOp, onNavigate }: ContextAddSurfaceProps) {
  return (
    <div className="w-full rounded-lg border border-slate-200 bg-white shadow-sm" data-testid="context-add-surface">
      <div className="flex items-center justify-between border-b border-slate-100 px-4 py-2">
        <div className="text-sm font-semibold text-slate-800">{surface.title}</div>
        {surface.payload.headline && (
          <div className="text-xs text-slate-500">{surface.payload.headline}</div>
        )}
      </div>

      <div className="divide-y divide-slate-100">
        {surface.payload.items.map((item) => (
          <div key={item.contextId} className="flex flex-col gap-2 px-4 py-3">
            <div className="flex items-center justify-between gap-3">
              <div className="flex flex-col">
                <div className="text-sm font-medium text-slate-800">{item.label}</div>
                <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500">
                  {item.sourceType && (
                    <span className="rounded-full bg-slate-100 px-2 py-1 text-slate-700">
                      {item.sourceType}
                    </span>
                  )}
                  <span className="rounded-full bg-slate-50 px-2 py-1 text-slate-700">
                    {item.contextId}
                  </span>
                </div>
              </div>
              <div className="flex items-center gap-2">
                {item.navigateTo && (
                  <button
                    type="button"
                    onClick={() => onNavigate?.(item.navigateTo)}
                    className="inline-flex items-center gap-1 rounded-md border border-slate-200 px-2 py-1 text-xs text-slate-700 hover:bg-slate-50"
                  >
                    <ArrowRight12Regular className="h-4 w-4" />
                    View
                  </button>
                )}
                {item.addOp && (
                  <button
                    type="button"
                    onClick={() => onInvokeOp?.(item.addOp!, undefined)}
                    className="inline-flex items-center gap-1 rounded-md bg-blue-600 px-3 py-1 text-xs font-medium text-white shadow-sm hover:bg-blue-700"
                  >
                    <Add16Regular className="h-4 w-4" />
                    Add context
                  </button>
                )}
              </div>
            </div>
            {item.summary && <div className="text-xs text-slate-600">{item.summary}</div>}
          </div>
        ))}
      </div>
    </div>
  );
}

