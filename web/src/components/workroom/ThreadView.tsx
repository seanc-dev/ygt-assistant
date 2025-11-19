import { AssistantChat } from "../hub/AssistantChat";
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
  projectId?: string;
  projectTitle?: string;
  mode?: "workroom" | "default";
  onAddReference?: (ref: any) => void;
}

export function ThreadView({
  threadId,
  taskId,
  projectId,
  projectTitle,
  mode = "workroom",
  onAddReference,
}: ThreadViewProps) {
  const handleInputFocus = () => {
    window.dispatchEvent(new CustomEvent("workspace:focus-input"));
  };

  return (
    <div className="h-full flex flex-col min-h-0">
      <AssistantChat
        actionId={taskId}
        taskId={taskId}
        threadId={threadId}
        projectId={projectId}
        projectTitle={projectTitle}
        shouldFocus={false}
        onOpenWorkroom={undefined}
        mode={mode}
        onAddReference={onAddReference}
        onInputFocus={handleInputFocus}
      />
    </div>
  );
}
