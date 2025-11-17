import type { AppProps } from "next/app";
import "../styles/globals.css";
import "../styles/theme.css";
import { ThemeProvider, ThemeScript } from "@ygt-assistant/ui";

export default function App({ Component, pageProps }: AppProps) {
  return (
    <div className="h-[100svh] md:h-screen flex flex-col overflow-hidden bg-[var(--lw-base)] text-[var(--lw-neutral-text)]">
    <ThemeProvider>
      <ThemeScript />
        <main className="flex-1 min-h-0 flex flex-col">
      <Component {...pageProps} />
        </main>
    </ThemeProvider>
    </div>
  );
}
