import { forwardRef, type HTMLAttributes } from "react";
import clsx from "clsx";
import { spacing } from "../tokens/spacing";

export type StackProps = HTMLAttributes<HTMLDivElement> & {
  direction?: "horizontal" | "vertical";
  gap?: keyof typeof spacing | string;
  align?: "start" | "center" | "end" | "stretch";
  justify?: "start" | "center" | "end" | "between";
  wrap?: boolean;
};

const justifyMap: Record<NonNullable<StackProps["justify"]>, string> = {
  start: "justify-start",
  center: "justify-center",
  end: "justify-end",
  between: "justify-between",
};

const alignMap: Record<NonNullable<StackProps["align"]>, string> = {
  start: "items-start",
  center: "items-center",
  end: "items-end",
  stretch: "items-stretch",
};

export const Stack = forwardRef<HTMLDivElement, StackProps>(function Stack(
  {
    direction = "vertical",
    gap = "md",
    align = "stretch",
    justify = "start",
    wrap,
    className,
    style,
    ...props
  },
  ref
) {
  const gapValue = gap ? spacing[gap as keyof typeof spacing] || gap : undefined;
  return (
    <div
      ref={ref}
      className={clsx(
        "flex",
        direction === "vertical" ? "flex-col" : "flex-row",
        wrap && "flex-wrap",
        justifyMap[justify],
        alignMap[align],
        className
      )}
      style={{ gap: gapValue, ...style }}
      {...props}
    />
  );
});
