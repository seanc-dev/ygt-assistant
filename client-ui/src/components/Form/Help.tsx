import { ComponentPropsWithoutRef } from "react";
import clsx from "clsx";

export function Help({ className, ...props }: ComponentPropsWithoutRef<"p">) {
  return (
    <p
      className={clsx("mt-1 text-sm text-slate-500", className)}
      {...props}
    />
  );
}
