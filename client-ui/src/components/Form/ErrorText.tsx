import { ComponentPropsWithoutRef } from "react";
import clsx from "clsx";

export function ErrorText({ className, ...props }: ComponentPropsWithoutRef<"p">) {
  return (
    <p
      className={clsx("mt-1 text-sm text-red-600", className)}
      role="alert"
      {...props}
    />
  );
}
