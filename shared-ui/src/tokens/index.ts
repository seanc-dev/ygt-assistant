import { colors } from "./colors";
import { spacing } from "./spacing";
import { typography } from "./typography";
import { radius } from "./radius";
import { shadows } from "./shadows";
import { motion } from "./motion";

export { colors, spacing, typography, radius, shadows, motion };

export const tokens = {
  colors,
  spacing,
  typography,
  radius,
  shadows,
  motion,
};

export type DesignTokens = typeof tokens;
