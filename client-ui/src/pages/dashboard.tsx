import { useEffect, useMemo, useRef, useState } from "react";
import Head from "next/head";
import { getServerSession } from "next-auth";
import { GetServerSideProps } from "next";
import { useSession } from "next-auth/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { authOptions } from "./api/auth/[...nextauth]";
import { NavBar } from "../components/NavBar";
import { ActionRow } from "../components/ActionRow";
import { ActionDetailsModal } from "../components/ActionDetailsModal";
import { Button } from "../components/Button";
import { Label } from "../components/Form/Label";
import { Field } from "../components/Form/Field";
import { Toast } from "../components/Toast";
import { useActionStream } from "../hooks/useActionStream";
import { ChangePasswordModal } from "../components/ChangePasswordModal";
import { api } from "../lib/api";
import { queryKeys } from "../lib/queryKeys";
import { Action, ActionType } from "../lib/types";
import {
  getSavedViewTags,
  hasMeetingToday,
  isActionOverdue,
  isClientRelated,
  isFinanceRelated,
} from "../lib/actionUtils";

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

export default function DashboardPage() {
  const { status } = useSession();
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState<ActionType | "all">("all");
  const [fromDate, setFromDate] = useState<string>("");
  const [toDate, setToDate] = useState<string>("");
  const [selectedAction, setSelectedAction] = useState<Action | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const seenIds = useRef(new Set<string>());
  const [showChangePw, setShowChangePw] = useState(false);
  const [selectedActionIds, setSelectedActionIds] = useState<Set<string>>(new Set());
  const [snoozedUntil, setSnoozedUntil] = useState<Record<string, string>>({});
  const [activeSavedView, setActiveSavedView] = useState<string>("all");

  const filters = useMemo(
    () => ({
      status: "pending" as const,
      type: typeFilter === "all" ? undefined : typeFilter,
      search: search || undefined,
      from: fromDate || undefined,
      to: toDate || undefined,
    }),
    [fromDate, search, toDate, typeFilter]
  );

  const actionsQuery = useQuery({
    queryKey: queryKeys.actions(filters),
    queryFn: () => api.actions.list(filters),
    enabled: status === "authenticated",
  });

  useActionStream(status === "authenticated");

  useEffect(() => {
    if (status !== "authenticated") return;
    (async () => {
      try {
        const me = await api.profile.get();
        if ((me as unknown as { must_change_password?: boolean })?.must_change_password) setShowChangePw(true);
      } catch {}
    })();
  }, [status]);

  useEffect(() => {
    if (!actionsQuery.data) return;
    for (const action of actionsQuery.data) {
      if (!seenIds.current.has(action.id)) {
        setToastMessage(`New ${action.type} action: ${action.title}`);
        seenIds.current.add(action.id);
        break;
      }
    }
  }, [actionsQuery.data]);

  const acceptMutation = useMutation({
    mutationFn: ({ id, patch }: { id: string; patch?: Partial<Action> }) =>
      api.actions.accept(id, patch),
    onSuccess: (updated) => {
      queryClient.setQueryData(
        queryKeys.actions(filters),
        (existing?: Action[]) =>
          existing?.filter((action) => action.id !== updated.id) ?? []
      );
      queryClient.setQueryData(queryKeys.action(updated.id), updated);
      setSelectedActionIds((prev) => {
        if (!prev.has(updated.id)) return prev;
        const next = new Set(prev);
        next.delete(updated.id);
        return next;
      });
      setToastMessage(`Accepted ${updated.title}`);
    },
  });

  const declineMutation = useMutation({
    mutationFn: ({ id, reason }: { id: string; reason?: string }) =>
      api.actions.decline(id, reason),
    onSuccess: (updated) => {
      queryClient.setQueryData(
        queryKeys.actions(filters),
        (existing?: Action[]) =>
          existing?.filter((action) => action.id !== updated.id) ?? []
      );
      queryClient.setQueryData(queryKeys.action(updated.id), updated);
      setSelectedActionIds((prev) => {
        if (!prev.has(updated.id)) return prev;
        const next = new Set(prev);
        next.delete(updated.id);
        return next;
      });
      setToastMessage(`Declined ${updated.title}`);
    },
  });

  const handleAccept = (action: Action) => {
    const confirmed = window.confirm(
      "Accept this action? Nothing is sent without approval."
    );
    if (!confirmed) return;
    acceptMutation.mutate({ id: action.id });
  };

  const handleDecline = async (action: Action) => {
    const reason = window.prompt("Add a short note", "Not needed");
    if (reason === null) return;
    declineMutation.mutate({ id: action.id, reason });
  };

  const handleSaveAndAccept = async (patch: Partial<Action>) => {
    if (!selectedAction) return;
    await acceptMutation.mutateAsync({ id: selectedAction.id, patch });
  };

  const pendingActions = useMemo(() => actionsQuery.data ?? [], [actionsQuery.data]);
  const groupInfo = useMemo(() => {
    const buckets = new Map<string, Action[]>();
    for (const action of pendingActions) {
      const key = action.metadata?.autoGroupKey;
      if (!key) continue;
      const list = buckets.get(key) ?? [];
      list.push(action);
      buckets.set(key, list);
    }
    const map = new Map<string, { key: string; members: Action[] }>();
    for (const [key, members] of buckets) {
      if (members.length <= 1) continue;
      for (const member of members) {
        map.set(member.id, { key, members });
      }
    }
    return map;
  }, [pendingActions]);
  const savedViews = useMemo(
    () => [
      {
        id: "all",
        label: "All pending",
        filter: () => true,
      },
      {
        id: "overdue",
        label: "Overdue",
        filter: (action: Action) => isActionOverdue(action),
      },
      {
        id: "finance",
        label: "Finance",
        filter: (action: Action) => isFinanceRelated(action),
      },
      {
        id: "clients",
        label: "Clients",
        filter: (action: Action) => isClientRelated(action),
      },
      {
        id: "meetings-today",
        label: "Meetings today",
        filter: (action: Action) => hasMeetingToday(action),
      },
    ],
    []
  );

  const visibleActions = useMemo(() => {
    const now = Date.now();
    const snoozedIds = new Set(
      Object.entries(snoozedUntil)
        .filter(([, iso]) => {
          if (!iso) return false;
          const until = new Date(iso).getTime();
          return until > now;
        })
        .map(([id]) => id)
    );
    const activeView = savedViews.find((view) => view.id === activeSavedView) ?? savedViews[0];
    return pendingActions.filter((action) => {
      if (snoozedIds.has(action.id)) return false;
      if (!activeView.filter(action)) return false;
      if (activeSavedView === "clients") {
        const tags = getSavedViewTags(action);
        if (tags.includes("client")) return true;
      }
      return true;
    });
  }, [pendingActions, snoozedUntil, savedViews, activeSavedView]);

  const allSelected = visibleActions.length > 0 && visibleActions.every((action) => selectedActionIds.has(action.id));
  const hasSelection = selectedActionIds.size > 0;

  const clearSelection = () => setSelectedActionIds(new Set());

  const updateActionInCache = (id: string, patch: Partial<Action>) => {
    queryClient.setQueryData(queryKeys.actions(filters), (existing?: Action[]) => {
      if (!existing) return existing;
      return existing.map((item) => (item.id === id ? { ...item, ...patch } : item));
    });
    queryClient.setQueryData(queryKeys.action(id), (existing?: Action) =>
      existing ? { ...existing, ...patch } : existing
    );
  };

  const handleSelect = (action: Action, selected: boolean) => {
    setSelectedActionIds((prev) => {
      const next = new Set(prev);
      if (selected) {
        next.add(action.id);
      } else {
        next.delete(action.id);
      }
      return next;
    });
  };

  const handleSelectAll = (selected: boolean) => {
    if (!selected) {
      setSelectedActionIds(new Set());
      return;
    }
    setSelectedActionIds(new Set(visibleActions.map((action) => action.id)));
  };

  const parseDurationToMs = (token: string): number | undefined => {
    const match = token.trim().toLowerCase().match(/^(\d+)([hmdw])$/);
    if (!match) return undefined;
    const amount = Number.parseInt(match[1] ?? "0", 10);
    const unit = match[2];
    if (Number.isNaN(amount) || amount <= 0) return undefined;
    switch (unit) {
      case "m":
        return amount * 60 * 1000;
      case "h":
        return amount * 60 * 60 * 1000;
      case "d":
        return amount * 24 * 60 * 60 * 1000;
      case "w":
        return amount * 7 * 24 * 60 * 60 * 1000;
      default:
        return undefined;
    }
  };

  const handleSnooze = (action: Action, duration: string, options: { silent?: boolean } = {}) => {
    const ms = parseDurationToMs(duration) ?? 60 * 60 * 1000;
    const until = new Date(Date.now() + ms);
    setSnoozedUntil((prev) => ({ ...prev, [action.id]: until.toISOString() }));
    setSelectedActionIds((prev) => {
      if (!prev.has(action.id)) return prev;
      const next = new Set(prev);
      next.delete(action.id);
      return next;
    });
    if (!options.silent) {
      setToastMessage(`Snoozed "${action.title}" until ${until.toLocaleString()}`);
    }
  };

  const handleSelectGroup = (action: Action) => {
    const info = groupInfo.get(action.id);
    if (!info) return;
    setSelectedActionIds((prev) => {
      const next = new Set(prev);
      for (const member of info.members) {
        next.add(member.id);
      }
      return next;
    });
    setToastMessage(`Selected ${info.members.length} related actions`);
  };

  const handleSnoozeGroup = (action: Action, duration: string) => {
    const info = groupInfo.get(action.id);
    if (!info) {
      handleSnooze(action, duration);
      return;
    }
    const confirmed = window.confirm(
      `Snooze ${info.members.length} related actions for ${duration}?`
    );
    if (!confirmed) return;
    info.members.forEach((member, index) => {
      handleSnooze(member, duration, { silent: index !== info.members.length - 1 });
    });
    setToastMessage(`Snoozed ${info.members.length} related actions`);
  };

  const handleAddNote = (action: Action) => {
    const existingNotes = action.metadata?.quickNotes ?? [];
    const note = window.prompt("Add a note for your teammates", existingNotes.at(-1) ?? "");
    if (note === null) return;
    const trimmed = note.trim();
    if (!trimmed) return;
    const metadata = {
      ...(action.metadata ?? {}),
      quickNotes: [...existingNotes, trimmed],
    };
    updateActionInCache(action.id, { metadata });
    if (selectedAction?.id === action.id) {
      setSelectedAction({ ...selectedAction, metadata });
    }
    setToastMessage(`Added note to ${action.title}`);
  };

  const handleCreateTask = (action: Action) => {
    const description = window.prompt(
      "What task should we create from this?",
      action.metadata?.proposedNextStep?.label ?? action.title
    );
    if (description === null) return;
    const trimmed = description.trim();
    if (!trimmed) return;
    setToastMessage(`Task drafted: ${trimmed}`);
  };

  return (
    <>
      <Head>
        <title>Dashboard</title>
      </Head>
      <div className="min-h-screen bg-slate-50 dark:bg-slate-950">
        <ChangePasswordModal
          open={showChangePw}
          onClose={() => setShowChangePw(false)}
        />
        <NavBar />
        <main className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
          <div className="flex flex-col gap-4 rounded-lg border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
            <div className="flex flex-wrap items-end gap-4">
              <div className="flex-1 min-w-[200px]">
                <Label htmlFor="search">Search</Label>
                <Field
                  id="search"
                  placeholder="Search title or summary"
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                />
              </div>
              <div>
                <Label htmlFor="type-filter">Type</Label>
                <select
                  id="type-filter"
                  className="focus-outline mt-1 block rounded-md border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-900 dark:text-slate-100"
                  value={typeFilter}
                  onChange={(event) =>
                    setTypeFilter(event.target.value as ActionType | "all")
                  }
                >
                  <option value="all">All</option>
                  <option value="email">Email</option>
                  <option value="calendar">Calendar</option>
                  <option value="task">Task</option>
                  <option value="other">Other</option>
                </select>
              </div>
              <div>
                <Label htmlFor="from-date">From</Label>
                <Field
                  id="from-date"
                  type="date"
                  value={fromDate}
                  onChange={(event) => setFromDate(event.target.value)}
                />
              </div>
              <div>
                <Label htmlFor="to-date">To</Label>
                <Field
                  id="to-date"
                  type="date"
                  value={toDate}
                  onChange={(event) => setToDate(event.target.value)}
                />
              </div>
              <div>
                <Button
                  type="button"
                  variant="ghost"
                  onClick={() => {
                    setSearch("");
                    setTypeFilter("all");
                    setFromDate("");
                    setToDate("");
                  }}
                >
                  Clear filters
                </Button>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-2 rounded-md bg-slate-100/70 p-3 text-xs text-slate-600 dark:bg-slate-800/60 dark:text-slate-300">
              <span className="text-sm font-semibold text-slate-700 dark:text-slate-200">Saved views</span>
              {savedViews.map((view) => (
                <button
                  key={view.id}
                  type="button"
                  onClick={() => setActiveSavedView(view.id)}
                  className={
                    view.id === activeSavedView
                      ? "rounded-full bg-primary-600 px-3 py-1 text-xs font-semibold text-white"
                      : "rounded-full px-3 py-1 text-xs font-medium text-slate-600 transition hover:bg-white hover:text-slate-900 dark:text-slate-300 dark:hover:bg-slate-700"
                  }
                >
                  {view.label}
                </button>
              ))}
            </div>

            {hasSelection && (
              <div className="flex flex-wrap items-center justify-between gap-3 rounded-md border border-primary-200 bg-primary-50 p-3 text-sm dark:border-primary-500/30 dark:bg-primary-500/10">
                <div className="text-sm font-semibold text-primary-800 dark:text-primary-200">
                  {selectedActionIds.size} selected
                </div>
                <div className="flex flex-wrap gap-2">
                  <Button
                    variant="primary"
                    onClick={() => {
                      for (const id of selectedActionIds) {
                        const action = pendingActions.find((item) => item.id === id);
                        if (action) handleAccept(action);
                      }
                      clearSelection();
                    }}
                  >
                    Accept selected
                  </Button>
                  <Button
                    variant="secondary"
                    onClick={() => {
                      for (const id of selectedActionIds) {
                        const action = pendingActions.find((item) => item.id === id);
                        if (action) handleSnooze(action, "4h");
                      }
                      clearSelection();
                    }}
                  >
                    Snooze 4h
                  </Button>
                  <Button
                    variant="ghost"
                    onClick={() => {
                      for (const id of selectedActionIds) {
                        const action = pendingActions.find((item) => item.id === id);
                        if (action) handleDecline(action);
                      }
                      clearSelection();
                    }}
                  >
                    Decline selected
                  </Button>
                </div>
              </div>
            )}

            <div className="overflow-x-auto">
              <table
                className="min-w-full divide-y divide-slate-200 dark:divide-slate-700"
                role="grid"
              >
                <thead className="bg-slate-100 dark:bg-slate-800">
                  <tr>
                    <th scope="col" className="w-10 px-4 py-3">
                      <input
                        type="checkbox"
                        aria-label="Select all"
                        className="h-4 w-4 rounded border-slate-300 text-primary-600 focus:ring-primary-500 dark:border-slate-600 dark:bg-slate-900"
                        checked={allSelected}
                        onChange={(event) => handleSelectAll(event.target.checked)}
                      />
                    </th>
                    <th
                      scope="col"
                      className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-600 dark:text-slate-300"
                    >
                      Smart action card
                    </th>
                    <th
                      scope="col"
                      className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-600 dark:text-slate-300"
                    >
                      Created
                    </th>
                    <th
                      scope="col"
                      className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-600 dark:text-slate-300"
                    >
                      Due
                    </th>
                    <th
                      scope="col"
                      className="px-4 py-3"
                      aria-label="Actions"
                    />
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 bg-white dark:divide-slate-800 dark:bg-slate-900">
                  {visibleActions.length === 0 ? (
                    <tr>
                      <td
                        colSpan={5}
                        className="px-4 py-6 text-center text-sm text-slate-600 dark:text-slate-300"
                      >
                        {actionsQuery.isLoading
                          ? "Loading actions…"
                          : "Nothing needs your attention here. Try switching views or clearing snoozes."}
                      </td>
                    </tr>
                  ) : (
                    visibleActions.map((action) => (
                      <ActionRow
                        key={action.id}
                        action={action}
                        selected={selectedActionIds.has(action.id)}
                        onSelect={handleSelect}
                        onAccept={handleAccept}
                        onEdit={(value) => setSelectedAction(value)}
                        onDecline={handleDecline}
                        onSnooze={handleSnooze}
                        onAddNote={handleAddNote}
                        onCreateTask={handleCreateTask}
                        groupSize={groupInfo.get(action.id)?.members.length}
                        onSelectGroup={handleSelectGroup}
                        onSnoozeGroup={handleSnoozeGroup}
                      />
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </main>

        {toastMessage && (
          <div
            className="fixed bottom-4 right-4 z-50 flex flex-col items-end gap-2"
            aria-live="polite"
          >
            <Toast
              message={toastMessage}
              onDismiss={() => setToastMessage(null)}
            />
          </div>
        )}

        <ActionDetailsModal
          action={selectedAction}
          onClose={() => setSelectedAction(null)}
          onAccept={handleSaveAndAccept}
          onSnooze={handleSnooze}
          onDecline={handleDecline}
          onAddNote={handleAddNote}
          onCreateTask={handleCreateTask}
        />
      </div>
    </>
  );
}
