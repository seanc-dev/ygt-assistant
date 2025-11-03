"use client";
import { ReactNode, useState, useRef, useEffect } from "react";
import clsx from "clsx";
import { motion } from "../tokens/motion";

/**
 * LucidWork Tooltip Component
 * 
 * Design: Appear on hover + focus, delay 200ms
 * - Respects prefers-reduced-motion
 * - Accessible with ARIA attributes
 * - Position: top, bottom, left, right
 */
export type TooltipProps = {
  content: ReactNode;
  children: ReactNode;
  position?: "top" | "bottom" | "left" | "right";
  delay?: number;
  disabled?: boolean;
};

const positionClasses = {
  top: "bottom-full left-1/2 -translate-x-1/2 mb-2",
  bottom: "top-full left-1/2 -translate-x-1/2 mt-2",
  left: "right-full top-1/2 -translate-y-1/2 mr-2",
  right: "left-full top-1/2 -translate-y-1/2 ml-2",
};

const arrowClasses = {
  top: "top-full left-1/2 -translate-x-1/2 border-t-[var(--lw-neutral-text)] border-l-transparent border-r-transparent border-b-transparent",
  bottom: "bottom-full left-1/2 -translate-x-1/2 border-b-[var(--lw-neutral-text)] border-l-transparent border-r-transparent border-t-transparent",
  left: "left-full top-1/2 -translate-y-1/2 border-l-[var(--lw-neutral-text)] border-t-transparent border-b-transparent border-r-transparent",
  right: "right-full top-1/2 -translate-y-1/2 border-r-[var(--lw-neutral-text)] border-t-transparent border-b-transparent border-l-transparent",
};

export function Tooltip({
  content,
  children,
  position = "top",
  delay = 200,
  disabled = false,
}: TooltipProps) {
  const [isVisible, setIsVisible] = useState(false);
  const [isHovered, setIsHovered] = useState(false);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (disabled) {
      setIsVisible(false);
      return;
    }

    if (isHovered) {
      timeoutRef.current = setTimeout(() => {
        setIsVisible(true);
      }, delay);
    } else {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
      setIsVisible(false);
    }

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [isHovered, delay, disabled]);

  const handleMouseEnter = () => {
    setIsHovered(true);
  };

  const handleMouseLeave = () => {
    setIsHovered(false);
  };

  const handleFocus = () => {
    setIsHovered(true);
  };

  const handleBlur = () => {
    setIsHovered(false);
  };

  return (
    <div
      className="relative inline-block"
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      onFocus={handleFocus}
      onBlur={handleBlur}
    >
      {children}
      {isVisible && (
        <div
          role="tooltip"
          className={clsx(
            "absolute z-50 whitespace-nowrap rounded px-3 py-1.5",
            "bg-[var(--lw-neutral-text)] text-[var(--lw-surface)] text-sm",
            "shadow-lg",
            positionClasses[position],
            "pointer-events-none"
          )}
          style={{
            transitionDuration: motion.duration.normal,
            transitionTimingFunction: motion.easing.default,
          }}
        >
          {content}
          {/* Arrow */}
          <div
            className={clsx(
              "absolute h-0 w-0 border-4",
              arrowClasses[position]
            )}
          />
        </div>
      )}
    </div>
  );
}

