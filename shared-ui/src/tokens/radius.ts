export const radius = {
  none: "0",
  sm: "0.375rem",
  md: "0.75rem",
  lg: "1.25rem",
  pill: "9999px",
} as const;

export type RadiusToken = keyof typeof radius;
