import {
  ChevronLeft24Regular,
  ChevronRight24Regular,
} from "@fluentui/react-icons";
import React from "react";

interface EdgeToggleProps {
  side: "left" | "right"; // which edge to render on
  onToggle: () => void; // action to open/close
  label: string; // accessible label
  visible?: boolean; // if false, render nothing
}

export function EdgeToggle({
  side,
  onToggle,
  label,
  visible = true,
}: EdgeToggleProps) {
  if (!visible) return null;
  const isLeft = side === "left";
  return (
    <button
      aria-label={label}
      aria-controls={side === "left" ? "navigator" : "context"}
      onClick={onToggle}
      className={[
        "group absolute top-1/2 -translate-y-1/2 z-20",
        isLeft ? "-right-3" : "-left-3",
        "h-7 w-7 rounded-full bg-white border border-slate-200 shadow-sm",
        "flex items-center justify-center",
        "opacity-60 hover:opacity-100 hover:shadow-md hover:scale-105 transition-all duration-120 ease-in-out",
        "focus:outline-none focus:ring-2 focus:ring-sky-500 focus:ring-offset-1",
      ].join(" ")}
    >
      {isLeft ? (
        <ChevronLeft24Regular className="w-3.5 h-3.5 text-slate-600 group-hover:text-slate-900 transition-colors" />
      ) : (
        <ChevronRight24Regular className="w-3.5 h-3.5 text-slate-600 group-hover:text-slate-900 transition-colors" />
      )}
    </button>
  );
}
