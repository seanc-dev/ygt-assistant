import { createElement, forwardRef, type HTMLAttributes } from "react";
import clsx from "clsx";
import { typography } from "../tokens/typography";

export type TextVariant = "label" | "body" | "muted" | "caption";
export type HeadingVariant = "title" | "subtitle" | "display";

type BaseProps = HTMLAttributes<HTMLElement> & {
  as?: keyof JSX.IntrinsicElements;
};

export type TextProps = BaseProps & {
  variant?: TextVariant;
};

export const Text = forwardRef<HTMLElement, TextProps>(function Text(
  { as = "p", variant = "body", className, style, ...props },
  ref
) {
  const sizeMap: Record<TextVariant, string> = {
    label: "text-sm font-medium",
    body: "text-sm",
    muted: "text-sm text-slate-500 dark:text-slate-400",
    caption: "text-xs text-slate-500 dark:text-slate-400",
  };

  return createElement(as, {
    ref,
    className: clsx("font-normal", sizeMap[variant], className),
    style: {
      fontFamily: typography.fontFamily,
      lineHeight: typography.lineHeights.normal,
      ...style,
    },
    ...props,
  });
});

export type HeadingProps = BaseProps & {
  variant?: HeadingVariant;
};

export const Heading = forwardRef<HTMLElement, HeadingProps>(function Heading(
  { as = "h2", variant = "title", className, style, ...props },
  ref
) {
  const variantMap: Record<HeadingVariant, string> = {
    display: "text-3xl font-semibold",
    title: "text-xl font-semibold",
    subtitle: "text-base font-semibold text-slate-600 dark:text-slate-300",
  };

  const lineHeightMap: Record<HeadingVariant, number> = {
    display: typography.lineHeights.tight,
    title: typography.lineHeights.tight,
    subtitle: typography.lineHeights.normal,
  };

  const fontSizeMap: Record<HeadingVariant, string> = {
    display: typography.sizes.display,
    title: typography.sizes.xl,
    subtitle: typography.sizes.md,
  };

  return createElement(as, {
    ref,
    className: clsx(variantMap[variant], className),
    style: {
      fontFamily: typography.fontFamily,
      lineHeight: lineHeightMap[variant],
      fontSize: fontSizeMap[variant],
      ...style,
    },
    ...props,
  });
});
