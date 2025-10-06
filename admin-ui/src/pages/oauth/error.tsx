import Head from "next/head";
import Link from "next/link";
import { useRouter } from "next/router";
import { Button } from "../../components/Button";
import { Badge } from "../../components/Badge";

export default function OAuthError() {
  const router = useRouter();
  const { reason } = router.query as { reason?: string };

  const closeWindow = () => {
    if (typeof window !== "undefined") window.close();
  };

  return (
    <>
      <Head>
        <title>Connection failed</title>
      </Head>
      <main className="flex min-h-screen items-center justify-center bg-slate-50 px-4 py-12">
        <div className="w-full max-w-lg space-y-4 rounded-lg border border-slate-200 bg-white p-6 text-center shadow-lg">
          <div className="flex items-center justify-center gap-2">
            <h1 className="text-2xl font-semibold text-slate-900">We couldn’t complete the connection</h1>
            <Badge tone="danger" className="text-sm">⚠️</Badge>
          </div>
          <p className="text-sm text-red-600">
            {reason ? `Reason: ${reason}` : "An unknown error occurred."}
          </p>
          <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
            <Button onClick={closeWindow} className="min-w-[140px]" variant="secondary">
              Close window
            </Button>
            <Link
              href="/"
              className="focus-outline inline-flex min-w-[140px] items-center justify-center rounded-md border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 shadow-sm transition hover:border-primary-300 hover:text-primary-700"
            >
              Return to admin
            </Link>
          </div>
        </div>
      </main>
    </>
  );
}
