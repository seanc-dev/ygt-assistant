import { ComponentPropsWithoutRef, forwardRef } from "react";
import clsx from "clsx";

export type TextareaProps = ComponentPropsWithoutRef<"textarea"> & {
  invalid?: boolean;
};

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  function Textarea({ className, invalid, ...props }, ref) {
    return (
      <textarea
        ref={ref}
        className={clsx(
          "block w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm",
          "placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-0",
          "min-h-[6rem]",
          invalid && "border-red-500",
          className
        )}
        aria-invalid={invalid ? "true" : undefined}
        {...props}
      />
    );
  }
);
