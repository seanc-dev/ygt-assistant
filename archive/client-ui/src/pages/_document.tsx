import { Html, Head, Main, NextScript } from "next/document";
import { ThemeScript } from "@coachflow/ui";

export default function Document() {
  return (
    <Html lang="en">
      <Head />
      <body className="min-h-screen antialiased">
        <ThemeScript />
        <Main />
        <NextScript />
      </body>
    </Html>
  );
}
