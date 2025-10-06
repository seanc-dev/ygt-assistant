import { ButtonHTMLAttributes } from "react";
import clsx from "clsx";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost" | "danger";
}

export function Button({ variant = "primary", className, ...props }: ButtonProps) {
  const base =
    "inline-flex items-center justify-center rounded-md px-4 py-2 text-sm font-medium transition focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 dark:focus-visible:ring-offset-slate-900";
  const variants: Record<NonNullable<ButtonProps["variant"]>, string> = {
    primary:
      "bg-primary-600 text-white hover:bg-primary-500 focus-visible:ring-primary-500 dark:bg-primary-500 dark:hover:bg-primary-400 dark:focus-visible:ring-primary-400",
    secondary:
      "bg-slate-100 text-slate-900 hover:bg-slate-200 focus-visible:ring-primary-500 dark:bg-slate-800 dark:text-slate-100 dark:hover:bg-slate-700",
    ghost:
      "bg-transparent text-primary-600 hover:bg-primary-50 focus-visible:ring-primary-500 dark:text-primary-300 dark:hover:bg-slate-800/60",
    danger:
      "bg-red-600 text-white hover:bg-red-500 focus-visible:ring-red-500 dark:bg-red-500 dark:hover:bg-red-400",
  };
  return <button className={clsx(base, variants[variant], className)} {...props} />;
}
