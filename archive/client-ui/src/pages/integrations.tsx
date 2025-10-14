import Head from "next/head";
import { GetServerSideProps } from "next";
import { getServerSession } from "next-auth";
import { useSession } from "next-auth/react";
import { useQuery } from "@tanstack/react-query";
import { authOptions } from "./api/auth/[...nextauth]";
import { NavBar } from "../components/NavBar";
import { Button } from "../components/Button";
import { api } from "../lib/api";
import { queryKeys } from "../lib/queryKeys";
import { Integration } from "../lib/types";

export const getServerSideProps: GetServerSideProps = async (context) => {
  if (process.env.RUN_E2E === "true") {
    return { props: {} };
  }
  const session = await getServerSession(context.req, context.res, authOptions);
  if (!session) {
    return {
      redirect: {
        destination: "/login",
        permanent: false,
      },
    };
  }
  return { props: {} };
};

const integrationMeta: Record<
  string,
  { name: string; description: string; initial: string }
> = {
  nylas: {
    name: "Nylas",
    description: "Sync availability from your email and calendar accounts.",
    initial: "N",
  },
  notion: {
    name: "Notion",
    description: "Publish notes and recaps directly to your workspace.",
    initial: "N",
  },
  google: {
    name: "Google",
    description: "Connect Gmail and Google Calendar to automate workflows.",
    initial: "G",
  },
};

function getIntegrationMeta(provider: string) {
  const fallbackInitial = provider.charAt(0).toUpperCase();
  return (
    integrationMeta[provider] ?? {
      name: provider.charAt(0).toUpperCase() + provider.slice(1),
      description: "Connect this service to keep CoachFlow up to date.",
      initial: fallbackInitial,
    }
  );
}

interface SummaryCardProps {
  label: string;
  value: number;
  description: string;
  isLoading?: boolean;
}

function SummaryCard({ label, value, description, isLoading }: SummaryCardProps) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <p className="text-sm font-medium text-slate-600">{label}</p>
      {isLoading ? (
        <div className="mt-2 h-7 w-16 animate-pulse rounded bg-slate-200" />
      ) : (
        <p className="mt-2 text-2xl font-semibold text-slate-900">{value}</p>
      )}
      <p className="mt-2 text-sm text-slate-600">{description}</p>
    </div>
  );
}

interface IntegrationListSectionProps {
  title: string;
  description: string;
  integrations: Integration[];
  emptyTitle: string;
  emptyDescription: string;
  onConnect: (provider: string) => void;
  isLoading: boolean;
}

function IntegrationListSection({
  title,
  description,
  integrations,
  emptyTitle,
  emptyDescription,
  onConnect,
  isLoading,
}: IntegrationListSectionProps) {
  return (
    <section className="mt-10">
      <div>
        <h2 className="text-lg font-semibold text-slate-900">{title}</h2>
        <p className="mt-1 text-sm text-slate-600">{description}</p>
      </div>

      {isLoading ? (
        <div className="mt-4 space-y-3">
          {[0, 1].map((item) => (
            <div
              key={item}
              className="h-28 animate-pulse rounded-xl border border-slate-200 bg-white"
            />
          ))}
        </div>
      ) : integrations.length === 0 ? (
        <div className="mt-4 rounded-xl border border-dashed border-slate-300 bg-slate-50 px-4 py-6 text-center">
          <p className="text-sm font-semibold text-slate-900">{emptyTitle}</p>
          <p className="mt-1 text-sm text-slate-600">{emptyDescription}</p>
        </div>
      ) : (
        <ul className="mt-4 space-y-3" role="list">
          {integrations.map((integration) => (
            <IntegrationListItem
              key={integration.provider}
              integration={integration}
              onConnect={onConnect}
            />
          ))}
        </ul>
      )}
    </section>
  );
}

interface IntegrationListItemProps {
  integration: Integration;
  onConnect: (provider: string) => void;
}

function IntegrationListItem({ integration, onConnect }: IntegrationListItemProps) {
  const { provider, status } = integration;
  const meta = getIntegrationMeta(provider);
  const isConnected = status === "connected";

  return (
    <li className="flex flex-col gap-4 rounded-xl border border-slate-200 bg-white p-4 shadow-sm sm:flex-row sm:items-center sm:justify-between">
      <div>
        <div className="flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-slate-100 text-base font-semibold text-slate-600">
            {meta.initial}
          </div>
          <div>
            <h3 className="text-base font-semibold text-slate-900">{meta.name}</h3>
            <p className="mt-1 max-w-xl text-sm text-slate-600">
              {meta.description}
            </p>
          </div>
        </div>
        <div className="mt-3 flex items-center gap-2 text-sm text-slate-600">
          <span
            className={`inline-flex h-2.5 w-2.5 rounded-full ${
              isConnected ? "bg-emerald-500" : "bg-slate-300"
            }`}
            aria-hidden="true"
          />
          <span className="font-medium text-slate-700">
            {isConnected ? "Connected" : "Not connected"}
          </span>
        </div>
      </div>
      <div className="sm:flex sm:flex-col sm:items-end">
        <Button
          type="button"
          variant={isConnected ? "secondary" : "primary"}
          onClick={() => onConnect(provider)}
        >
          {isConnected ? "Reconnect" : "Connect"}
        </Button>
      </div>
    </li>
  );
}

export default function IntegrationsPage() {
  const { status } = useSession();
  const profileQuery = useQuery({
    queryKey: queryKeys.profile,
    queryFn: () => api.profile.get(),
    enabled: status === "authenticated",
  });

  const integrations = profileQuery.data?.integrations ?? [];
  const isLoading = status !== "authenticated" || profileQuery.isPending;
  const connectedIntegrations = integrations.filter(
    (integration) => integration.status === "connected"
  );
  const readyToConnect = integrations.filter(
    (integration) => integration.status !== "connected"
  );

  const handleConnect = (provider: string) => {
    window.location.href = `/api/integrations/${provider}/connect`;
  };

  return (
    <>
      <Head>
        <title>Integrations</title>
      </Head>
      <div className="min-h-screen bg-slate-50">
        <NavBar />
        <main className="mx-auto max-w-5xl px-4 py-10 sm:px-6 lg:px-8">
          <header>
            <h1 className="text-3xl font-semibold text-slate-900">Integrations</h1>
            <p className="mt-2 max-w-2xl text-sm text-slate-600">
              Manage the tools that keep CoachFlow in sync. Connect new services
              or review existing connections without leaving this page.
            </p>
          </header>

          <section className="mt-8 grid gap-4 md:grid-cols-3">
            <SummaryCard
              label="Total integrations"
              value={integrations.length}
              description="Available to your workspace."
              isLoading={isLoading}
            />
            <SummaryCard
              label="Connected"
              value={connectedIntegrations.length}
              description="Currently syncing with CoachFlow."
              isLoading={isLoading}
            />
            <SummaryCard
              label="Ready to set up"
              value={readyToConnect.length}
              description="Connect these services to unlock automations."
              isLoading={isLoading}
            />
          </section>

          <IntegrationListSection
            title="Connected integrations"
            description="These services are actively sharing data with CoachFlow."
            integrations={connectedIntegrations}
            emptyTitle="No integrations connected yet"
            emptyDescription="Connect a service below to start syncing data."
            onConnect={handleConnect}
            isLoading={isLoading}
          />

          <IntegrationListSection
            title="Available to connect"
            description="Bring CoachFlow to the rest of your workflow in just a few clicks."
            integrations={readyToConnect}
            emptyTitle="You're fully connected"
            emptyDescription="All available integrations are connected right now."
            onConnect={handleConnect}
            isLoading={isLoading}
          />
        </main>
      </div>
    </>
  );
}
