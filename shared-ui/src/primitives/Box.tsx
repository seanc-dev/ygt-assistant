import { forwardRef, type HTMLAttributes } from "react";
import clsx from "clsx";
import { spacing } from "../tokens/spacing";
import { radius } from "../tokens/radius";
import { shadows } from "../tokens/shadows";

export type BoxProps = HTMLAttributes<HTMLDivElement> & {
  padding?: keyof typeof spacing | string;
  gap?: keyof typeof spacing | string;
  radius?: keyof typeof radius | string;
  shadow?: keyof typeof shadows;
  border?: boolean;
};

export const Box = forwardRef<HTMLDivElement, BoxProps>(function Box(
  { className, padding, gap, radius: radiusKey, shadow, border, style, ...props },
  ref
) {
  const paddingValue = padding ? spacing[padding as keyof typeof spacing] || padding : undefined;
  const gapValue = gap ? spacing[gap as keyof typeof spacing] || gap : undefined;
  const radiusValue = radiusKey
    ? radius[radiusKey as keyof typeof radius] || radiusKey
    : undefined;
  const shadowValue = shadow ? shadows[shadow] : undefined;

  return (
    <div
      ref={ref}
      className={clsx(border && "border border-slate-200 dark:border-slate-800", className)}
      style={{
        padding: paddingValue,
        gap: gapValue,
        borderRadius: radiusValue,
        boxShadow: shadowValue,
        ...style,
      }}
      {...props}
    />
  );
});
