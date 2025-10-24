export const shadows = {
  none: "none",
  sm: "0 1px 2px rgba(15, 23, 42, 0.08)",
  md: "0 10px 40px rgba(15, 23, 42, 0.08)",
  inset: "inset 0 1px 0 rgba(255, 255, 255, 0.1)",
} as const;

export type ShadowToken = keyof typeof shadows;
