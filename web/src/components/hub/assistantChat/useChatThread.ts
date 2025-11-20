import { useEffect, useRef, useState } from "react";
import useSWR from "swr";
import { api } from "../../../lib/api";
import { parseInteractiveSurfaces } from "../../../lib/llm/surfaces";
import type { Message, ThreadResponse } from "./types";

type UseChatThreadOptions = {
  threadId: string | null;
  fetchThread?: (threadId: string) => Promise<ThreadResponse | null | undefined>;
};

const fingerprintContent = (content: string): string =>
  content.toLowerCase().trim().replace(/\s+/g, " ");

const defaultFetchThread = async (threadId: string) => {
  const response = await api.getThread(threadId);
  if (!response) {
    return {
      ok: true,
      thread: {
        id: threadId,
        messages: [],
      },
    };
  }
  return response as ThreadResponse;
};

export function useChatThread(options: UseChatThreadOptions) {
  const { threadId, fetchThread = defaultFetchThread } = options;
  const [messages, setMessages] = useState<Message[]>([]);
  const previousThreadDataRef = useRef<ThreadResponse | null>(null);

  const {
    data: threadData,
    mutate: mutateThreadRaw,
    isLoading: isLoadingThread,
  } = useSWR<ThreadResponse>(
    threadId ? ["thread", threadId] : null,
    async () => {
      if (!threadId) {
        throw new Error("No thread ID");
      }
      return (
        (await fetchThread(threadId)) ?? {
          ok: true,
          thread: {
            id: threadId,
            messages: [],
          },
        }
      );
    },
    {
      refreshInterval: threadId ? 5000 : 0,
      revalidateOnFocus: !!threadId,
      onError: (error: any) => {
        if (error?.status !== 404 && !error?.message?.includes("404")) {
          console.warn("SWR error fetching thread:", error);
        }
      },
    }
  );

  useEffect(() => {
    if (threadId) {
      setMessages([]);
    }
  }, [threadId]);

  useEffect(() => {
    if (!threadData?.thread?.messages || threadData.thread.id !== threadId) {
      previousThreadDataRef.current = null;
      return;
    }

    if (previousThreadDataRef.current === threadData) {
      return;
    }

    previousThreadDataRef.current = threadData;

    setMessages((prev) => {
      const backendMessages = threadData.thread.messages;
      const optimisticMessages = prev.filter((msg) => msg.optimistic);
      const confirmedIds = new Set(backendMessages.map((m: any) => m.id));

      const backendUserCounts = new Map<string, number>();
      backendMessages.forEach((msg: any) => {
        const content = msg.content || msg.text || "";
        if (msg.role === "user") {
          const fingerprint = fingerprintContent(content);
          backendUserCounts.set(
            fingerprint,
            (backendUserCounts.get(fingerprint) || 0) + 1
          );
        }
      });

      const optimisticUserBuckets = new Map<string, Message[]>();
      optimisticMessages.forEach((msg) => {
        if (msg.role === "user") {
          const fingerprint = fingerprintContent(msg.content);
          if (!optimisticUserBuckets.has(fingerprint)) {
            optimisticUserBuckets.set(fingerprint, []);
          }
          optimisticUserBuckets.get(fingerprint)!.push(msg);
        }
      });

      const matchedOptimisticIds = new Set<string>();
      optimisticUserBuckets.forEach((bucket, fingerprint) => {
        const backendCount = backendUserCounts.get(fingerprint) || 0;
        const sortedBucket = [...bucket].sort(
          (a, b) => new Date(a.ts).getTime() - new Date(b.ts).getTime()
        );
        for (
          let i = 0;
          i < Math.min(backendCount, sortedBucket.length);
          i++
        ) {
          matchedOptimisticIds.add(sortedBucket[i].id);
        }
      });

      const backendAssistantWithSurfaces = backendMessages.find(
        (msg: any) =>
          msg.role === "assistant" &&
          (msg.surfaces ||
            (msg.metadata?.surfaces && Array.isArray(msg.metadata.surfaces)))
      );

      const stillOptimistic = optimisticMessages.filter((msg) => {
        if (confirmedIds.has(msg.id)) {
          return false;
        }
        if (msg.role === "user" && matchedOptimisticIds.has(msg.id)) {
          return false;
        }
        if (
          msg.role === "assistant" &&
          msg.surfaces &&
          msg.surfaces.length > 0 &&
          backendAssistantWithSurfaces
        ) {
          return false;
        }
        return true;
      });

      const correctedBackendMessages = backendMessages.map((msg: any) => {
        const metadata =
          msg.metadata && typeof msg.metadata === "object" ? msg.metadata : {};
        const surfacesSource =
          msg.surfaces ??
          (Array.isArray(metadata?.surfaces)
            ? metadata.surfaces
            : metadata?.surfaces);
        const parsedSurfaces =
          msg.role === "assistant"
            ? parseInteractiveSurfaces(surfacesSource)
            : [];
        const normalizedMsg: Message = {
          id: msg.id || String(Math.random()),
          role: msg.role === "user" ? "user" : "assistant",
          content: msg.content || msg.text || "",
          ts: msg.ts || msg.created_at || new Date().toISOString(),
          embeds: msg.embeds || [],
          surfaces: parsedSurfaces.length ? parsedSurfaces : undefined,
        };

        const matchingOptimistic = optimisticMessages.find(
          (opt) =>
            fingerprintContent(opt.content) ===
              fingerprintContent(normalizedMsg.content) && opt.role === "user"
        );
        if (matchingOptimistic) {
          return { ...normalizedMsg, role: "user" as const };
        }
        return normalizedMsg;
      });

      const merged = [...correctedBackendMessages, ...stillOptimistic];
      return merged.sort(
        (a, b) => new Date(a.ts).getTime() - new Date(b.ts).getTime()
      );
    });
  }, [threadData, threadId]);

  return {
    messages,
    setMessages,
    threadData,
    mutateThreadRaw,
    isLoadingThread,
  };
}

