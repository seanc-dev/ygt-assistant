import { Layout } from "../../components/Layout";
import { Card } from "../../components/Card";

export default function ConnectionsPage() {
  const tiles = [
    {
      key: "gmail",
      title: "Gmail",
      desc: "Draft and send emails.",
      cta: "Test",
    },
    {
      key: "calendar",
      title: "Calendar",
      desc: "Plan today and reschedule.",
      cta: "Test",
    },
    {
      key: "whatsapp",
      title: "WhatsApp",
      desc: "Send cards and replies.",
      cta: "Test",
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
              <button className="rounded bg-slate-900 px-3 py-1 text-sm text-white dark:bg-slate-100 dark:text-slate-900">
                {t.cta}
              </button>
            }
          />
        ))}
      </div>
    </Layout>
  );
}
