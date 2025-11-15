import { useState } from "react";
import {
  Checkmark24Regular,
  Edit24Regular,
  Dismiss24Regular,
  ArrowUndo24Regular,
} from "@fluentui/react-icons";

export type LlmOperation = {
  op: string;
  params: Record<string, any>;
};

type ActionSummaryProps = {
  appliedOps: LlmOperation[];
  pendingOps: LlmOperation[];
  onApprove?: (op: LlmOperation) => void;
  onEdit?: (op: LlmOperation) => void;
  onDecline?: (op: LlmOperation) => void;
  onUndo?: (op: LlmOperation) => void;
  trustMode?: "training_wheels" | "supervised" | "autonomous";
};

function formatOperation(op: LlmOperation): string {
  const { op: opType, params } = op;
  
  switch (opType) {
    case "create_task":
      return `Task created: ${params.title || "Untitled"}`;
    case "update_task_status":
      return `Task ${params.task_id?.slice(0, 8)} status → ${params.status}`;
    case "link_action_to_task":
      return `Linked to task ${params.task_id?.slice(0, 8)}`;
    case "update_action_state":
      if (params.state === "deferred" && params.defer_until) {
        return `Deferred until ${new Date(params.defer_until).toLocaleDateString()}`;
      }
      if (params.added_to_today) {
        return "Added to today";
      }
      return `State → ${params.state}`;
    case "chat":
      return params.message?.substring(0, 50) || "Message sent";
    default:
      return `${opType} operation`;
  }
}

export function ActionSummary({
  appliedOps,
  pendingOps,
  onApprove,
  onEdit,
  onDecline,
  onUndo,
  trustMode = "training_wheels",
}: ActionSummaryProps) {
  const [expanded, setExpanded] = useState(false);
  
  // Show approval mode if there are pending ops
  const showApprovalMode = pendingOps.length > 0;
  
  if (appliedOps.length === 0 && pendingOps.length === 0) {
    return null;
  }
  
  return (
    <div className="border-t border-slate-200 bg-slate-50 p-4">
      {showApprovalMode && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-semibold text-slate-900">
              Proposed actions ({pendingOps.length})
            </h4>
            <button
              onClick={() => setExpanded(!expanded)}
              className="text-xs text-slate-600 hover:text-slate-900"
            >
              {expanded ? "Collapse" : "Expand"}
            </button>
          </div>
          
          <div className="space-y-2">
            {pendingOps.map((op, idx) => {
              const isDeleteProject = op.op === "delete_project";
              const projectIds = op.params?.project_ids || [];
              const taskCount = op.params?.tasks_deleted || 0;
              
              return (
                <div
                  key={idx}
                  className="flex items-start justify-between rounded-lg bg-white p-3 border border-slate-200"
                >
                  <div className="flex-1">
                    <span className="text-sm text-slate-700">
                      {formatOperation(op)}
                    </span>
                    {isDeleteProject && taskCount > 0 && (
                      <div className="mt-1 text-xs text-amber-600 font-medium">
                        ⚠️ This will also delete {taskCount} task{taskCount !== 1 ? 's' : ''}
                      </div>
                    )}
                  </div>
                  <div className="flex items-center gap-2 ml-4">
                  {onApprove && (
                    <button
                      onClick={() => onApprove(op)}
                      className="p-1.5 text-green-600 hover:bg-green-50 rounded transition-colors"
                      title="Approve"
                    >
                      <Checkmark24Regular className="w-4 h-4" />
                    </button>
                  )}
                  {onEdit && (
                    <button
                      onClick={() => onEdit(op)}
                      className="p-1.5 text-blue-600 hover:bg-blue-50 rounded transition-colors"
                      title="Edit"
                    >
                      <Edit24Regular className="w-4 h-4" />
                    </button>
                  )}
                  {onDecline && (
                    <button
                      onClick={() => onDecline(op)}
                      className="p-1.5 text-red-600 hover:bg-red-50 rounded transition-colors"
                      title="Decline"
                    >
                      <Dismiss24Regular className="w-4 h-4" />
                    </button>
                  )}
                </div>
              </div>
              );
            })}
          </div>
        </div>
      )}
      
      {appliedOps.length > 0 && (
        <div className={`space-y-2 ${showApprovalMode ? "mt-4 pt-4 border-t border-slate-200" : ""}`}>
          <h4 className="text-xs font-medium text-slate-600 uppercase tracking-wide">
            Applied ({appliedOps.length})
          </h4>
          <div className="flex flex-wrap gap-2">
            {appliedOps.map((op, idx) => {
              // Skip chat ops in summary pills
              if (op.op === "chat") {
                return null;
              }
              return (
                <div
                  key={idx}
                  className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-green-50 text-green-700 rounded-full text-xs"
                >
                  <span>{formatOperation(op)}</span>
                  {onUndo && (
                    <button
                      onClick={() => onUndo(op)}
                      className="ml-1 text-green-600 hover:text-green-800"
                      title="Undo"
                    >
                      <ArrowUndo24Regular className="w-3 h-3" />
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

