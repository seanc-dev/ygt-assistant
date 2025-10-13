import Link from "next/link";
import { useRouter } from "next/router";

const items = [
  { href: "/", label: "Home" },
  { href: "/review", label: "To review" },
  { href: "/drafts", label: "Drafts" },
  { href: "/automations", label: "Automations" },
  { href: "/connections", label: "Connections" },
  { href: "/history", label: "History" },
];

export function TopNav() {
  const { pathname } = useRouter();
  return (
    <header className="sticky top-0 z-10 border-b border-slate-200/60 bg-white/80 backdrop-blur dark:border-slate-800 dark:bg-slate-900/80">
      <nav className="mx-auto flex max-w-5xl items-center gap-2 px-4 py-3 sm:px-6 overflow-x-auto" aria-label="Primary">
        {items.map((it) => {
          const active = pathname === it.href || pathname.startsWith(it.href + "/");
          return (
            <Link
              key={it.href}
              href={it.href}
              aria-current={active ? "page" : undefined}
              className={`rounded px-4 py-2 text-sm ${active ? "bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900" : "text-slate-700 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"}`}
            >
              {it.label}
            </Link>
          );
        })}
      </nav>
    </header>
  );
}
