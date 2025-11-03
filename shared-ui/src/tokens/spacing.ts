/**
 * LucidWork Design System - Spacing Tokens
 * 
 * Base: 8px spacing system
 * Vertical rhythm: 32px minimum between sections
 */

export const spacing = {
  none: "0",
  quark: "0.125rem", // 2px
  nano: "0.25rem", // 4px
  xs: "0.5rem", // 8px - base unit
  sm: "0.75rem", // 12px
  md: "1rem", // 16px
  lg: "1.5rem", // 24px
  xl: "2rem", // 32px - vertical rhythm minimum
  "2xl": "2.5rem", // 40px
  "3xl": "3rem", // 48px
  "4xl": "4rem", // 64px
} as const;

export type SpacingToken = keyof typeof spacing;
