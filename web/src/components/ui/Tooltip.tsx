import { useState, useRef, useEffect, ReactNode, cloneElement, isValidElement } from "react";
import { createPortal } from "react-dom";

interface TooltipProps {
  label: string;
  children: ReactNode;
  side?: "top" | "bottom" | "left" | "right";
  align?: "start" | "center" | "end";
  delayDuration?: number;
}

export function Tooltip({
  label,
  children,
  side = "top",
  align = "center",
  delayDuration = 150,
}: TooltipProps) {
  const [show, setShow] = useState(false);
  const [position, setPosition] = useState({ top: 0, left: 0 });
  const triggerRef = useRef<HTMLElement>(null);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  const handleMouseEnter = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    timeoutRef.current = setTimeout(() => {
      if (triggerRef.current) {
        const rect = triggerRef.current.getBoundingClientRect();
        let top = 0;
        let left = 0;

        switch (side) {
          case "top":
            top = rect.top - 8;
            left = rect.left + rect.width / 2;
            break;
          case "bottom":
            top = rect.bottom + 8;
            left = rect.left + rect.width / 2;
            break;
          case "left":
            top = rect.top + rect.height / 2;
            left = rect.left - 8;
            break;
          case "right":
            top = rect.top + rect.height / 2;
            left = rect.right + 8;
            break;
        }

        // Adjust for alignment
        if (side === "top" || side === "bottom") {
          if (align === "start") left = rect.left;
          else if (align === "end") left = rect.right;
        } else {
          if (align === "start") top = rect.top;
          else if (align === "end") top = rect.bottom;
        }

        setPosition({ top, left });
        setShow(true);
      }
    }, delayDuration);
  };

  const handleMouseLeave = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    setShow(false);
  };

  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  const tooltipContent = show && (
    <div
      className="fixed z-[60] pointer-events-none"
      style={{
        top: `${position.top}px`,
        left: `${position.left}px`,
        transform:
          side === "top" || side === "bottom"
            ? `translateX(${align === "start" ? "0" : align === "end" ? "-100%" : "-50%"}) translateY(${side === "top" ? "-100%" : "0"})`
            : `translateY(${align === "start" ? "0" : align === "end" ? "-100%" : "-50%"}) translateX(${side === "left" ? "-100%" : "0"})`,
      }}
    >
      <div className="px-2 py-1 text-xs font-medium text-white bg-slate-900 rounded-md shadow-lg whitespace-nowrap">
        {label}
      </div>
    </div>
  );

  // Clone child element and add ref and event handlers
  if (isValidElement(children)) {
    return (
      <>
        {cloneElement(children as any, {
          ref: triggerRef,
          onMouseEnter: handleMouseEnter,
          onMouseLeave: handleMouseLeave,
          onFocus: handleMouseEnter,
          onBlur: handleMouseLeave,
        })}
        {typeof document !== "undefined" &&
          createPortal(tooltipContent, document.body)}
      </>
    );
  }

  return (
    <>
      <span
        ref={triggerRef as any}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        onFocus={handleMouseEnter}
        onBlur={handleMouseLeave}
      >
        {children}
      </span>
      {typeof document !== "undefined" &&
        createPortal(tooltipContent, document.body)}
    </>
  );
}

