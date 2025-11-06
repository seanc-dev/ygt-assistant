import { ReactNode } from "react";

interface CommandBarProps {
  children: ReactNode;
}

/**
 * Fluent-style command bar wrapper for action buttons.
 * Provides consistent spacing and flex layout.
 */
export default function CommandBar({ children }: CommandBarProps) {
  return <div className="flex flex-wrap items-center gap-1.5">{children}</div>;
}

