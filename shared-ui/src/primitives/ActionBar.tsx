import { ReactNode } from "react";
import clsx from "clsx";
import { Box } from "./Box";
import { Text } from "./Text";

export type ActionBarProps = {
  primaryAction: ReactNode;
  secondaryActions?: ReactNode[];
  helperText?: string;
  tone?: "default" | "highlight";
  className?: string;
};

export function ActionBar({
  primaryAction,
  secondaryActions = [],
  helperText,
  tone = "default",
  className,
}: ActionBarProps) {
  return (
    <Box
      padding="md"
      radius="md"
      className={clsx(
        "flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between",
        tone === "highlight"
          ? "bg-slate-900 text-white shadow-md dark:bg-slate-100 dark:text-slate-900"
          : "bg-white/95 backdrop-blur border border-slate-200/70 shadow-sm dark:border-slate-800/60 dark:bg-slate-900/70",
        className
      )}
    >
      {helperText ? (
        <Text
          variant="label"
          className={clsx(
            "text-sm",
            tone === "highlight"
              ? "text-white/90 dark:text-slate-800"
              : "text-slate-600 dark:text-slate-300"
          )}
        >
          {helperText}
        </Text>
      ) : null}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:gap-3">
        <div className="flex items-center gap-2">{primaryAction}</div>
        {secondaryActions.length > 0 ? (
          <div className="flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400">
            {secondaryActions.map((action, index) => (
              <div key={index} className="flex items-center gap-2">
                {index > 0 ? <span aria-hidden="true">·</span> : null}
                {action}
              </div>
            ))}
          </div>
        ) : null}
      </div>
    </Box>
  );
}
