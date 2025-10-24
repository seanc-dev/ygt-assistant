import { ButtonHTMLAttributes, forwardRef } from "react";
import clsx from "clsx";

export type ButtonVariant =
  | "primary"
  | "secondary"
  | "subtle"
  | "danger"
  | "ghost";

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: "sm" | "md";
  block?: boolean;
}

const baseStyles =
  "inline-flex items-center justify-center rounded-full border transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:opacity-60 disabled:cursor-not-allowed";

const variantStyles: Record<ButtonVariant, string> = {
  primary:
    "border-transparent bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 focus-visible:ring-indigo-500",
  secondary:
    "border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-900 hover:bg-slate-50 focus-visible:ring-indigo-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100",
  subtle:
    "border-transparent bg-slate-100 px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-200 focus-visible:ring-indigo-500 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700",
  danger:
    "border-transparent bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-500 focus-visible:ring-red-500",
  ghost:
    "border-transparent bg-transparent px-3 py-1.5 text-sm font-medium text-indigo-600 hover:bg-indigo-50 focus-visible:ring-indigo-500 dark:text-indigo-300 dark:hover:bg-indigo-950/50",
};

const sizeStyles: Record<NonNullable<ButtonProps["size"]>, string> = {
  sm: "text-xs px-3 py-1.5",
  md: "text-sm px-4 py-2",
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { variant = "primary", size = "md", className, block, ...props },
  ref
) {
  return (
    <button
      ref={ref}
      className={clsx(
        baseStyles,
        variantStyles[variant],
        sizeStyles[size],
        block && "w-full",
        className
      )}
      {...props}
    />
  );
});
