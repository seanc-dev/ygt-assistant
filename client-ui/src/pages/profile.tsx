import Head from "next/head";
import { GetServerSideProps } from "next";
import { getServerSession } from "next-auth";
import { useSession } from "next-auth/react";
import { FormEvent, useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { authOptions } from "./api/auth/[...nextauth]";
import { NavBar } from "../components/NavBar";
import { Label } from "../components/Form/Label";
import { Field } from "../components/Form/Field";
import { Button } from "../components/Button";
import { TimezoneSelect } from "../components/TimezoneSelect";
import { api } from "../lib/api";
import { queryKeys } from "../lib/queryKeys";
import { UserProfile } from "../lib/types";

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

export default function ProfilePage() {
  const { status } = useSession();
  const queryClient = useQueryClient();
  const profileQuery = useQuery({
    queryKey: queryKeys.profile,
    queryFn: () => api.profile.get(),
    enabled: status === "authenticated",
  });

  const updateProfileMutation = useMutation({
    mutationFn: (patch: Partial<UserProfile>) => api.profile.update(patch),
    onSuccess: (updated) => {
      queryClient.setQueryData(queryKeys.profile, updated);
    },
  });

  const profile = profileQuery.data;
  const [formState, setFormState] = useState({
    name: "",
    email: "",
    timezone: "",
    notificationsEmail: true,
    notificationsPush: false,
    // New granular controls
    askFirst: true,
    proactiveness: "medium" as "low" | "medium" | "high",
    useOverallEmail: true,
    emailAskFirst: true,
    emailProactiveness: "medium" as "low" | "medium" | "high",
    useOverallCalendar: true,
    calendarAskFirst: true,
    calendarProactiveness: "medium" as "low" | "medium" | "high",
    useOverallNotion: true,
    notionAskFirst: true,
    notionProactiveness: "medium" as "low" | "medium" | "high",
  });

  useEffect(() => {
    if (!profile) return;
    setFormState({
      name: profile.name,
      email: profile.email,
      timezone: profile.timezone,
      notificationsEmail: profile.preferences.notificationsEmail,
      notificationsPush: profile.preferences.notificationsPush ?? false,
      askFirst: Boolean(profile.preferences.global?.askFirst ?? true),
      proactiveness: (profile.preferences.global?.proactiveness ?? "medium") as
        | "low"
        | "medium"
        | "high",
      useOverallEmail: !profile.preferences.domains?.email,
      emailAskFirst: Boolean(
        profile.preferences.domains?.email?.askFirst ?? true
      ),
      emailProactiveness: (profile.preferences.domains?.email?.proactiveness ??
        "medium") as "low" | "medium" | "high",
      useOverallCalendar: !profile.preferences.domains?.calendar,
      calendarAskFirst: Boolean(
        profile.preferences.domains?.calendar?.askFirst ?? true
      ),
      calendarProactiveness: (profile.preferences.domains?.calendar
        ?.proactiveness ?? "medium") as "low" | "medium" | "high",
      useOverallNotion: !profile.preferences.domains?.notion,
      notionAskFirst: Boolean(
        profile.preferences.domains?.notion?.askFirst ?? true
      ),
      notionProactiveness: (profile.preferences.domains?.notion
        ?.proactiveness ?? "medium") as "low" | "medium" | "high",
    });
  }, [profile]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    await updateProfileMutation.mutateAsync({
      name: formState.name,
      timezone: formState.timezone,
      preferences: {
        notificationsEmail: formState.notificationsEmail,
        notificationsPush: formState.notificationsPush,
        global: {
          askFirst: formState.askFirst,
          proactiveness: formState.proactiveness,
        },
        domains: {
          email: formState.useOverallEmail
            ? undefined
            : {
                askFirst: formState.emailAskFirst,
                proactiveness: formState.emailProactiveness,
              },
          calendar: formState.useOverallCalendar
            ? undefined
            : {
                askFirst: formState.calendarAskFirst,
                proactiveness: formState.calendarProactiveness,
              },
          notion: formState.useOverallNotion
            ? undefined
            : {
                askFirst: formState.notionAskFirst,
                proactiveness: formState.notionProactiveness,
              },
        },
      },
    });
  };

  return (
    <>
      <Head>
        <title>Profile</title>
      </Head>
      <div className="min-h-screen bg-slate-50">
        <NavBar />
        <main className="mx-auto max-w-4xl px-4 py-8 sm:px-6">
          <h1 className="text-2xl font-semibold text-slate-900">Profile</h1>
          <p className="mt-1 text-sm text-slate-600">
            Update your details and manage integrations.
          </p>

          {!profile ? (
            <p className="mt-6 text-sm text-slate-600">Loading profile…</p>
          ) : (
            <form className="mt-6 space-y-6" onSubmit={handleSubmit}>
              <section className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
                <h2 className="text-lg font-semibold text-slate-900">
                  Contact
                </h2>
                <div className="mt-4 grid gap-4 sm:grid-cols-2">
                  <div>
                    <Label htmlFor="profile-name">Name</Label>
                    <Field
                      id="profile-name"
                      value={formState.name}
                      onChange={(event) =>
                        setFormState((state) => ({
                          ...state,
                          name: event.target.value,
                        }))
                      }
                      required
                    />
                  </div>
                  <div>
                    <Label htmlFor="profile-email">Email</Label>
                    <Field
                      id="profile-email"
                      value={formState.email}
                      readOnly
                      disabled
                      className="bg-slate-100"
                    />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <Label htmlFor="profile-timezone">Timezone</Label>
                      <span
                        className="inline-flex h-5 w-5 items-center justify-center rounded-full text-slate-400 hover:text-slate-600"
                        title="Used to schedule emails, events, reminders, and nudges in your local time. We interpret and generate times based on this timezone."
                        aria-label="Timezone usage information"
                      >
                        <svg
                          viewBox="0 0 20 20"
                          fill="currentColor"
                          className="h-4 w-4"
                          aria-hidden="true"
                        >
                          <path
                            fillRule="evenodd"
                            d="M10 18a8 8 0 100-16 8 8 0 000 16zm-.75-9.5a.75.75 0 011.5 0v5a.75.75 0 01-1.5 0v-5zM10 6a1 1 0 100 2 1 1 0 000-2z"
                            clipRule="evenodd"
                          />
                        </svg>
                      </span>
                    </div>
                    <TimezoneSelect
                      id="profile-timezone"
                      value={formState.timezone}
                      onChange={(value) =>
                        setFormState((state) => ({
                          ...state,
                          timezone: value,
                        }))
                      }
                    />
                  </div>
                </div>
              </section>

              <section className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
                <h2 className="text-lg font-semibold text-slate-900">
                  Preferences
                </h2>
                <div className="mt-4 space-y-4">
                  <label className="flex items-start gap-3">
                    <input
                      type="checkbox"
                      className="mt-1 h-4 w-4 rounded border-slate-300 text-primary-600 focus:ring-primary-500"
                      checked={formState.notificationsEmail}
                      onChange={(event) =>
                        setFormState((state) => ({
                          ...state,
                          notificationsEmail: event.target.checked,
                        }))
                      }
                    />
                    <span className="text-sm text-slate-700">
                      Email notifications
                    </span>
                  </label>
                  <label className="flex items-start gap-3">
                    <input
                      type="checkbox"
                      className="mt-1 h-4 w-4 rounded border-slate-300 text-primary-600 focus:ring-primary-500"
                      checked={formState.notificationsPush}
                      onChange={(event) =>
                        setFormState((state) => ({
                          ...state,
                          notificationsPush: event.target.checked,
                        }))
                      }
                    />
                    <span className="text-sm text-slate-700">
                      Push notifications
                    </span>
                  </label>
                  <div className="space-y-4">
                    <div className="grid gap-3 sm:grid-cols-2">
                      <label className="flex items-center gap-3">
                        <input
                          type="checkbox"
                          className="h-4 w-4 rounded border-slate-300 text-primary-600 focus:ring-primary-500"
                          checked={formState.askFirst}
                          onChange={(e) =>
                            setFormState((s) => ({
                              ...s,
                              askFirst: e.target.checked,
                            }))
                          }
                        />
                        <span className="text-sm text-slate-700">
                          Ask first (overall)
                        </span>
                      </label>
                      <div>
                        <div className="flex items-center gap-2">
                          <Label htmlFor="overall-proactiveness">
                            Proactiveness (overall)
                          </Label>
                          <span
                            className="inline-flex h-5 w-5 items-center justify-center rounded-full text-slate-400 hover:text-slate-600"
                            title="How proactively CoachFlow suggests/acts. Low = conservative, Medium = balanced, High = more proactive."
                            aria-label="Proactiveness information"
                          >
                            <svg
                              viewBox="0 0 20 20"
                              fill="currentColor"
                              className="h-4 w-4"
                              aria-hidden="true"
                            >
                              <path
                                fillRule="evenodd"
                                d="M10 18a8 8 0 100-16 8 8 0 000 16zm-.75-9.5a.75.75 0 011.5 0v5a.75.75 0 01-1.5 0v-5zM10 6a1 1 0 100 2 1 1 0 000-2z"
                                clipRule="evenodd"
                              />
                            </svg>
                          </span>
                        </div>
                        <select
                          id="overall-proactiveness"
                          className="focus-outline mt-1 block w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm"
                          value={formState.proactiveness}
                          onChange={(e) =>
                            setFormState((s) => ({
                              ...s,
                              proactiveness: e.target.value as
                                | "low"
                                | "medium"
                                | "high",
                            }))
                          }
                        >
                          <option value="low">Low</option>
                          <option value="medium">Medium</option>
                          <option value="high">High</option>
                        </select>
                      </div>
                    </div>

                    <details className="rounded border border-slate-200 p-3">
                      <summary className="cursor-pointer text-sm font-medium text-slate-800">
                        Customize by app
                      </summary>
                      <div className="mt-3 grid gap-4 sm:grid-cols-3">
                        {/* Email */}
                        <div className="rounded border border-slate-200 p-3">
                          <div className="text-sm font-medium">Email</div>
                          <label className="mt-2 flex items-center gap-2 text-sm">
                            <input
                              type="checkbox"
                              checked={formState.useOverallEmail}
                              onChange={(e) =>
                                setFormState((s) => ({
                                  ...s,
                                  useOverallEmail: e.target.checked,
                                }))
                              }
                            />
                            Use overall settings
                          </label>
                          {!formState.useOverallEmail && (
                            <div className="mt-2 space-y-2">
                              <label className="flex items-center gap-2 text-sm">
                                <input
                                  type="checkbox"
                                  checked={formState.emailAskFirst}
                                  onChange={(e) =>
                                    setFormState((s) => ({
                                      ...s,
                                      emailAskFirst: e.target.checked,
                                    }))
                                  }
                                />
                                Ask first
                              </label>
                              <select
                                className="focus-outline block w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm"
                                value={formState.emailProactiveness}
                                onChange={(e) =>
                                  setFormState((s) => ({
                                    ...s,
                                    emailProactiveness: e.target.value as
                                      | "low"
                                      | "medium"
                                      | "high",
                                  }))
                                }
                              >
                                <option value="low">Low</option>
                                <option value="medium">Medium</option>
                                <option value="high">High</option>
                              </select>
                            </div>
                          )}
                        </div>
                        {/* Calendar */}
                        <div className="rounded border border-slate-200 p-3">
                          <div className="text-sm font-medium">Calendar</div>
                          <label className="mt-2 flex items-center gap-2 text-sm">
                            <input
                              type="checkbox"
                              checked={formState.useOverallCalendar}
                              onChange={(e) =>
                                setFormState((s) => ({
                                  ...s,
                                  useOverallCalendar: e.target.checked,
                                }))
                              }
                            />
                            Use overall settings
                          </label>
                          {!formState.useOverallCalendar && (
                            <div className="mt-2 space-y-2">
                              <label className="flex items-center gap-2 text-sm">
                                <input
                                  type="checkbox"
                                  checked={formState.calendarAskFirst}
                                  onChange={(e) =>
                                    setFormState((s) => ({
                                      ...s,
                                      calendarAskFirst: e.target.checked,
                                    }))
                                  }
                                />
                                Ask first
                              </label>
                              <select
                                className="focus-outline block w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm"
                                value={formState.calendarProactiveness}
                                onChange={(e) =>
                                  setFormState((s) => ({
                                    ...s,
                                    calendarProactiveness: e.target.value as
                                      | "low"
                                      | "medium"
                                      | "high",
                                  }))
                                }
                              >
                                <option value="low">Low</option>
                                <option value="medium">Medium</option>
                                <option value="high">High</option>
                              </select>
                            </div>
                          )}
                        </div>
                        {/* Notion */}
                        <div className="rounded border border-slate-200 p-3">
                          <div className="text-sm font-medium">Notion</div>
                          <label className="mt-2 flex items-center gap-2 text-sm">
                            <input
                              type="checkbox"
                              checked={formState.useOverallNotion}
                              onChange={(e) =>
                                setFormState((s) => ({
                                  ...s,
                                  useOverallNotion: e.target.checked,
                                }))
                              }
                            />
                            Use overall settings
                          </label>
                          {!formState.useOverallNotion && (
                            <div className="mt-2 space-y-2">
                              <label className="flex items-center gap-2 text-sm">
                                <input
                                  type="checkbox"
                                  checked={formState.notionAskFirst}
                                  onChange={(e) =>
                                    setFormState((s) => ({
                                      ...s,
                                      notionAskFirst: e.target.checked,
                                    }))
                                  }
                                />
                                Ask first
                              </label>
                              <select
                                className="focus-outline block w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm"
                                value={formState.notionProactiveness}
                                onChange={(e) =>
                                  setFormState((s) => ({
                                    ...s,
                                    notionProactiveness: e.target.value as
                                      | "low"
                                      | "medium"
                                      | "high",
                                  }))
                                }
                              >
                                <option value="low">Low</option>
                                <option value="medium">Medium</option>
                                <option value="high">High</option>
                              </select>
                            </div>
                          )}
                        </div>
                      </div>
                    </details>
                  </div>
                </div>
              </section>

              <div className="flex justify-end">
                <Button
                  type="submit"
                  disabled={updateProfileMutation.isPending}
                >
                  {updateProfileMutation.isPending ? "Saving…" : "Save changes"}
                </Button>
              </div>
            </form>
          )}
        </main>
      </div>
    </>
  );
}
