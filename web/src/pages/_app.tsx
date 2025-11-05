import type { AppProps } from "next/app";
import "../styles/globals.css";
import { ThemeProvider, ThemeScript } from "@lucid-work/ui";

export default function App({ Component, pageProps }: AppProps) {
  return (
    <ThemeProvider>
      <ThemeScript />
      <Component {...pageProps} />
    </ThemeProvider>
  );
}
