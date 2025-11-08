import { InlineChat } from "../hub/InlineChat";
import { ActionEmbedComponent } from "./ActionEmbed";
import type { ActionEmbed } from "../../lib/actionEmbeds";

interface Message {
  id: string;
  chatId: string;
  role: "user" | "assistant" | "system";
  text?: string;
  embeds?: ActionEmbed[];
  ts: string;
}

interface ThreadViewProps {
  threadId: string;
  taskId: string;
  mode?: "workroom" | "default";
  onAddReference?: (ref: any) => void;
}

export function ThreadView({
  threadId,
  taskId,
  mode = "workroom",
  onAddReference,
}: ThreadViewProps) {
  const handleInputFocus = () => {
    window.dispatchEvent(new CustomEvent("workspace:focus-input"));
  };

  return (
    <div className="h-full flex flex-col">
      <InlineChat
        actionId={taskId}
        threadId={threadId}
        shouldFocus={false}
        onOpenWorkroom={undefined}
        mode={mode}
        onAddReference={onAddReference}
        onInputFocus={handleInputFocus}
      />
    </div>
  );
}

