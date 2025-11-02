import { useEffect, useCallback, useRef } from "react";

export interface HotkeyConfig {
  [key: string]: string; // action -> key combo
}

export interface HotkeyHandlers {
  [key: string]: () => void; // action -> handler
}

/**
 * Parse a key combination string into normalized form.
 * Examples: "a" -> "a", "Meta+k" -> "Meta+k", "Ctrl+Enter" -> "Control+Enter"
 */
function normalizeKey(key: string): string {
  return key
    .toLowerCase()
    .replace(/ctrl/g, "Control")
    .replace(/cmd/g, "Meta")
    .replace(/⌘/g, "Meta")
    .replace(/⌃/g, "Control")
    .replace(/⌥/g, "Alt")
    .replace(/⇧/g, "Shift");
}

/**
 * Check if a keyboard event matches a normalized key combination.
 */
function matchesKey(event: KeyboardEvent, combo: string): boolean {
  const normalized = normalizeKey(combo);
  const parts = normalized.split("+");
  
  const key = parts[parts.length - 1];
  const modifiers = parts.slice(0, -1);
  
  // Check main key
  if (event.key.toLowerCase() !== key.toLowerCase() && event.key !== key) {
    return false;
  }
  
  // Check modifiers
  const hasMeta = modifiers.includes("meta");
  const hasControl = modifiers.includes("control");
  const hasAlt = modifiers.includes("alt");
  const hasShift = modifiers.includes("shift");
  
  if (hasMeta && !event.metaKey) return false;
  if (hasControl && !event.ctrlKey) return false;
  if (hasAlt && !event.altKey) return false;
  if (hasShift && !event.shiftKey) return false;
  
  // Ensure no extra modifiers are pressed
  if (!hasMeta && event.metaKey) return false;
  if (!hasControl && event.ctrlKey) return false;
  if (!hasAlt && event.altKey) return false;
  if (!hasShift && event.shiftKey) return false;
  
  return true;
}

/**
 * Hook for handling keyboard shortcuts.
 * 
 * @param handlers Map of action names to handler functions
 * @param config Map of action names to key combinations (optional, uses defaults if not provided)
 * @param enabled Whether hotkeys are enabled (default: true)
 * @param excludeTags HTML tags to ignore (default: ["INPUT", "TEXTAREA", "SELECT"])
 */
export function useHotkeys(
  handlers: HotkeyHandlers,
  config?: HotkeyConfig,
  enabled: boolean = true,
  excludeTags: string[] = ["INPUT", "TEXTAREA", "SELECT"]
) {
  const handlersRef = useRef(handlers);
  const configRef = useRef(config);
  
  useEffect(() => {
    handlersRef.current = handlers;
    configRef.current = config;
  }, [handlers, config]);
  
  const keyHandler = useCallback(
    (event: KeyboardEvent) => {
      if (!enabled) return;
      
      // Don't trigger if user is typing in an input field
      const tag = (event.target as HTMLElement)?.tagName;
      if (excludeTags.includes(tag || "")) return;
      
      // Check each configured hotkey
      const effectiveConfig = configRef.current || {};
      for (const [action, handler] of Object.entries(handlersRef.current)) {
        const keyCombo = effectiveConfig[action] || action; // Fallback to action name as key
        if (matchesKey(event, keyCombo)) {
          event.preventDefault();
          handler();
          break; // Only trigger first match
        }
      }
    },
    [enabled, excludeTags]
  );
  
  useEffect(() => {
    if (!enabled) return;
    
    window.addEventListener("keydown", keyHandler);
    return () => {
      window.removeEventListener("keydown", keyHandler);
    };
  }, [keyHandler, enabled]);
}

/**
 * Format a key combination for display.
 */
export function formatKeyCombo(combo: string): string {
  const normalized = normalizeKey(combo);
  const parts = normalized.split("+");
  
  const key = parts[parts.length - 1];
  const modifiers = parts.slice(0, -1);
  
  const modifierSymbols: { [key: string]: string } = {
    meta: "⌘",
    control: "⌃",
    alt: "⌥",
    shift: "⇧",
  };
  
  const displayModifiers = modifiers
    .map((m) => modifierSymbols[m.toLowerCase()] || m.charAt(0).toUpperCase())
    .join("");
  
  const displayKey = key === "escape" ? "Esc" : key.toUpperCase();
  
  return displayModifiers ? `${displayModifiers}${displayKey}` : displayKey;
}

