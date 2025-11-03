import { ReactNode, type HTMLAttributes } from "react";
import clsx from "clsx";
import { Box } from "./Box";
import { Heading, Text } from "./Text";
import { spacing } from "../tokens/spacing";
import { radius } from "../tokens/radius";
import { shadows } from "../tokens/shadows";
import { motion } from "../tokens/motion";

/**
 * LucidWork Panel Component
 * 
 * Design: Cards with calm depth, subtle elevation on hover
 * - Flat by default, subtle elevation on hover (translateY -2px, 150ms)
 * - Inline expansion to chat: scale 1 → 1.02 (200ms), then fade content in
 * - Radius: 6px for cards/panels
 */
export type PanelProps = HTMLAttributes<HTMLDivElement> & {
  title?: string;
  subtitle?: string;
  kicker?: string;
  description?: string;
  tone?: "default" | "soft" | "calm";
  actions?: ReactNode;
  footer?: ReactNode;
  hoverable?: boolean;
  expandable?: boolean;
};

const toneClasses: Record<NonNullable<PanelProps["tone"]>, string> = {
  default: clsx(
    "bg-[var(--lw-surface)] border-[var(--lw-border)]",
    "dark:bg-[var(--lw-surface)] dark:border-[var(--lw-border)]"
  ),
  soft: clsx(
    "bg-[var(--lw-base)] border-[var(--lw-border)]",
    "dark:bg-[var(--lw-base)] dark:border-[var(--lw-border)]"
  ),
  calm: clsx(
    "bg-[var(--lw-base)] border-[var(--lw-primary)] border-opacity-20",
    "dark:bg-[var(--lw-base)] dark:border-[var(--lw-primary)] dark:border-opacity-20"
  ),
};

export function Panel({
  title,
  subtitle,
  kicker,
  description,
  tone = "default",
  actions,
  footer,
  children,
  className,
  hoverable = false,
  expandable = false,
  ...htmlProps
}: PanelProps) {
  return (
    <Box
      padding="lg"
      radius="md"
      className={clsx(
        "relative flex flex-col gap-5 border shadow-sm transition-all",
        toneClasses[tone],
        hoverable && "lw-card-hover cursor-pointer",
        expandable && "lw-card-expand",
        className
      )}
      style={{
        borderRadius: radius.md, // 6px
        boxShadow: shadows.sm,
        transitionDuration: hoverable ? motion.duration.fast : motion.duration.normal,
        transitionTimingFunction: motion.easing.default,
      }}
      {...htmlProps}
    >
      {(kicker || title || subtitle || actions) && (
        <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
          <div className="flex-1 space-y-1">
            {kicker ? (
              <Text
                as="p"
                variant="caption"
                className="uppercase tracking-wide text-[var(--lw-primary)]"
              >
                {kicker}
              </Text>
            ) : null}
            {title ? <Heading as="h2" variant="title">{title}</Heading> : null}
            {subtitle ? (
              <Heading as="p" variant="subtitle">
                {subtitle}
              </Heading>
            ) : null}
            {description ? <Text variant="muted">{description}</Text> : null}
          </div>
          {actions ? (
            <div className="flex-shrink-0 self-end sm:self-start">{actions}</div>
          ) : null}
        </div>
      )}
      {children ? <div className="space-y-3">{children}</div> : null}
      {footer ? (
        <div
          className="border-t border-[var(--lw-border)] pt-4"
          style={{ marginTop: spacing.md }}
        >
          {footer}
        </div>
      ) : null}
    </Box>
  );
}
