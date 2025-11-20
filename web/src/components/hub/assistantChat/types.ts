import type { InteractiveSurface } from "../../../lib/llm/surfaces";

export type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  ts: string;
  optimistic?: boolean;
  error?: boolean;
  retryable?: boolean;
  errorMessage?: string;
  embeds?: any[];
  surfaces?: InteractiveSurface[];
};

export type MessageView = {
  id: string;
  role: "user" | "assistant";
  content: string;
  embeds?: any[];
  surfaces?: InteractiveSurface[];
  marginTop: string;
  timestampLabel: string;
  showTimestamp: boolean;
  shouldAnimate: boolean;
  startDelayMs?: number;
  error?: boolean;
  retryable?: boolean;
  errorMessage?: string;
};

export type ParsedTokenChip = {
  raw: string;
  kind: "ref" | "op";
  label: string;
  start: number;
  end: number;
  data?: Record<string, string>;
};

export type TokenSegment =
  | { type: "text"; text: string }
  | { type: "token"; token: ParsedTokenChip };

export type ThreadResponse = {
  ok: boolean;
  thread: {
    id: string;
    messages: Message[];
  };
};

export type ProjectOption = {
  id: string;
  title: string;
};

export type TaskOption = {
  id: string;
  title: string;
  projectId?: string | null;
  projectTitle?: string | null;
};

export type TaskSuggestion = TaskOption & {
  meta?: string;
  isSuggested?: boolean;
};

