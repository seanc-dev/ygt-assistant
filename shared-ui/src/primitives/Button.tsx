import { ButtonHTMLAttributes, forwardRef } from "react";
import clsx from "clsx";
import { radius } from "../tokens/radius";
import { motion } from "../tokens/motion";

/**
 * LucidWork Button Component
 * 
 * Variants:
 * - solid (primary): Core actions
 * - outline (secondary): Secondary actions
 * - ghost (tertiary): Tertiary actions
 * 
 * Design: Rounded 4px, calm transitions, focus glow @ 40% opacity
 */
export type ButtonVariant = "solid" | "outline" | "ghost";
export type ButtonSize = "sm" | "md" | "lg";

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  block?: boolean;
}

const baseStyles = clsx(
  "inline-flex items-center justify-center",
  "font-medium transition-all",
  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2",
  "disabled:opacity-60 disabled:cursor-not-allowed",
  "disabled:pointer-events-none"
);

const variantStyles: Record<ButtonVariant, string> = {
  solid: clsx(
    "bg-[var(--lw-primary)] text-white",
    "hover:opacity-90",
    "focus-visible:ring-[var(--lw-primary)] focus-visible:ring-opacity-40",
    "active:opacity-80"
  ),
  outline: clsx(
    "border border-[var(--lw-border)] bg-[var(--lw-surface)] text-[var(--lw-neutral-text)]",
    "hover:bg-[var(--lw-base)]",
    "focus-visible:ring-[var(--lw-primary)] focus-visible:ring-opacity-40",
    "dark:border-[var(--lw-border)] dark:bg-[var(--lw-surface)] dark:text-[var(--lw-neutral-text)]"
  ),
  ghost: clsx(
    "bg-transparent text-[var(--lw-primary)]",
    "hover:bg-[var(--lw-base)]",
    "focus-visible:ring-[var(--lw-primary)] focus-visible:ring-opacity-40",
    "active:opacity-80"
  ),
};

const sizeStyles: Record<ButtonSize, string> = {
  sm: "text-sm px-3 py-1.5",
  md: "text-sm px-4 py-2",
  lg: "text-base px-6 py-3",
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { variant = "solid", size = "md", className, block, style, ...props },
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
      style={{
        borderRadius: radius.sm, // 4px
        transitionDuration: motion.duration.normal, // 180ms
        transitionTimingFunction: motion.easing.default,
        ...style,
      }}
      {...props}
    />
  );
});
