"use client";
import { ReactNode, useEffect, useRef } from "react";
import { createPortal } from "react-dom";
import clsx from "clsx";
import { radius } from "../tokens/radius";
import { motion } from "../tokens/motion";

/**
 * LucidWork Modal Component
 * 
 * Design: Center-fade, blur background = 6px
 * - Modal appears centered with fade animation
 * - Backdrop has 6px blur effect
 * - Duration: 200ms ease-in-out
 */
export type ModalProps = {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: ReactNode;
  footer?: ReactNode;
  size?: "sm" | "md" | "lg" | "xl";
  closeOnBackdropClick?: boolean;
  closeOnEscape?: boolean;
};

const sizeClasses = {
  sm: "max-w-md",
  md: "max-w-lg",
  lg: "max-w-2xl",
  xl: "max-w-4xl",
};

export function Modal({
  isOpen,
  onClose,
  title,
  children,
  footer,
  size = "md",
  closeOnBackdropClick = true,
  closeOnEscape = true,
}: ModalProps) {
  const modalRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isOpen || !closeOnEscape) return;

    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
    };

    document.addEventListener("keydown", handleEscape);
    return () => document.removeEventListener("keydown", handleEscape);
  }, [isOpen, closeOnEscape, onClose]);

  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [isOpen]);

  if (!isOpen) return null;

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (closeOnBackdropClick && e.target === e.currentTarget) {
      onClose();
    }
  };

  const modalContent = (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      onClick={handleBackdropClick}
      role="dialog"
      aria-modal="true"
      aria-labelledby={title ? "modal-title" : undefined}
    >
      {/* Backdrop */}
      <div
        className="lw-modal-backdrop fixed inset-0 bg-black/20"
        style={{
          transitionDuration: motion.duration.slow,
          transitionTimingFunction: motion.easing.default,
        }}
      />

      {/* Modal */}
      <div
        ref={modalRef}
        className={clsx(
          "relative z-10 w-full rounded-lg bg-[var(--lw-surface)] shadow-lg",
          "transform transition-all",
          sizeClasses[size]
        )}
        style={{
          borderRadius: radius.md, // 6px
          transitionDuration: motion.duration.slow,
          transitionTimingFunction: motion.easing.default,
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        {title && (
          <div className="border-b border-[var(--lw-border)] px-6 py-4">
            <h2
              id="modal-title"
              className="lw-text-heading text-xl font-semibold text-[var(--lw-neutral-text)]"
            >
              {title}
            </h2>
          </div>
        )}

        {/* Content */}
        <div className="px-6 py-4">{children}</div>

        {/* Footer */}
        {footer && (
          <div className="border-t border-[var(--lw-border)] px-6 py-4">
            {footer}
          </div>
        )}

        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute right-4 top-4 rounded p-1 text-[var(--lw-neutral-muted)] hover:bg-[var(--lw-base)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--lw-primary)] focus-visible:ring-opacity-40"
          aria-label="Close modal"
          style={{
            borderRadius: radius.sm,
            transitionDuration: motion.duration.normal,
          }}
        >
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>
      </div>
    </div>
  );

  if (typeof window !== "undefined") {
    return createPortal(modalContent, document.body);
  }

  return null;
}

