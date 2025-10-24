export const typography = {
  fontFamily: "'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif",
  sizes: {
    xs: "0.75rem",
    sm: "0.875rem",
    md: "1rem",
    lg: "1.125rem",
    xl: "1.375rem",
    display: "2rem",
  },
  lineHeights: {
    tight: 1.2,
    normal: 1.5,
    relaxed: 1.75,
  },
  weights: {
    regular: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
  },
} as const;

export type TypographyToken = typeof typography;
