import { ReactNode } from "react";
import { TopNav } from "./TopNav";

interface LayoutProps {
  children: ReactNode;
  variant?: "default" | "tight";
}

export function Layout({ children, variant = "default" }: LayoutProps) {
  const mainClasses =
    variant === "tight"
      ? "mx-auto flex w-full max-w-6xl flex-col gap-0 px-4 py-0 sm:px-8"
      : "mx-auto flex w-full max-w-6xl flex-col gap-6 px-4 py-6 sm:px-8";

  return (
    <div className="min-h-screen flex flex-col bg-[color:var(--ds-surface-muted)] text-[color:var(--ds-text-primary)] transition-colors">
      <TopNav />
      <main className={`${mainClasses} flex-1 min-h-0`}>{children}</main>
    </div>
  );
}
