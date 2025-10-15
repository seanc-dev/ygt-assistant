import type { AppProps } from "next/app";
import type { Session } from "next-auth";
import type { DehydratedState } from "@tanstack/react-query";
import { useState } from "react";
import { QueryClient, QueryClientProvider, HydrationBoundary } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { SessionProvider } from "next-auth/react";
import { ThemeProvider } from "@coachflow/ui";
import "../styles/globals.css";

type PageProps = AppProps["pageProps"] & {
  session?: Session;
  dehydratedState?: DehydratedState;
};

export default function App({ Component, pageProps }: AppProps<PageProps>) {
  const [queryClient] = useState(() => new QueryClient());

  return (
    <SessionProvider session={pageProps.session}>
      <ThemeProvider>
        <QueryClientProvider client={queryClient}>
          <HydrationBoundary state={pageProps.dehydratedState}>
            <Component {...pageProps} />
          </HydrationBoundary>
          <ReactQueryDevtools initialIsOpen={false} />
        </QueryClientProvider>
      </ThemeProvider>
    </SessionProvider>
  );
}
