import { ReactNode } from "react";
import { Panel, type PanelProps } from "@ygt-assistant/ui";

type CardProps = PanelProps & {
  children?: ReactNode;
};

export function Card({ children, ...panelProps }: CardProps) {
  return <Panel {...panelProps}>{children}</Panel>;
}
