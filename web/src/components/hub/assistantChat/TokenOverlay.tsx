import type { MutableRefObject, RefObject } from "react";
import type { TokenSegment } from "./types";

type TokenOverlayProps = {
  message: string;
  tokenSegments: TokenSegment[];
  activeTokenDetailId: string | null;
  tokenOverlayRef:
    | RefObject<HTMLDivElement>
    | MutableRefObject<HTMLDivElement | null>;
  onToggleDetail: (tokenId: string) => void;
  onRemoveToken: (tokenId: string, rawToken: string) => void;
};

export function TokenOverlay({
  message,
  tokenSegments,
  activeTokenDetailId,
  tokenOverlayRef,
  onToggleDetail,
  onRemoveToken,
}: TokenOverlayProps) {
  return (
    <div
      ref={tokenOverlayRef}
      className="pointer-events-none absolute inset-0 overflow-y-auto max-h-24 px-3 py-2 text-sm leading-relaxed text-slate-900 whitespace-pre-wrap break-words rounded-md"
      aria-hidden="true"
    >
      {message.length === 0 ? (
        <span className="text-slate-400">Message Assistant</span>
      ) : (
        tokenSegments.map((segment, idx) => {
          if (segment.type === "text") {
            return (
              <span key={`text-${idx}`} className="whitespace-pre-wrap">
                {segment.text}
              </span>
            );
          }

          const token = segment.token;
          const tokenId = `${token.kind}-${token.start}-${token.end}-${idx}`;
          const isActive = activeTokenDetailId === tokenId;
          const detailLines: string[] = [];

          if (token.data) {
            if (token.kind === "ref") {
              if (token.data.name) {
                detailLines.push(`Name: ${token.data.name}`);
              }
              if (token.data.project) {
                detailLines.push(`Project: ${token.data.project}`);
              }
              if (token.data.id) {
                detailLines.push(`ID: ${token.data.id}`);
              }
            } else {
              detailLines.push(`Op: ${token.data.type || "op"}`);
              Object.entries(token.data)
                .filter(([key]) => key !== "type" && key !== "v")
                .slice(0, 3)
                .forEach(([key, value]) => {
                  detailLines.push(`${key}: ${value}`);
                });
            }
          }

          return (
            <span
              key={tokenId}
              className="relative inline-flex items-center gap-1 mr-1 mb-1 pointer-events-auto"
            >
              <button
                type="button"
                onMouseDown={(event) => event.preventDefault()}
                onClick={(event) => {
                  event.preventDefault();
                  onToggleDetail(tokenId);
                }}
                className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-slate-300 ${
                  token.kind === "ref"
                    ? "bg-sky-50 border-sky-200 text-sky-800 hover:bg-sky-100"
                    : "bg-amber-50 border-amber-200 text-amber-800 hover:bg-amber-100"
                }`}
              >
                <span>{token.label}</span>
              </button>
              <button
                type="button"
                onMouseDown={(event) => event.preventDefault()}
                onClick={(event) => {
                  event.preventDefault();
                  onRemoveToken(tokenId, token.raw);
                }}
                aria-label="Remove token"
                className="text-xs text-slate-500 hover:text-slate-900 focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-slate-300 rounded-full px-1"
              >
                ×
              </button>
              {isActive && detailLines.length > 0 && (
                <div className="absolute left-0 top-full mt-1 min-w-[200px] rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs text-slate-700 shadow-xl ring-1 ring-slate-100 pointer-events-auto z-10">
                  <div className="font-semibold mb-1">{token.label}</div>
                  <ul className="space-y-0.5">
                    {detailLines.map((line, lineIdx) => (
                      <li key={`${tokenId}-detail-${lineIdx}`}>{line}</li>
                    ))}
                  </ul>
                </div>
              )}
            </span>
          );
        })
      )}
    </div>
  );
}

