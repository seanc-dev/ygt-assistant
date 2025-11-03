/**
 * LucidWork Design System - Radius Tokens
 * 
 * Small UI elements: 4px
 * Cards/Panels: 6px
 */

export const radius = {
  none: "0",
  sm: "0.25rem", // 4px - small UI elements
  md: "0.375rem", // 6px - cards, panels
  lg: "0.5rem", // 8px
  xl: "0.75rem", // 12px
  pill: "9999px",
} as const;

export type RadiusToken = keyof typeof radius;
