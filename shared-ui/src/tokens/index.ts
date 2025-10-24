import { colors } from "./colors";
import { spacing } from "./spacing";
import { typography } from "./typography";
import { radius } from "./radius";
import { shadows } from "./shadows";

export { colors, spacing, typography, radius, shadows };

export const tokens = {
  colors,
  spacing,
  typography,
  radius,
  shadows,
};

export type DesignTokens = typeof tokens;
