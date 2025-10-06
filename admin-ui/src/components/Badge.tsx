import { HTMLAttributes } from "react";
import clsx from "clsx";

type BadgeTone = "neutral" | "info" | "success" | "warning" | "danger";

type BadgeProps = HTMLAttributes<HTMLSpanElement> & {
  tone?: BadgeTone;
};

const toneStyles: Record<BadgeTone, string> = {
  neutral: "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300",
  info: "bg-primary-50 text-primary-700 dark:bg-primary-500/20 dark:text-primary-200",
  success: "bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-200",
  warning: "bg-amber-100 text-amber-800 dark:bg-amber-500/20 dark:text-amber-200",
  danger: "bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-200",
};

export function Badge({ tone = "neutral", className, ...props }: BadgeProps) {
  return (
    <span
      className={clsx(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium capitalize",
        toneStyles[tone],
        className
      )}
      {...props}
    />
  );
}
