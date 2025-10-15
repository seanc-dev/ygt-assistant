import { useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Action } from "../lib/types";
import { queryKeys } from "../lib/queryKeys";

interface ActionEventPayload {
  action: Action;
  event: "pending" | "updated" | "deleted";
}

export function useActionStream(enabled: boolean) {
  const queryClient = useQueryClient();

  useEffect(() => {
    if (!enabled) return;
    const prefix = process.env.NEXT_PUBLIC_API_BASE_URL ?? "";
    const devToken =
      typeof window !== "undefined"
        ? window.localStorage.getItem("cf_dev_session_token")
        : null;
    const qs = devToken ? `?token=${encodeURIComponent(devToken)}` : "";
    const url = `${prefix.replace(/\/$/, "")}/api/actions/stream${qs}`;
    const eventSource = new EventSource(url, { withCredentials: true });

    eventSource.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data) as ActionEventPayload;
        if (!payload?.action) return;
        if (payload.event === "pending") {
          queryClient.setQueriesData(
            { queryKey: ["actions"] },
            (existing: Action[] | undefined) => {
              if (!existing) {
                return [payload.action];
              }
              const index = existing.findIndex(
                (item) => item.id === payload.action.id
              );
              if (index >= 0) {
                const copy = existing.slice();
                copy[index] = payload.action;
                return copy;
              }
              return [payload.action, ...existing];
            }
          );
        }
        if (payload.event === "updated") {
          queryClient.setQueriesData(
            { queryKey: ["actions"] },
            (existing: Action[] | undefined) => {
              if (!existing) return existing;
              const index = existing.findIndex(
                (item) => item.id === payload.action.id
              );
              if (index >= 0) {
                const copy = existing.slice();
                copy[index] = payload.action;
                return copy;
              }
              return existing;
            }
          );
        }
        if (payload.event === "deleted") {
          queryClient.setQueriesData(
            { queryKey: ["actions"] },
            (existing: Action[] | undefined) => {
              if (!existing) return existing;
              return existing.filter((item) => item.id !== payload.action.id);
            }
          );
        }
        queryClient.setQueryData(
          queryKeys.action(payload.action.id),
          payload.action
        );
      } catch (error) {
        console.error("Failed to parse action stream payload", error);
      }
    };

    eventSource.onerror = () => {
      eventSource.close();
    };

    return () => {
      eventSource.close();
    };
  }, [enabled, queryClient]);
}
