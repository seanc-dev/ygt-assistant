import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/router";
import { api } from "../lib/api";

const items = [
  { href: "/hub", label: "Hub" },
  { href: "/workroom", label: "Workroom" },
  { href: "/history", label: "History" },
  { href: "/settings", label: "Settings" },
];

export function TopNav() {
  const router = useRouter();
  const { pathname } = router;
  const [connectionStatus, setConnectionStatus] = useState<"connected" | "disconnected" | "unknown">(
    "unknown"
  );
  const [isSeeding, setIsSeeding] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const readStatus = () => {
      const stored = window.localStorage.getItem("ygt-connection-status");
      if (stored === "connected" || stored === "disconnected") {
        setConnectionStatus(stored);
      }
    };
    readStatus();
    const handleStorage = (event: StorageEvent) => {
      if (event.key === "ygt-connection-status") {
        readStatus();
      }
    };
    window.addEventListener("storage", handleStorage);
    return () => window.removeEventListener("storage", handleStorage);
  }, []);

  const handleSeedDevData = async () => {
    if (isSeeding) return;
    setIsSeeding(true);
    try {
      const result = await api.seedDevData();
      console.log("Seeded dev data:", result);
      // SWR will automatically revalidate on focus/interval
      // No need to force reload - just reset loading state
      setIsSeeding(false);
      // Give user feedback that data was seeded
      if (typeof window !== "undefined") {
        // Trigger a custom event that SWR components can listen to
        window.dispatchEvent(new Event("seed-data-complete"));
      }
    } catch (error) {
      console.error("Failed to seed dev data:", error);
      alert("Failed to seed dev data. Check console for details.");
      setIsSeeding(false);
    }
  };

  return (
    <header className="sticky top-0 z-10 border-b border-slate-200/60 bg-white/80 backdrop-blur dark:border-slate-800 dark:bg-slate-900/80">
      <nav
        className="mx-auto flex max-w-5xl items-center gap-2 px-4 py-3 sm:px-6 overflow-x-auto"
        aria-label="Primary"
      >
        {items.map((it) => {
          const active =
            pathname === it.href || pathname.startsWith(it.href + "/");
          const needsAttention =
            it.href === "/connections" && connectionStatus === "disconnected";
          return (
            <Link
              key={it.href}
              href={it.href}
              aria-current={active ? "page" : undefined}
              className={`rounded px-4 py-2 text-sm ${
                active
                  ? "bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900"
                  : "text-slate-700 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
              }`}
            >
              <span className="flex items-center gap-2">
                {it.label}
                {needsAttention ? (
                  <span
                    className="inline-flex h-2 w-2 rounded-full bg-amber-500"
                    aria-hidden="true"
                  />
                ) : null}
              </span>
            </Link>
          );
        })}
        {/* Seed Dev Data Button (dev only) - moved to right side */}
        {process.env.NODE_ENV === "development" && (
          <div className="ml-auto">
            <button
              onClick={handleSeedDevData}
              disabled={isSeeding}
              className="rounded px-3 py-1.5 text-xs font-medium bg-blue-100 text-blue-700 hover:bg-blue-200 dark:bg-blue-900 dark:text-blue-200 dark:hover:bg-blue-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              title="Seed dev data (queue items, schedule blocks)"
            >
              {isSeeding ? "Seeding..." : "🌱 Seed"}
            </button>
          </div>
        )}
      </nav>
    </header>
  );
}
