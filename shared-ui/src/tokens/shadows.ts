/**
 * LucidWork Design System - Shadow Tokens
 * 
 * Single soft shadow: 8% opacity black, y-offset = 2px, blur = 8px
 * Cards: subtle elevation on hover (translateY -2px)
 */

export const shadows = {
  none: "none",
  sm: "0 2px 8px rgba(0, 0, 0, 0.08)", // Primary shadow - 8% opacity, 2px offset, 8px blur
  md: "0 4px 16px rgba(0, 0, 0, 0.08)",
  lg: "0 8px 24px rgba(0, 0, 0, 0.08)",
  cardHover: "0 2px 8px rgba(0, 0, 0, 0.08)", // For card hover elevation
  inset: "inset 0 1px 0 rgba(255, 255, 255, 0.1)",
} as const;

export type ShadowToken = keyof typeof shadows;
