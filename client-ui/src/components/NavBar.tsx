import Link from "next/link";
import { useRouter } from "next/router";
import { ProfileDropdown } from "./ProfileDropdown";
import clsx from "clsx";
import { ThemeToggle } from "@coachflow/ui";

const links = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/rules", label: "Rules" },
  { href: "/integrations", label: "Integrations" },
];

export function NavBar() {
  const router = useRouter();

  return (
    <header className="border-b border-slate-200 bg-white/90 backdrop-blur dark:border-slate-800 dark:bg-slate-900/75">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3 sm:px-6">
        <nav aria-label="Primary" className="flex items-center gap-4">
          <span className="text-lg font-semibold text-slate-900 dark:text-slate-100">CoachFlow</span>
          <ul className="flex items-center gap-2">
            {links.map((link) => (
              <li key={link.href}>
                <Link
                  href={link.href}
                  className={clsx(
                    "rounded-md px-3 py-2 text-sm font-medium focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2 dark:focus-visible:ring-offset-slate-900",
                    router.pathname === link.href
                      ? "bg-primary-50 text-primary-700 dark:bg-primary-500/20 dark:text-primary-200"
                      : "text-slate-600 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-slate-100"
                  )}
                >
                  {link.label}
                </Link>
              </li>
            ))}
          </ul>
        </nav>
        <div className="flex items-center gap-3">
          <ThemeToggle
            className="focus-outline h-9 w-9 rounded-md border border-slate-200 bg-white text-slate-600 transition hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
            inactiveLabel="Switch to dark theme"
            activeLabel="Switch to light theme"
          />
          <ProfileDropdown />
        </div>
      </div>
    </header>
  );
}
