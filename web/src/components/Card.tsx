import { ReactNode } from "react";
import { Panel, type PanelProps } from "@lucid-work/ui";

type CardProps = PanelProps & {
  children?: ReactNode;
};

export function Card({ children, ...panelProps }: CardProps) {
  return <Panel {...panelProps}>{children}</Panel>;
}
