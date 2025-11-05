"use client";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useLayoutEffect,
  useMemo,
  useState,
  type ReactNode,
  type FC,
} from "react";
import { cx } from "./cx";
import { colors } from "./tokens/colors";

const STORAGE_KEY = "lucid-work-theme";

export type ThemePreference = "light" | "dark" | "system" | "high-contrast" | "color-blind";
export type Theme = "light" | "dark" | "high-contrast" | "color-blind";

const themeVariables: Record<Theme, Record<string, string>> = {
  light: {
    "--ds-surface": colors.background.surface,
    "--ds-surface-muted": colors.background.elevated,
    "--ds-surface-calm": colors.background.accent,
    "--ds-text-primary": colors.text.primary,
    "--ds-text-secondary": colors.text.secondary,
    "--ds-text-subtle": colors.text.subtle,
    "--ds-text-accent": colors.text.accent,
    "--ds-border-subtle": colors.border.subtle,
    "--ds-border-prominent": colors.border.prominent,
    "--ds-brand": colors.brand.primary,
    "--ds-brand-contrast": colors.brand.contrast,
    "--ds-status-info": colors.status.info,
    "--ds-status-success": colors.status.success,
    "--ds-status-warning": colors.status.warning,
    "--ds-status-danger": colors.status.danger,
    // LucidWork tokens
    "--lw-primary": colors.light.primary,
    "--lw-secondary": colors.light.secondary,
    "--lw-base": colors.light.base,
    "--lw-neutral-text": colors.light.neutralText,
    "--lw-neutral-muted": colors.light.neutralMuted,
    "--lw-success": colors.light.success,
    "--lw-warning": colors.light.warning,
    "--lw-surface": colors.light.surface,
    "--lw-error": colors.light.error,
  },
  dark: {
    "--ds-surface": colors.background.surfaceDark,
    "--ds-surface-muted": colors.background.elevatedDark,
    "--ds-surface-calm": colors.background.accentDark,
    "--ds-text-primary": colors.text.primaryDark,
    "--ds-text-secondary": colors.text.secondaryDark,
    "--ds-text-subtle": colors.text.subtleDark,
    "--ds-text-accent": colors.text.accentDark,
    "--ds-border-subtle": colors.border.subtleDark,
    "--ds-border-prominent": colors.border.prominentDark,
    "--ds-brand": colors.brand.primaryDark,
    "--ds-brand-contrast": colors.brand.contrast,
    "--ds-status-info": colors.status.infoDark,
    "--ds-status-success": colors.status.successDark,
    "--ds-status-warning": colors.status.warningDark,
    "--ds-status-danger": colors.status.dangerDark,
    // LucidWork tokens
    "--lw-primary": colors.dark.primary,
    "--lw-secondary": colors.dark.secondary,
    "--lw-base": colors.dark.base,
    "--lw-neutral-text": colors.dark.textPrimary,
    "--lw-neutral-muted": colors.dark.textMuted,
    "--lw-success": colors.dark.success,
    "--lw-warning": colors.dark.warning,
    "--lw-surface": colors.dark.surface,
    "--lw-error": colors.dark.error,
  },
  "high-contrast": {
    "--ds-surface": colors.highContrast.base,
    "--ds-surface-muted": colors.highContrast.base,
    "--ds-surface-calm": colors.highContrast.base,
    "--ds-text-primary": colors.highContrast.textPrimary,
    "--ds-text-secondary": colors.highContrast.textPrimary,
    "--ds-text-subtle": colors.highContrast.textPrimary,
    "--ds-text-accent": colors.highContrast.accent1,
    "--ds-border-subtle": colors.highContrast.textPrimary,
    "--ds-border-prominent": colors.highContrast.textPrimary,
    "--ds-brand": colors.highContrast.accent1,
    "--ds-brand-contrast": colors.highContrast.base,
    "--ds-status-info": colors.highContrast.accent1,
    "--ds-status-success": colors.highContrast.success,
    "--ds-status-warning": colors.highContrast.accent2,
    "--ds-status-danger": colors.highContrast.error,
    // LucidWork tokens
    "--lw-primary": colors.highContrast.accent1,
    "--lw-secondary": colors.highContrast.accent2,
    "--lw-base": colors.highContrast.base,
    "--lw-neutral-text": colors.highContrast.textPrimary,
    "--lw-neutral-muted": colors.highContrast.textPrimary,
    "--lw-success": colors.highContrast.success,
    "--lw-warning": colors.highContrast.accent2,
    "--lw-surface": colors.highContrast.base,
    "--lw-error": colors.highContrast.error,
  },
  "color-blind": {
    "--ds-surface": colors.colorBlind.background,
    "--ds-surface-muted": colors.colorBlind.background,
    "--ds-surface-calm": colors.colorBlind.background,
    "--ds-text-primary": colors.text.primary,
    "--ds-text-secondary": colors.text.secondary,
    "--ds-text-subtle": colors.text.subtle,
    "--ds-text-accent": colors.colorBlind.primary,
    "--ds-border-subtle": colors.border.subtle,
    "--ds-border-prominent": colors.colorBlind.primary,
    "--ds-brand": colors.colorBlind.primary,
    "--ds-brand-contrast": colors.brand.contrast,
    "--ds-status-info": colors.colorBlind.info,
    "--ds-status-success": colors.colorBlind.success,
    "--ds-status-warning": colors.colorBlind.warning,
    "--ds-status-danger": colors.colorBlind.error,
    // LucidWork tokens
    "--lw-primary": colors.colorBlind.primary,
    "--lw-secondary": colors.colorBlind.info,
    "--lw-base": colors.colorBlind.background,
    "--lw-neutral-text": colors.text.primary,
    "--lw-neutral-muted": colors.text.secondary,
    "--lw-success": colors.colorBlind.success,
    "--lw-warning": colors.colorBlind.warning,
    "--lw-surface": colors.colorBlind.background,
    "--lw-error": colors.colorBlind.error,
  },
};

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
  
  // Set color-scheme only for light/dark modes
  if (theme === "light" || theme === "dark") {
    root.style.colorScheme = theme;
  } else {
    root.style.colorScheme = "light";
  }
  
  const vars = themeVariables[theme];
  Object.entries(vars).forEach(([key, value]) => {
    root.style.setProperty(key, value);
  });
}

type ThemeProviderProps = {
  children: ReactNode;
  defaultTheme?: ThemePreference;
};

export const ThemeProvider: FC<ThemeProviderProps> = ({
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
    if (stored === "light" || stored === "dark" || stored === "high-contrast" || stored === "color-blind") {
      setThemeState(stored as ThemePreference);
    } else if (stored === "system") {
      setThemeState("system");
    }
  }, []);

  useIsomorphicLayoutEffect(() => {
    const mediaQuery = isBrowser()
      ? window.matchMedia("(prefers-color-scheme: dark)")
      : null;

    const resolve = (value: ThemePreference): Theme => {
      if (value === "system") {
        return mediaQuery?.matches ? "dark" : "light";
      }
      return value as Theme;
    };

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
    // Cycle through: light -> dark -> light
    if (theme === "system") {
      setTheme(resolvedTheme === "dark" ? "light" : "dark");
    } else if (theme === "light") {
      setTheme("dark");
    } else if (theme === "dark") {
      setTheme("light");
    } else {
      // For special modes, default to light
      setTheme("light");
    }
  }, [theme, resolvedTheme, setTheme]);

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
