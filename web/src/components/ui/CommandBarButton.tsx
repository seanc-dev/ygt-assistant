import { ButtonHTMLAttributes, ReactNode } from "react";

interface CommandBarButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant: "subtle" | "ghost";
  size?: "xs";
  children: ReactNode;
}

/**
 * Fluent-style button for CommandBar.
 * Subtle variant for quick actions, ghost variant for navigation.
 * Size "xs" = 28px height (h-7).
 */
export function CommandBarButton({
  variant,
  size = "xs",
  children,
  className,
  ...props
}: CommandBarButtonProps) {
  const baseStyles =
    "inline-flex items-center gap-1.5 h-7 rounded-md text-sm leading-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-300 transition-colors";

  const variantStyles = {
    subtle:
      "bg-slate-100 text-slate-800 px-2.5 hover:bg-slate-200",
    ghost: "bg-transparent text-slate-600 px-1 hover:text-slate-800 hover:bg-slate-100",
  };

  return (
    <button
      className={`${baseStyles} ${variantStyles[variant]} ${className || ""}`}
      {...props}
    >
      {children}
    </button>
  );
}
