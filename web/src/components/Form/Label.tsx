import { ComponentPropsWithoutRef } from "react";
import clsx from "clsx";

export function Label({ className, ...props }: ComponentPropsWithoutRef<"label">) {
  return (
    <label
      className={clsx(
        "block text-sm font-medium text-[color:var(--ds-text-secondary)]",
        className
      )}
      {...props}
    />
  );
}
