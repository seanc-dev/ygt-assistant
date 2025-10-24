import { ComponentPropsWithoutRef, forwardRef } from "react";
import clsx from "clsx";

export type FieldProps = ComponentPropsWithoutRef<"input"> & {
  invalid?: boolean;
};

export const Field = forwardRef<HTMLInputElement, FieldProps>(function Field(
  { className, invalid, type = "text", ...props },
  ref
) {
  return (
    <input
      ref={ref}
      type={type}
      className={clsx(
        "block w-full rounded-md border border-[color:var(--ds-border-subtle)] bg-[color:var(--ds-surface)] px-3 py-2 text-sm text-[color:var(--ds-text-primary)] shadow-sm",
        "placeholder:text-[color:var(--ds-text-subtle)] focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:ring-offset-2 focus:ring-offset-[color:var(--ds-surface-muted)]",
        invalid && "border-red-500 dark:border-red-500",
        className
      )}
      aria-invalid={invalid ? "true" : undefined}
      {...props}
    />
  );
});
