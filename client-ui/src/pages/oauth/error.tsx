import Link from "next/link";
import { useRouter } from "next/router";

export default function OAuthError() {
  const r = useRouter();
  const { reason } = r.query as { reason?: string };
  return (
    <div className="p-6 space-y-4">
      <h1 className="text-2xl font-semibold">Connection failed</h1>
      <p className="text-gray-700">
        {reason || "We couldn't complete the connection."}
      </p>
      <Link className="underline" href="/">
        Go to app
      </Link>
    </div>
  );
}
