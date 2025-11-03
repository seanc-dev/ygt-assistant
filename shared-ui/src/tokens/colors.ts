/**
 * LucidWork Design System - Color Tokens
 * 
 * Core Brand Essence: Clarity, Calm, Controlled Productivity
 * Supports: Light, Dark, High-Contrast, Color-Blind Safe palettes
 */

// Light Mode Palette
export const lightColors = {
  primary: "#2563EB",
  secondary: "#0EA5E9",
  base: "#F9FAFB",
  neutralText: "#1E293B",
  neutralMuted: "#64748B",
  success: "#10B981",
  warning: "#FBBF24",
  surface: "#FFFFFF",
  error: "#DC2626",
} as const;

// Dark Mode Palette
export const darkColors = {
  base: "#0F172A",
  surface: "#1E293B",
  primary: "#3B82F6",
  secondary: "#06B6D4",
  textPrimary: "#F1F5F9",
  textMuted: "#94A3B8",
  success: "#34D399",
  warning: "#FACC15",
  error: "#F87171",
} as const;

// High-Contrast Palette
export const highContrastColors = {
  base: "#FFFFFF",
  textPrimary: "#000000",
  accent1: "#0000FF",
  accent2: "#00AEEF",
  error: "#FF0000",
  success: "#007E33",
} as const;

// Color-Blind Safe Palette (distinguishable for protanopia, deuteranopia, tritanopia)
export const colorBlindColors = {
  primary: "#1F77B4",
  success: "#2CA02C",
  warning: "#FF7F0E",
  info: "#17BECF",
  error: "#D62728",
  background: "#F8F9FA",
} as const;

export const colors = {
  light: lightColors,
  dark: darkColors,
  highContrast: highContrastColors,
  colorBlind: colorBlindColors,
  // Legacy structure for backwards compatibility
  background: {
    canvas: lightColors.base,
    canvasDark: darkColors.base,
    surface: lightColors.surface,
    surfaceDark: darkColors.surface,
    elevated: "#F1F5F9",
    elevatedDark: "#111827",
    accent: "#EEF2FF",
    accentDark: "#312E81",
  },
  text: {
    primary: lightColors.neutralText,
    primaryDark: darkColors.textPrimary,
    secondary: lightColors.neutralMuted,
    secondaryDark: darkColors.textMuted,
    subtle: lightColors.neutralMuted,
    subtleDark: darkColors.textMuted,
    accent: lightColors.primary,
    accentDark: darkColors.primary,
  },
  border: {
    subtle: "#E2E8F0",
    subtleDark: "#1F2937",
    prominent: "#CBD5F5",
    prominentDark: "#312E81",
  },
  status: {
    info: lightColors.primary,
    infoSurface: "#DBEAFE",
    infoDark: darkColors.primary,
    infoSurfaceDark: "#1E3A8A",
    success: lightColors.success,
    successSurface: "#DCFCE7",
    successDark: darkColors.success,
    successSurfaceDark: "#14532D",
    warning: lightColors.warning,
    warningSurface: "#FEF3C7",
    warningDark: darkColors.warning,
    warningSurfaceDark: "#78350F",
    danger: lightColors.error,
    dangerSurface: "#FEE2E2",
    dangerDark: darkColors.error,
    dangerSurfaceDark: "#7F1D1D",
  },
  brand: {
    primary: lightColors.primary,
    primaryDark: darkColors.primary,
    contrast: "#FFFFFF",
  },
} as const;

export type ColorToken = typeof colors;
