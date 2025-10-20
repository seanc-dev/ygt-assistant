import type { AppProps } from "next/app";
import "../styles/globals.css";
import { ThemeProvider, ThemeScript } from "@ygt-assistant/ui";

export default function App({ Component, pageProps }: AppProps) {
  return (
    <ThemeProvider>
      <ThemeScript />
      <Component {...pageProps} />
    </ThemeProvider>
  );
}
