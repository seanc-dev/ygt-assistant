import { ReactNode } from "react";
import { TopNav } from "./TopNav";

export function Layout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-[color:var(--ds-surface-muted)] text-[color:var(--ds-text-primary)] transition-colors">
      <TopNav />
      <main className="mx-auto flex w-full max-w-6xl flex-col gap-6 px-4 py-6 sm:px-8">
        {children}
      </main>
    </div>
  );
}
