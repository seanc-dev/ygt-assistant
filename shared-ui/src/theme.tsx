"use client";
import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useLayoutEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { cx } from "./cx";

const STORAGE_KEY = "coachflow-theme";

export type ThemePreference = "light" | "dark" | "system";
export type Theme = "light" | "dark";

type ThemeContextValue = {
  theme: ThemePreference;
  resolvedTheme: Theme;
  setTheme: (value: ThemePreference) => void;
  toggleTheme: () => void;
};

const ThemeContext = createContext<ThemeContextValue>({
  theme: "system",
  resolvedTheme: "light",
  setTheme: () => {},
  toggleTheme: () => {},
});

const isBrowser = () => typeof window !== "undefined";

const useIsomorphicLayoutEffect = isBrowser() ? useLayoutEffect : useEffect;

function applyTheme(theme: Theme) {
  if (!isBrowser()) return;
  const root = window.document.documentElement;
  root.classList.toggle("dark", theme === "dark");
  root.dataset.theme = theme;
  root.style.colorScheme = theme;
}

type ThemeProviderProps = {
  children: ReactNode;
  defaultTheme?: ThemePreference;
};

export const ThemeProvider: React.FC<ThemeProviderProps> = ({
  children,
  defaultTheme = "system",
}) => {
  const [theme, setThemeState] = useState<ThemePreference>(defaultTheme);
  const [resolvedTheme, setResolvedTheme] = useState<Theme>(() =>
    defaultTheme === "dark" ? "dark" : "light"
  );

  useEffect(() => {
    if (!isBrowser()) return;
    const stored = window.localStorage.getItem(STORAGE_KEY);
    if (stored === "light" || stored === "dark") {
      setThemeState(stored);
    } else if (stored === "system") {
      setThemeState("system");
    }
  }, []);

  useIsomorphicLayoutEffect(() => {
    const mediaQuery = isBrowser()
      ? window.matchMedia("(prefers-color-scheme: dark)")
      : null;

    const resolve = (value: ThemePreference): Theme =>
      value === "system" ? (mediaQuery?.matches ? "dark" : "light") : value;

    const nextTheme = resolve(theme);
    setResolvedTheme(nextTheme);
    applyTheme(nextTheme);

    if (!mediaQuery) return;
    if (theme !== "system") return;

    const listener = (event: MediaQueryListEvent) => {
      const updated = event.matches ? "dark" : "light";
      setResolvedTheme(updated);
      applyTheme(updated);
    };

    mediaQuery.addEventListener("change", listener);
    return () => mediaQuery.removeEventListener("change", listener);
  }, [theme]);

  const setTheme = useCallback((value: ThemePreference) => {
    setThemeState(value);
    if (!isBrowser()) return;
    if (value === "system") {
      window.localStorage.removeItem(STORAGE_KEY);
    } else {
      window.localStorage.setItem(STORAGE_KEY, value);
    }
  }, []);

  const toggleTheme = useCallback(() => {
    setTheme(resolvedTheme === "dark" ? "light" : "dark");
  }, [resolvedTheme, setTheme]);

  const contextValue = useMemo<ThemeContextValue>(
    () => ({ theme, resolvedTheme, setTheme, toggleTheme }),
    [theme, resolvedTheme, setTheme, toggleTheme]
  );

  return (
    <ThemeContext.Provider value={contextValue}>
      {children}
    </ThemeContext.Provider>
  );
};

export function useTheme(): ThemeContextValue {
  const context = useContext(ThemeContext);
  return context;
}

type ThemeToggleProps = {
  className?: string;
  inactiveLabel?: string;
  activeLabel?: string;
};

export function ThemeToggle({
  className,
  inactiveLabel = "Switch to dark mode",
  activeLabel = "Switch to light mode",
}: ThemeToggleProps) {
  const { resolvedTheme, toggleTheme } = useTheme();
  const isDark = resolvedTheme === "dark";

  return (
    <button
      type="button"
      onClick={toggleTheme}
      className={cx("cf-theme-toggle", className)}
      aria-label={isDark ? activeLabel : inactiveLabel}
      data-theme-state={resolvedTheme}
    >
      <span aria-hidden="true" className="cf-theme-toggle__icon">
        {isDark ? (
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            width="20"
            height="20"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M12 3a1 1 0 0 1 1 1v1.25a1 1 0 0 1-2 0V4a1 1 0 0 1 1-1Zm7.778 3.222a1 1 0 0 1 0 1.414l-.884.884a1 1 0 0 1-1.414-1.414l.884-.884a1 1 0 0 1 1.414 0ZM21 13a1 1 0 0 1-1 1h-1.25a1 1 0 0 1 0-2H20a1 1 0 0 1 1 1Zm-4.222 7.778a1 1 0 0 1-1.414 0l-.884-.884a1 1 0 0 1 1.414-1.414l.884.884a1 1 0 0 1 0 1.414ZM13 21a1 1 0 0 1-2 0v-1.25a1 1 0 0 1 2 0V21Zm-7.778-3.222a1 1 0 0 1 0-1.414l.884-.884a1 1 0 0 1 1.414 1.414l-.884.884a1 1 0 0 1-1.414 0ZM4 13a1 1 0 0 1 0-2h1.25a1 1 0 0 1 0 2H4Zm3.222-7.778a1 1 0 0 1 1.414 0l.884.884A1 1 0 1 1 8.106 7.52l-.884-.884a1 1 0 0 1 0-1.414ZM12 8a4 4 0 1 1 0 8 4 4 0 0 1 0-8Z"
            />
          </svg>
        ) : (
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            width="20"
            height="20"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M21 15a9 9 0 1 1-9-9c.34 0 .675.02 1.005.06a1 1 0 0 1 .69 1.6A6.001 6.001 0 0 0 19.34 14.3a1 1 0 0 1 .768 1.532A8.96 8.96 0 0 1 21 15Z"
            />
          </svg>
        )}
      </span>
    </button>
  );
}

type ThemeScriptProps = {
  storageKey?: string;
};

export function ThemeScript({
  storageKey = STORAGE_KEY,
}: ThemeScriptProps = {}) {
  const script = `(() => {\n  try {\n    const storageKey = ${JSON.stringify(
    storageKey
  )};\n    const root = document.documentElement;\n    const stored = window.localStorage.getItem(storageKey);\n    const media = window.matchMedia('(prefers-color-scheme: dark)');\n    const resolved = stored === 'light' || stored === 'dark' ? stored : media.matches ? 'dark' : 'light';\n    root.classList.toggle('dark', resolved === 'dark');\n    root.dataset.theme = resolved;\n    root.style.colorScheme = resolved;\n  } catch (error) {\n    console.error('theme hydration failed', error);\n  }\n})();`;

  return <script dangerouslySetInnerHTML={{ __html: script }} />;
}

export { STORAGE_KEY as themeStorageKey };
