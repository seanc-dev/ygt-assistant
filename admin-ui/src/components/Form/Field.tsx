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
        "block w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm dark:border-slate-600 dark:bg-slate-900 dark:text-slate-100",
        "placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-0 dark:placeholder:text-slate-500 dark:focus:ring-offset-slate-900",
        invalid && "border-red-500 dark:border-red-500",
        className
      )}
      aria-invalid={invalid ? "true" : undefined}
      {...props}
    />
  );
});
