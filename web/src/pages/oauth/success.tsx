import Head from "next/head";
import Link from "next/link";
import { useRouter } from "next/router";
import { Button } from "../../components/Button";
import { Badge } from "../../components/Badge";

export default function OAuthSuccess() {
  const router = useRouter();
  const { provider, email } = router.query as {
    provider?: string;
    email?: string;
  };

  const closeWindow = () => {
    if (typeof window !== "undefined") window.close();
  };

  const providerName = provider
    ? `${provider.charAt(0).toUpperCase()}${provider.slice(1)}`
    : "Account";

  return (
    <>
      <Head>
        <title>Connection successful</title>
      </Head>
      <main className="flex min-h-screen items-center justify-center bg-slate-50 px-4 py-12">
        <div className="w-full max-w-lg space-y-4 rounded-lg border border-slate-200 bg-white p-6 text-center shadow-lg">
          <div className="flex items-center justify-center gap-2">
            <h1 className="text-2xl font-semibold text-slate-900">You’re all set</h1>
            <Badge tone="success" className="text-sm">✅</Badge>
          </div>
          <p className="text-sm text-slate-600">
            {providerName} connected successfully.
          </p>
          {email ? (
            <p className="text-sm text-slate-500">Authorized account: {email}</p>
          ) : null}
          <p className="text-sm text-slate-600">You can safely close this window.</p>
          <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
            <Button onClick={closeWindow} className="min-w-[140px]">
              Close window
            </Button>
            <a
              href={process.env.NEXT_PUBLIC_CLIENT_APP_URL || "https://app.ygt-assistant.com"}
              className="focus-outline inline-flex min-w-[140px] items-center justify-center rounded-md border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 shadow-sm transition hover:border-primary-300 hover:text-primary-700"
            >
              Go to app
            </a>
          </div>
        </div>
      </main>
    </>
  );
}
