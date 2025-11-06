import { useEffect, useRef, ReactNode, useState } from "react";
import { createPortal } from "react-dom";

interface OverflowMenuProps {
  open: boolean;
  onClose: () => void;
  triggerRef: React.RefObject<HTMLElement>;
  children: ReactNode;
}

export function OverflowMenu({
  open,
  onClose,
  triggerRef,
  children,
}: OverflowMenuProps) {
  const menuRef = useRef<HTMLDivElement>(null);
  const [focusedIndex, setFocusedIndex] = useState(0);

  useEffect(() => {
    if (!open) return;

    const handleClickOutside = (e: MouseEvent) => {
      if (
        menuRef.current &&
        !menuRef.current.contains(e.target as Node) &&
        triggerRef.current &&
        !triggerRef.current.contains(e.target as Node)
      ) {
        onClose();
      }
    };

    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
    };

    const handleArrowKeys = (e: KeyboardEvent) => {
      if (!menuRef.current) return;
      const items = Array.from(menuRef.current.querySelectorAll('[role="menuitem"]')) as HTMLElement[];
      if (items.length === 0) return;

      let newIndex = focusedIndex;

      if (e.key === "ArrowDown") {
        e.preventDefault();
        newIndex = (focusedIndex + 1) % items.length;
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        newIndex = focusedIndex === 0 ? items.length - 1 : focusedIndex - 1;
      } else if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        items[focusedIndex]?.click();
      }

      setFocusedIndex(newIndex);
      items[newIndex]?.focus();
    };

    document.addEventListener("mousedown", handleClickOutside);
    document.addEventListener("keydown", handleEscape);
    document.addEventListener("keydown", handleArrowKeys);

    // Focus first item when menu opens
    if (menuRef.current) {
      const items = Array.from(menuRef.current.querySelectorAll('[role="menuitem"]')) as HTMLElement[];
      if (items.length > 0) {
        setFocusedIndex(0);
        setTimeout(() => items[0]?.focus(), 0);
      }
    }

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("keydown", handleEscape);
      document.removeEventListener("keydown", handleArrowKeys);
    };
  }, [open, onClose, triggerRef, focusedIndex]);

  useEffect(() => {
    if (!open || !triggerRef.current || !menuRef.current) return;

    const rect = triggerRef.current.getBoundingClientRect();
    const menu = menuRef.current;

    // Position menu below trigger, aligned to right
    const top = rect.bottom + 4;
    const left = rect.right;

    menu.style.top = `${top}px`;
    menu.style.left = `${left}px`;
    menu.style.transform = "translateX(-100%)";
  }, [open, triggerRef]);

  if (!open) return null;

  const menuContent = (
    <div
      ref={menuRef}
      className="fixed z-[70] bg-white border border-slate-200 rounded-lg shadow-lg py-1 min-w-[160px]"
      role="menu"
      aria-orientation="vertical"
    >
      {children}
    </div>
  );

  return typeof document !== "undefined"
    ? createPortal(menuContent, document.body)
    : null;
}

interface OverflowMenuItemProps {
  onClick: (e: React.MouseEvent) => void;
  children: ReactNode;
  variant?: "default" | "danger";
}

export function OverflowMenuItem({
  onClick,
  children,
  variant = "default",
}: OverflowMenuItemProps) {
  return (
    <button
      onClick={onClick}
      role="menuitem"
      tabIndex={-1}
      className={`w-full text-left px-3 py-1.5 text-sm transition focus:outline-none focus:bg-slate-100 ${
        variant === "danger"
          ? "text-red-600 hover:bg-red-50 focus:bg-red-50"
          : "text-slate-700 hover:bg-slate-100"
      }`}
    >
      {children}
    </button>
  );
}

