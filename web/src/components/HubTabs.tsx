import Link from "next/link";
import { useRouter } from "next/router";

const hubTabs = [
  { href: "/hub/queue", label: "Queue" },
  { href: "/hub/schedule", label: "Schedule" },
  { href: "/hub/brief", label: "Brief" },
];

export function HubTabs() {
  const router = useRouter();

  return (
    <div className="flex gap-2 border-b">
      {hubTabs.map((tab) => {
        const active = router.pathname === tab.href;
        return (
          <Link
            key={tab.href}
            href={tab.href}
            className={`px-4 py-2 text-sm ${
              active
                ? "border-b-2 border-blue-600 font-medium"
                : "text-gray-600 hover:text-gray-900"
            }`}
          >
            {tab.label}
          </Link>
        );
      })}
    </div>
  );
}

