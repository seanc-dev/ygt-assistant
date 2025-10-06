import { KeyboardEvent } from "react";
import { format } from "date-fns";
import clsx from "clsx";
import { Action } from "../lib/types";
import {
  formatActionTitle,
  formatAgeLabel,
  formatRiskLevel,
  getAttachmentLabel,
  getContextLabels,
  getEntitiesSummary,
  getInlinePreview,
  getKeyDates,
  getPriorityLabel,
  getProposedNextStep,
  getSavedViewTags,
} from "../lib/actionUtils";
import { Button } from "./Button";

interface ActionRowProps {
  action: Action;
  selected: boolean;
  onSelect: (action: Action, selected: boolean) => void;
  onAccept: (action: Action) => void;
  onEdit: (action: Action) => void;
  onDecline: (action: Action) => void;
  onSnooze: (action: Action, duration: string) => void;
  onAddNote: (action: Action) => void;
  onCreateTask: (action: Action) => void;
  groupSize?: number;
  onSelectGroup?: (action: Action) => void;
  onSnoozeGroup?: (action: Action, duration: string) => void;
}

const statusStyles: Record<Action["status"], string> = {
  pending: "bg-amber-100 text-amber-900 dark:bg-amber-500/20 dark:text-amber-100",
  accepted: "bg-emerald-100 text-emerald-900 dark:bg-emerald-500/20 dark:text-emerald-100",
  declined: "bg-rose-100 text-rose-900 dark:bg-rose-500/20 dark:text-rose-100",
  scheduled: "bg-sky-100 text-sky-900 dark:bg-sky-500/20 dark:text-sky-100",
};

export function ActionRow({
  action,
  selected,
  onSelect,
  onAccept,
  onEdit,
  onDecline,
  onSnooze,
  onAddNote,
  onCreateTask,
  groupSize,
  onSelectGroup,
  onSnoozeGroup,
}: ActionRowProps) {
  const title = formatActionTitle(action);
  const contextLabels = getContextLabels(action);
  const preview = getInlinePreview(action);
  const keyDates = getKeyDates(action);
  const attachmentLabel = getAttachmentLabel(action);
  const entities = getEntitiesSummary(action);
  const risk = formatRiskLevel(action.metadata?.risk?.level);
  const priorityLabel = getPriorityLabel(action);
  const savedViews = getSavedViewTags(action);
  const proposedNextStep = getProposedNextStep(action);

  const handleKeyDown = (event: KeyboardEvent<HTMLTableRowElement>) => {
    if (event.defaultPrevented) return;
    if (event.key === "Enter") {
      event.preventDefault();
      onAccept(action);
    } else if (event.key.toLowerCase() === "e") {
      event.preventDefault();
      onEdit(action);
    } else if (event.key.toLowerCase() === "d") {
      event.preventDefault();
      onDecline(action);
    } else if (event.key === "?") {
      event.preventDefault();
      onEdit(action);
    }
  };

  return (
    <tr
      className="border-b border-slate-200 transition hover:bg-slate-50 focus-within:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-800/40"
      tabIndex={0}
      onKeyDown={handleKeyDown}
      aria-selected={selected}
    >
      <td className="px-4 py-3 align-top">
        <input
          type="checkbox"
          className="h-4 w-4 rounded border-slate-300 text-primary-600 focus:ring-primary-500 dark:border-slate-600 dark:bg-slate-900"
          checked={selected}
          onChange={(event) => onSelect(action, event.target.checked)}
          aria-label={`Select ${title}`}
        />
      </td>
      <td className="px-4 py-3 align-top text-sm">
        <div className="flex flex-col gap-2">
          <div className="flex flex-wrap items-start justify-between gap-2">
            <div>
              <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">{title}</p>
              <p className="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">{action.type}</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span
                className={clsx(
                  "inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold capitalize",
                  statusStyles[action.status]
                )}
              >
                {action.status}
                <span className="ml-2 font-normal text-[10px] uppercase tracking-wide opacity-80">
                  {formatAgeLabel(action)}
                </span>
              </span>
              {risk && (
                <span className={clsx("inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold", risk.className)}>
                  {risk.label}
                </span>
              )}
              {priorityLabel && (
                <span className="inline-flex items-center rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-700 dark:bg-slate-800 dark:text-slate-200">
                  {priorityLabel}
                </span>
              )}
            </div>
          </div>

          {contextLabels.length > 0 && (
            <div className="flex flex-wrap gap-2 text-xs text-slate-500 dark:text-slate-400">
              {contextLabels.map((item) => (
                <span
                  key={`${item.label}-${item.value}`}
                  className="inline-flex items-center gap-1 rounded-md border border-slate-200 px-2 py-1 dark:border-slate-700"
                >
                  <span className="font-semibold text-slate-600 dark:text-slate-300">{item.label}:</span>
                  <span>{item.value}</span>
                </span>
              ))}
            </div>
          )}

          {preview && (
            <p className="text-sm text-slate-600 line-clamp-2 dark:text-slate-300">{preview}</p>
          )}

          {(keyDates.length > 0 || attachmentLabel) && (
            <div className="flex flex-wrap items-center gap-3 text-xs text-slate-500 dark:text-slate-400">
              {keyDates.length > 0 && (
                <div className="flex items-center gap-1">
                  <span className="font-semibold">Key dates:</span>
                  <span>{keyDates.join(" • ")}</span>
                </div>
              )}
              {attachmentLabel && (
                <div className="flex items-center gap-1">
                  <span className="font-semibold">Attachments:</span>
                  <span>{attachmentLabel}</span>
                </div>
              )}
            </div>
          )}

          {entities.length > 0 && (
            <div className="flex flex-wrap gap-2 text-xs text-slate-500 dark:text-slate-400">
              {entities.map((entity) => (
                <span
                  key={entity.label}
                  className="inline-flex items-center gap-2 rounded-md bg-slate-100 px-2 py-1 dark:bg-slate-800"
                >
                  <span className="font-semibold capitalize text-slate-600 dark:text-slate-300">{entity.label}:</span>
                  <span>{entity.values.join(", ")}</span>
                </span>
              ))}
            </div>
          )}

          {groupSize && groupSize > 1 && (
            <div className="rounded-md border border-dashed border-slate-200 bg-slate-50 p-3 text-xs text-slate-600 dark:border-slate-700 dark:bg-slate-800/40 dark:text-slate-300">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="font-semibold text-slate-700 dark:text-slate-200">
                  Batched with {groupSize - 1} similar item{groupSize - 1 === 1 ? "" : "s"}
                </div>
                <div className="flex flex-wrap gap-2">
                  <Button
                    type="button"
                    variant="ghost"
                    onClick={() => onSelectGroup?.(action)}
                  >
                    Select group
                  </Button>
                  <Button
                    type="button"
                    variant="secondary"
                    onClick={() => onSnoozeGroup?.(action, "1d")}
                  >
                    Snooze group 1d
                  </Button>
                </div>
              </div>
            </div>
          )}

          {proposedNextStep && (
            <div className="rounded-md border border-primary-100 bg-primary-50/60 p-3 text-sm dark:border-primary-500/30 dark:bg-primary-500/10">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <p className="font-semibold text-primary-700 dark:text-primary-200">
                    Smart suggestion: {proposedNextStep.label || proposedNextStep.type}
                  </p>
                  {proposedNextStep.reason && (
                    <p className="mt-1 text-xs text-primary-700/80 dark:text-primary-200/80">{proposedNextStep.reason}</p>
                  )}
                </div>
                <div className="flex flex-wrap gap-2">
                  <Button variant="secondary" onClick={() => onAccept(action)}>
                    Accept
                  </Button>
                  <Button variant="ghost" onClick={() => onEdit(action)}>
                    Edit first
                  </Button>
                </div>
              </div>
            </div>
          )}

          {savedViews.length > 0 && (
            <div className="flex flex-wrap gap-2 text-[10px] uppercase tracking-wide text-slate-400 dark:text-slate-500">
              {savedViews.map((tag) => (
                <span key={tag} className="rounded-full border border-dashed border-slate-300 px-2 py-0.5 dark:border-slate-700">
                  {tag}
                </span>
              ))}
            </div>
          )}

          <div className="flex flex-wrap items-center gap-2 text-[11px] uppercase tracking-wide text-slate-400 dark:text-slate-500">
            <span className="flex items-center gap-1">
              <kbd className="rounded border border-slate-300 bg-white px-1 dark:border-slate-700 dark:bg-slate-900">Enter</kbd>
              Accept
            </span>
            <span className="flex items-center gap-1">
              <kbd className="rounded border border-slate-300 bg-white px-1 dark:border-slate-700 dark:bg-slate-900">E</kbd>
              Edit
            </span>
            <span className="flex items-center gap-1">
              <kbd className="rounded border border-slate-300 bg-white px-1 dark:border-slate-700 dark:bg-slate-900">D</kbd>
              Decline
            </span>
            <span className="flex items-center gap-1">
              <kbd className="rounded border border-slate-300 bg-white px-1 dark:border-slate-700 dark:bg-slate-900">?</kbd>
              Details
            </span>
          </div>
        </div>
      </td>
      <td className="px-4 py-3 align-top text-sm text-slate-600 dark:text-slate-300">
        {format(new Date(action.createdAt), "PP p")}
      </td>
      <td className="px-4 py-3 align-top text-sm text-slate-600 dark:text-slate-300">
        {action.dueAt ? format(new Date(action.dueAt), "PP p") : "—"}
      </td>
      <td className="px-4 py-3 align-top text-right">
        <div className="flex flex-wrap justify-end gap-2">
          <Button variant="ghost" onClick={() => onEdit(action)}>
            Details
          </Button>
          <Button variant="primary" onClick={() => onAccept(action)}>
            Accept
          </Button>
          <Button variant="secondary" onClick={() => onSnooze(action, "1h")}>
            Snooze 1h
          </Button>
          <Button variant="ghost" onClick={() => onAddNote(action)}>
            Add note
          </Button>
          <Button variant="ghost" onClick={() => onCreateTask(action)}>
            Create task
          </Button>
          <Button variant="danger" onClick={() => onDecline(action)}>
            Decline
          </Button>
        </div>
      </td>
    </tr>
  );
}
