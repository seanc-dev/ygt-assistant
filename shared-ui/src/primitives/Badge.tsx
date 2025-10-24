import { HTMLAttributes } from "react";
import clsx from "clsx";

export type BadgeTone =
  | "neutral"
  | "info"
  | "success"
  | "warning"
  | "danger"
  | "calm";

export type BadgeProps = HTMLAttributes<HTMLSpanElement> & {
  tone?: BadgeTone;
  soft?: boolean;
};

const softTone: Record<BadgeTone, string> = {
  neutral: "bg-slate-100/70 text-slate-700 dark:bg-slate-800/70 dark:text-slate-200",
  info: "bg-sky-100/70 text-sky-700 dark:bg-sky-900/40 dark:text-sky-300",
  success: "bg-emerald-100/80 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300",
  warning: "bg-amber-100/80 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300",
  danger: "bg-rose-100/80 text-rose-700 dark:bg-rose-900/40 dark:text-rose-300",
  calm: "bg-indigo-100/70 text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-300",
};

const solidTone: Record<BadgeTone, string> = {
  neutral: "bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900",
  info: "bg-sky-600 text-white",
  success: "bg-emerald-600 text-white",
  warning: "bg-amber-600 text-white",
  danger: "bg-rose-600 text-white",
  calm: "bg-indigo-600 text-white",
};

export function Badge({ tone = "neutral", soft = true, className, ...props }: BadgeProps) {
  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium",
        soft ? softTone[tone] : solidTone[tone],
        className
      )}
      {...props}
    />
  );
}
