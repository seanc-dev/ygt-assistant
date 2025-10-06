import { ComponentPropsWithoutRef } from "react";
import clsx from "clsx";

export function Label({ className, ...props }: ComponentPropsWithoutRef<"label">) {
  return (
    <label
      className={clsx("block text-sm font-medium text-slate-700 dark:text-slate-300", className)}
      {...props}
    />
  );
}
