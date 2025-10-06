import Document, { Head, Html, Main, NextScript } from "next/document";
import { ThemeScript } from "@coachflow/ui";

export default class MyDocument extends Document {
  render() {
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
}
