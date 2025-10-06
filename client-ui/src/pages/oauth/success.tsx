import { useRouter } from "next/router";

export default function OAuthSuccess() {
  const r = useRouter();
  const { provider, email } = r.query as { provider?: string; email?: string };
  const goToApp = () => {
    if (typeof window !== "undefined") window.location.href = "/";
  };
  return (
    <div className="p-6 space-y-4">
      <h1 className="text-2xl font-semibold">You&apos;re all set ✅</h1>
      <p className="text-gray-700">
        {provider
          ? `${provider.charAt(0).toUpperCase()}${provider.slice(
              1
            )} account connected successfully.`
          : "Account connected successfully."}
      </p>
      {email ? (
        <p className="text-gray-600">Authorized account: {email}</p>
      ) : null}
      <div className="flex gap-3">
        <button
          className="bg-black text-white px-4 py-2 rounded"
          onClick={goToApp}
        >
          Go to app
        </button>
      </div>
    </div>
  );
}
