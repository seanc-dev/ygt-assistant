import {
  Button as PrimitiveButton,
  type ButtonProps as PrimitiveButtonProps,
} from "@lucid-work/ui";

export type ButtonProps = PrimitiveButtonProps;

export function Button(props: ButtonProps) {
  return <PrimitiveButton {...props} />;
}
