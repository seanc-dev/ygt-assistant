export const spacing = {
  none: "0",
  quark: "0.125rem",
  nano: "0.25rem",
  xs: "0.5rem",
  sm: "0.75rem",
  md: "1rem",
  lg: "1.5rem",
  xl: "2rem",
  xxl: "3rem",
} as const;

export type SpacingToken = keyof typeof spacing;
