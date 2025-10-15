import { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { signOut, useSession } from "next-auth/react";
import clsx from "clsx";

export function ProfileDropdown() {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const { data: session } = useSession();

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    }

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  const userDisplayName = session?.user?.name ?? session?.user?.email ?? "User";

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100 hover:text-slate-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2"
        aria-expanded={isOpen}
        aria-haspopup="true"
      >
        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary-100 text-sm font-medium text-primary-700">
          {userDisplayName.charAt(0).toUpperCase()}
        </div>
        <span className="hidden sm:block">{userDisplayName}</span>
        <svg
          className={clsx(
            "h-4 w-4 transition-transform",
            isOpen && "rotate-180"
          )}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </button>

      {isOpen && (
        <div className="absolute right-0 z-10 mt-2 w-56 origin-top-right rounded-md bg-white shadow-lg ring-1 ring-black ring-opacity-5">
          <div className="py-1">
            <div className="px-4 py-2 text-sm text-slate-700 border-b border-slate-100">
              <div className="font-medium">{session?.user?.name}</div>
              <div className="text-slate-500">{session?.user?.email}</div>
            </div>
            <Link
              href="/profile"
              className="block px-4 py-2 text-sm text-slate-700 hover:bg-slate-100"
              onClick={() => setIsOpen(false)}
            >
              Profile Settings
            </Link>
            <button
              type="button"
              onClick={() => {
                setIsOpen(false);
                signOut({ callbackUrl: "/login" });
              }}
              className="block w-full px-4 py-2 text-left text-sm text-slate-700 hover:bg-slate-100"
            >
              Sign out
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
