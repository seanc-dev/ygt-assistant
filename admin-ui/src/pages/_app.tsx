import type { AppProps } from "next/app";
import "../styles/globals.css";
import { ThemeProvider, ThemeScript } from "@coachflow/ui";

export default function App({ Component, pageProps }: AppProps) {
  return (
    <ThemeProvider>
      <ThemeScript />
      <Component {...pageProps} />
    </ThemeProvider>
  );
}
