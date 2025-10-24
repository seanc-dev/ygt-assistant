import { ReactNode } from "react";
import clsx from "clsx";
import { Box } from "./Box";
import { Heading, Text } from "./Text";
import { spacing } from "../tokens/spacing";

export type PanelProps = {
  title?: string;
  subtitle?: string;
  kicker?: string;
  description?: string;
  tone?: "default" | "soft" | "calm";
  actions?: ReactNode;
  footer?: ReactNode;
  children?: ReactNode;
  className?: string;
};

const toneClasses: Record<NonNullable<PanelProps["tone"]>, string> = {
  default:
    "bg-white/90 dark:bg-slate-900/80 border-slate-200/70 dark:border-slate-800/70", 
  soft:
    "bg-slate-50/90 dark:bg-slate-900/60 border-slate-200/60 dark:border-slate-800/60", 
  calm:
    "bg-indigo-50/90 dark:bg-indigo-950/40 border-indigo-200/60 dark:border-indigo-900/60", 
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
}: PanelProps) {
  return (
    <Box
      padding="lg"
      radius="lg"
      className={clsx(
        "relative flex flex-col gap-5 border shadow-sm transition-colors",
        toneClasses[tone],
        className
      )}
    >
      {(kicker || title || subtitle || actions) && (
        <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
          <div className="flex-1 space-y-1">
            {kicker ? (
              <Text
                as="p"
                variant="caption"
                className="uppercase tracking-wide text-indigo-500 dark:text-indigo-300"
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
          className="border-t border-slate-200/70 pt-4 dark:border-slate-800/60"
          style={{ marginTop: spacing.md }}
        >
          {footer}
        </div>
      ) : null}
    </Box>
  );
}
