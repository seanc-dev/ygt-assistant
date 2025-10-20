import { Layout } from "../../components/Layout";
import { Card } from "../../components/Card";

export default function ConnectionsPage() {
  const tiles = [
    {
      key: "msft",
      title: "Microsoft",
      desc: "Mail and Calendar via Microsoft Graph.",
      cta: "Connect",
    },
  ];
  return (
    <Layout>
      <h1 className="mb-4 text-2xl font-semibold">Connections</h1>
      <div className="grid gap-3 md:grid-cols-3">
        {tiles.map((t) => (
          <Card
            key={t.key}
            title={t.title}
            subtitle={t.desc}
            actions={
              <div className="flex gap-2">
                <a
                  href={`${
                    process.env.NEXT_PUBLIC_ADMIN_API_BASE ||
                    "http://localhost:8000"
                  }/connections/ms/oauth/start?user_id=local-user`}
                  className="rounded bg-slate-900 px-3 py-1 text-sm text-white dark:bg-slate-100 dark:text-slate-900"
                >
                  {t.cta}
                </a>
                <button
                  onClick={async () => {
                    const res = await fetch(
                      `${
                        process.env.NEXT_PUBLIC_ADMIN_API_BASE ||
                        "http://localhost:8000"
                      }/connections/ms/test?user_id=local-user`,
                      { method: "POST" }
                    );
                    const data = await res.json();
                    alert(data.ok ? "OK" : "Failed");
                  }}
                  className="rounded border px-3 py-1 text-sm"
                >
                  Test
                </button>
              </div>
            }
          />
        ))}
      </div>
    </Layout>
  );
}
