/**
 * LucidWork Design System - Typography Tokens
 * 
 * Primary: Inter (400/500/700) - Body text, labels, system text
 * Secondary: Space Grotesk (500/700) - Headings, wordmark, section headers
 * 
 * Letter spacing: +0.02em for uppercase headings
 * Line height: 1.45 for text blocks; 1.2 for headings
 */

export const typography = {
  fontFamily: {
    body: "'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif",
    heading: "'Space Grotesk', 'Inter', system-ui, -apple-system, sans-serif",
  },
  sizes: {
    xs: "0.75rem",
    sm: "0.875rem",
    md: "1rem",
    lg: "1.125rem",
    xl: "1.375rem",
    "2xl": "1.5rem",
    "3xl": "1.875rem",
    display: "2rem",
  },
  lineHeights: {
    tight: 1.2, // Headings
    normal: 1.45, // Text blocks
    relaxed: 1.75,
  },
  weights: {
    regular: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
  },
  letterSpacing: {
    normal: "0",
    wide: "0.02em", // Uppercase headings
  },
} as const;

export type TypographyToken = typeof typography;
