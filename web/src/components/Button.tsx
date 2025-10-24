import {
  Button as PrimitiveButton,
  type ButtonProps as PrimitiveButtonProps,
} from "@ygt-assistant/ui";

export type ButtonProps = PrimitiveButtonProps;

export function Button(props: ButtonProps) {
  return <PrimitiveButton {...props} />;
}
