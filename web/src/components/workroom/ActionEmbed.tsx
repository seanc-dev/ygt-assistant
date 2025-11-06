import { useState } from "react";
import {
  CheckmarkCircle24Regular,
  DismissCircle24Regular,
  Edit24Regular,
  Document24Regular,
  Code24Regular,
  Mail24Regular,
  Calendar24Regular,
  Play24Regular,
} from "@fluentui/react-icons";
import type { ActionEmbed, ActionEmbedKind } from "../lib/actionEmbeds";
import { workroomApi } from "../lib/workroomApi";
import { Button } from "@ygt-assistant/ui";

interface ActionEmbedProps {
  embed: ActionEmbed;
  messageId: string;
  onUpdate?: (embed: ActionEmbed) => void;
}

const kindIcons: Record<string, React.ComponentType<{ className?: string }>> = {
  plan: Document24Regular,
  tool: Code24Regular,
  diff: Code24Regular,
  sendEmail: Mail24Regular,
  schedule: Calendar24Regular,
  runScript: Play24Regular,
};

const statusColors: Record<ActionEmbed["status"], string> = {
  proposed: "bg-blue-100 text-blue-800 border-blue-200",
  running: "bg-yellow-100 text-yellow-800 border-yellow-200",
  succeeded: "bg-green-100 text-green-800 border-green-200",
  failed: "bg-red-100 text-red-800 border-red-200",
  cancelled: "bg-gray-100 text-gray-800 border-gray-200",
};

export function ActionEmbedComponent({
  embed,
  messageId,
  onUpdate,
}: ActionEmbedProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const Icon = kindIcons[embed.kind] || Document24Regular;

  const handleApprove = async () => {
    setIsProcessing(true);
    try {
      const response = await workroomApi.approveActionEmbed(embed.id, messageId);
      if (response.ok && response.embed) {
        onUpdate?.(response.embed);
      }
    } catch (err) {
      console.error("Failed to approve embed:", err);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleEdit = async () => {
    // TODO: Open edit modal
    console.log("Edit embed:", embed.id);
  };

  const handleDecline = async () => {
    setIsProcessing(true);
    try {
      const response = await workroomApi.declineActionEmbed(embed.id, messageId);
      if (response.ok) {
        onUpdate?.({ ...embed, status: "cancelled" });
      }
    } catch (err) {
      console.error("Failed to decline embed:", err);
    } finally {
      setIsProcessing(false);
    }
  };

  const isCollapsed = embed.status === "cancelled" && !isExpanded;

  return (
    <div
      className={`rounded-lg border p-4 my-2 transition-all ${
        isCollapsed ? "opacity-60" : ""
      }`}
    >
      {/* Header */}
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 mt-0.5">
          <Icon className="w-5 h-5 text-slate-600" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-sm font-medium text-slate-900">
              {embed.title}
            </span>
            <span
              className={`text-xs px-2 py-0.5 rounded border ${statusColors[embed.status]}`}
            >
              {embed.status}
            </span>
          </div>
          <p className="text-sm text-slate-600">{embed.summary}</p>
        </div>
      </div>

      {/* Details (collapsible) */}
      {(embed.details || embed.preview || embed.diff) && (
        <div className="mt-3">
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-xs text-slate-500 hover:text-slate-700"
          >
            {isExpanded ? "Hide" : "Show"} details
          </button>
          {isExpanded && (
            <div className="mt-2 space-y-2">
              {embed.details && (
                <div className="text-sm text-slate-700 bg-slate-50 p-2 rounded">
                  {embed.details}
                </div>
              )}
              {embed.preview && (
                <div className="text-sm text-slate-700 bg-slate-50 p-2 rounded font-mono">
                  {embed.preview}
                </div>
              )}
              {embed.diff && (
                <div className="text-sm bg-slate-900 text-slate-100 p-2 rounded font-mono overflow-x-auto">
                  <pre>{embed.diff}</pre>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Controls (only when proposed) */}
      {embed.status === "proposed" && embed.controls && (
        <div className="flex gap-2 mt-3">
          {embed.controls.approve && (
            <Button
              variant="solid"
              size="sm"
              onClick={handleApprove}
              disabled={isProcessing}
            >
              <CheckmarkCircle24Regular className="w-4 h-4 mr-1" />
              Approve
            </Button>
          )}
          {embed.controls.edit && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleEdit}
              disabled={isProcessing}
            >
              <Edit24Regular className="w-4 h-4 mr-1" />
              Edit
            </Button>
          )}
          {embed.controls.decline && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleDecline}
              disabled={isProcessing}
            >
              <DismissCircle24Regular className="w-4 h-4 mr-1" />
              Decline
            </Button>
          )}
        </div>
      )}
    </div>
  );
}

