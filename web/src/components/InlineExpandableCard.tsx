import { ReactNode, useState } from "react";

interface InlineExpandableCardProps {
  children: ReactNode;
  preview: ReactNode;
  expanded?: boolean;
  onToggle?: () => void;
}

export function InlineExpandableCard({
  children,
  preview,
  expanded: controlledExpanded,
  onToggle,
}: InlineExpandableCardProps) {
  const [internalExpanded, setInternalExpanded] = useState(false);
  const expanded = controlledExpanded ?? internalExpanded;
  const handleToggle = onToggle ?? (() => setInternalExpanded(!internalExpanded));

  // Cap height: min(60% column height, 70vh)
  const maxHeight = typeof window !== "undefined" 
    ? Math.min(window.innerHeight * 0.7, window.innerHeight * 0.6)
    : 600;

  return (
    <div
      className={`rounded-lg border transition-all ${
        expanded ? "col-span-full" : ""
      }`}
      style={{
        maxHeight: expanded ? `${maxHeight}px` : "none",
        overflow: expanded ? "auto" : "visible",
      }}
    >
      <div onClick={handleToggle} className="cursor-pointer p-4">
        {preview}
      </div>
      {expanded && (
        <div className="p-4 border-t" style={{ maxHeight: `${maxHeight - 100}px`, overflow: "auto" }}>
          {children}
        </div>
      )}
    </div>
  );
}


