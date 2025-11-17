import Document, { Head, Html, Main, NextScript } from "next/document";
import { ThemeScript } from "@ygt-assistant/ui";

export default class MyDocument extends Document {
  render() {
    return (
      <Html lang="en">
        <Head />
        <body className="antialiased">
          <ThemeScript />
          <Main />
          <NextScript />
        </body>
      </Html>
    );
  }
}
