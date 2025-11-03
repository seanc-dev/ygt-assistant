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
      className={`rounded-lg border transition-all duration-200 ease-in-out ${
        expanded ? "col-span-full" : ""
      }`}
      style={{
        maxHeight: expanded ? `${maxHeight}px` : "none",
        overflow: expanded ? "auto" : "visible",
        transition: "max-height 0.2s ease-in-out, transform 0.2s ease-in-out",
      }}
    >
      <div onClick={handleToggle} className="cursor-pointer p-4 hover:bg-gray-50 transition-colors duration-150">
        {preview}
      </div>
      {expanded && (
        <div 
          className="p-4 border-t animate-in fade-in duration-200" 
          style={{ maxHeight: `${maxHeight - 100}px`, overflow: "auto" }}
        >
          {children}
        </div>
      )}
    </div>
  );
}


