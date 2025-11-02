import { ReactNode } from "react";
import { Layout } from "./Layout";

export function AppShell({ children }: { children: ReactNode }) {
  return <Layout>{children}</Layout>;
}
