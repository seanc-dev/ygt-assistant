import { Dialog, Transition } from "@headlessui/react";
import { Fragment, useEffect, useMemo, useState } from "react";
import { Action, ActionLLMDraft } from "../lib/types";
import { Button } from "./Button";
import { Label } from "./Form/Label";
import { Field } from "./Form/Field";
import { Textarea } from "./Form/Textarea";
import {
  formatActionTitle,
  formatAgeLabel,
  getAttachmentLabel,
  getContextLabels,
  getEntitiesSummary,
  getKeyDates,
  getPriorityLabel,
  getProposedNextStep,
} from "../lib/actionUtils";

interface ActionDetailsModalProps {
  action: Action | null;
  onClose: () => void;
  onAccept: (patch: Partial<Action>) => Promise<void>;
  onSnooze: (action: Action, duration: string) => void;
  onDecline: (action: Action) => void;
  onAddNote: (action: Action) => void;
  onCreateTask: (action: Action) => void;
}

function formatDateValue(value?: string | null) {
  if (!value) return "";
  try {
    const date = new Date(value);
    const pad = (num: number) => String(num).padStart(2, "0");
    return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(
      date.getHours()
    )}:${pad(date.getMinutes())}`;
  } catch {
    return "";
  }
}

export function ActionDetailsModal({
  action,
  onClose,
  onAccept,
  onSnooze,
  onDecline,
  onAddNote,
  onCreateTask,
}: ActionDetailsModalProps) {
  const [title, setTitle] = useState(action?.title ?? "");
  const [summary, setSummary] = useState(action?.summary ?? "");
  const [dueAt, setDueAt] = useState(formatDateValue(action?.dueAt));
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copiedTone, setCopiedTone] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<"up" | "down" | null>(null);

  const open = Boolean(action);
  const metadata = action?.metadata ?? {};
  const contextLabels = useMemo(() => (action ? getContextLabels(action) : []), [action]);
  const entities = useMemo(() => (action ? getEntitiesSummary(action) : []), [action]);
  const keyDates = useMemo(() => (action ? getKeyDates(action) : []), [action]);
  const attachmentLabel = useMemo(() => (action ? getAttachmentLabel(action) : undefined), [action]);
  const priorityLabel = useMemo(() => (action ? getPriorityLabel(action) : undefined), [action]);
  const proposedNextStep = useMemo(() => (action ? getProposedNextStep(action) : undefined), [action]);
  const llmDrafts = metadata.llmDrafts ?? [];
  const quickNotes = metadata.quickNotes ?? [];
  const titleSuggestion = action ? formatActionTitle(action) : "";

  useEffect(() => {
    setTitle(action?.title ?? "");
    setSummary(action?.summary ?? "");
    setDueAt(formatDateValue(action?.dueAt));
    setCopiedTone(null);
    setFeedback(null);
  }, [action]);

  const handleSubmit = async () => {
    if (!action) return;
    setIsSubmitting(true);
    setError(null);
    try {
      await onAccept({
        title,
        summary,
        dueAt: dueAt ? new Date(dueAt).toISOString() : null,
      });
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save changes");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleUseDraft = (draft: ActionLLMDraft) => {
    if (draft.subject) {
      setTitle(draft.subject);
    }
    if (draft.body) {
      setSummary(draft.body);
    }
  };

  const handleCopyDraft = async (draft: ActionLLMDraft) => {
    const clipboard = typeof navigator !== "undefined" ? navigator.clipboard : undefined;
    if (!clipboard) {
      setCopiedTone(null);
      return;
    }
    try {
      await clipboard.writeText(`${draft.subject ?? ""}\n\n${draft.body ?? ""}`.trim());
      setCopiedTone(draft.tone);
    } catch {
      setCopiedTone(null);
    }
  };

  const handleFeedback = (value: "up" | "down") => {
    setFeedback(value);
  };

  return (
    <Transition show={open} as={Fragment}>
      <Dialog onClose={onClose} className="relative z-50">
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-200"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-150"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-slate-900/40 dark:bg-slate-950/60" aria-hidden="true" />
        </Transition.Child>

        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-200"
              enterFrom="opacity-0 translate-y-4"
              enterTo="opacity-100 translate-y-0"
              leave="ease-in duration-150"
              leaveFrom="opacity-100 translate-y-0"
              leaveTo="opacity-0 translate-y-4"
            >
              <Dialog.Panel className="w-full max-w-2xl rounded-lg bg-white p-6 shadow-xl focus:outline-none dark:bg-slate-900">
                <Dialog.Title className="text-lg font-semibold text-slate-900 dark:text-slate-100">
                  {titleSuggestion}
                </Dialog.Title>
                {action && (
                  <div className="mt-2 flex flex-wrap items-center gap-2 text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">
                    <span className="rounded-full border border-slate-200 px-2 py-1 dark:border-slate-700">
                      {action.type}
                    </span>
                    <span className="rounded-full border border-slate-200 px-2 py-1 dark:border-slate-700">
                      {formatAgeLabel(action)}
                    </span>
                    {priorityLabel && (
                      <span className="rounded-full border border-slate-200 px-2 py-1 dark:border-slate-700">
                        {priorityLabel}
                      </span>
                    )}
                  </div>
                )}

                <p className="mt-3 text-sm text-slate-600 dark:text-slate-400">
                  Make any edits before approving the action. Nothing is sent until you accept. Use smart suggestions to act quickly.
                </p>

                {contextLabels.length > 0 && (
                  <div className="mt-4 flex flex-wrap gap-2 text-xs text-slate-500 dark:text-slate-400">
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

                <div className="mt-4 space-y-4">
                  {proposedNextStep && action && (
                    <div className="rounded-md border border-primary-200 bg-primary-50 p-4 dark:border-primary-500/40 dark:bg-primary-500/10">
                      <div className="flex flex-wrap items-center justify-between gap-3">
                        <div>
                          <p className="text-sm font-semibold text-primary-800 dark:text-primary-200">
                            Suggested next step: {proposedNextStep.label || proposedNextStep.type}
                          </p>
                          {proposedNextStep.reason && (
                            <p className="mt-1 text-xs text-primary-700/80 dark:text-primary-200/80">{proposedNextStep.reason}</p>
                          )}
                        </div>
                        <div className="flex flex-wrap gap-2">
                          <Button type="button" variant="primary" onClick={handleSubmit} disabled={isSubmitting}>
                            {isSubmitting ? "Saving…" : "Accept as-is"}
                          </Button>
                          <Button type="button" variant="secondary" onClick={() => onCreateTask(action)}>
                            Create task
                          </Button>
                          <Button
                            type="button"
                            variant="ghost"
                            onClick={() => {
                              onDecline(action);
                              onClose();
                            }}
                          >
                            Decline
                          </Button>
                        </div>
                      </div>
                      {proposedNextStep.dueWithin && (
                        <p className="mt-2 text-xs text-primary-700/80 dark:text-primary-200/80">
                          Recommended timing: {proposedNextStep.dueWithin}
                        </p>
                      )}
                    </div>
                  )}

                  {action && (
                    <div className="rounded-md border border-slate-200 p-3 dark:border-slate-700">
                      <p className="text-sm font-semibold text-slate-700 dark:text-slate-200">Quick actions</p>
                      <div className="mt-2 flex flex-wrap gap-2">
                        <Button type="button" variant="primary" onClick={handleSubmit} disabled={isSubmitting}>
                          {isSubmitting ? "Saving…" : "Save & accept"}
                        </Button>
                        <Button type="button" variant="secondary" onClick={() => onSnooze(action, "1h")}>
                          Snooze 1h
                        </Button>
                        <Button type="button" variant="secondary" onClick={() => onSnooze(action, "1d")}>
                          Snooze 1d
                        </Button>
                        <Button type="button" variant="ghost" onClick={() => onAddNote(action)}>
                          Add note
                        </Button>
                        <Button type="button" variant="ghost" onClick={() => onCreateTask(action)}>
                          Create task
                        </Button>
                        <Button
                          type="button"
                          variant="danger"
                          onClick={() => {
                            onDecline(action);
                            onClose();
                          }}
                        >
                          Decline
                        </Button>
                      </div>
                    </div>
                  )}

                  <div>
                    <Label htmlFor="action-title">Title</Label>
                    <Field
                      id="action-title"
                      value={title}
                      onChange={(event) => setTitle(event.target.value)}
                    />
                  </div>
                  <div>
                    <Label htmlFor="action-summary">Summary</Label>
                    <Textarea
                      id="action-summary"
                      rows={4}
                      value={summary}
                      onChange={(event) => setSummary(event.target.value)}
                    />
                  </div>
                  <div>
                    <Label htmlFor="action-due">Due</Label>
                    <Field
                      id="action-due"
                      type="datetime-local"
                      value={dueAt ?? ""}
                      onChange={(event) => setDueAt(event.target.value)}
                    />
                  </div>
                </div>

                {error && (
                  <p className="mt-3 text-sm text-red-500 dark:text-red-400" role="alert">
                    {error}
                  </p>
                )}

                {action && (
                  <div className="mt-6 space-y-4 text-sm text-slate-600 dark:text-slate-300">
                    {(keyDates.length > 0 || attachmentLabel) && (
                      <div className="rounded-md bg-slate-100/70 p-3 dark:bg-slate-800/60">
                        {keyDates.length > 0 && (
                          <p className="font-semibold">Key dates: {keyDates.join(" • ")}</p>
                        )}
                        {attachmentLabel && <p className="mt-1">Attachments: {attachmentLabel}</p>}
                      </div>
                    )}

                    {entities.length > 0 && (
                      <div className="rounded-md border border-slate-200 p-3 dark:border-slate-700">
                        <p className="font-semibold">Extracted entities</p>
                        <ul className="mt-2 grid gap-2 sm:grid-cols-2">
                          {entities.map((entity) => (
                            <li key={entity.label} className="text-sm">
                              <span className="font-semibold capitalize">{entity.label}:</span> {entity.values.join(", ")}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {llmDrafts.length > 0 && (
                      <div className="rounded-md border border-slate-200 p-3 dark:border-slate-700">
                        <p className="font-semibold">Draft replies</p>
                        <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                          Choose a tone to auto-fill your reply. You can edit before sending.
                        </p>
                        <div className="mt-3 space-y-3">
                          {llmDrafts.map((draft) => (
                            <div key={draft.tone} className="rounded-md bg-slate-50 p-3 dark:bg-slate-800/60">
                              <div className="flex flex-wrap items-center justify-between gap-2">
                                <span className="text-sm font-semibold capitalize">{draft.tone}</span>
                                <div className="flex gap-2">
                                  <Button type="button" variant="secondary" onClick={() => handleUseDraft(draft)}>
                                    Use draft
                                  </Button>
                                  <Button type="button" variant="ghost" onClick={() => handleCopyDraft(draft)}>
                                    {copiedTone === draft.tone ? "Copied" : "Copy"}
                                  </Button>
                                </div>
                              </div>
                              {draft.subject && (
                                <p className="mt-2 text-xs font-semibold text-slate-500 dark:text-slate-400">Subject: {draft.subject}</p>
                              )}
                              {draft.body && (
                                <p className="mt-2 whitespace-pre-line text-sm text-slate-600 dark:text-slate-300">{draft.body}</p>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {metadata.calendarSuggestions?.times && metadata.calendarSuggestions.times.length > 0 && (
                      <div className="rounded-md border border-slate-200 p-3 dark:border-slate-700">
                        <p className="font-semibold">Suggested meeting times</p>
                        <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                          Time zone: {metadata.calendarSuggestions.timezone ?? "auto"}
                        </p>
                        <div className="mt-2 flex flex-wrap gap-2">
                          {metadata.calendarSuggestions.times.map((time) => (
                            <span key={time} className="rounded-md bg-slate-100 px-2 py-1 text-xs dark:bg-slate-800">
                              {time}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {action.metadata?.thread && (
                      <div className="rounded-md border border-slate-200 p-3 dark:border-slate-700">
                        <p className="font-semibold">Thread context</p>
                        {action.metadata.thread.link && (
                          <a
                            href={action.metadata.thread.link}
                            target="_blank"
                            rel="noreferrer"
                            className="text-xs font-medium text-primary-600 underline dark:text-primary-300"
                          >
                            Open original
                          </a>
                        )}
                        {action.metadata.thread.lastMessageSnippet && (
                          <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
                            {action.metadata.thread.lastMessageSnippet}
                          </p>
                        )}
                      </div>
                    )}

                    {(metadata.whyThis || metadata.matchedRule) && (
                      <div className="rounded-md border border-slate-200 p-3 dark:border-slate-700">
                        <p className="text-sm font-semibold text-slate-700 dark:text-slate-200">Why this surfaced</p>
                        {metadata.whyThis?.rule && <p className="mt-1 text-sm">Rule: {metadata.whyThis.rule}</p>}
                        {metadata.whyThis?.fields && (
                          <p className="mt-1 text-sm">Fields: {metadata.whyThis.fields.join(", ")}</p>
                        )}
                        {metadata.whyThis?.confidence && (
                          <p className="mt-1 text-sm">Confidence: {Math.round(metadata.whyThis.confidence * 100)}%</p>
                        )}
                        {metadata.whyThis?.examples && metadata.whyThis.examples.length > 0 && (
                          <ul className="mt-2 list-disc space-y-1 pl-4 text-xs">
                            {metadata.whyThis.examples.map((example, index) => (
                              <li key={index}>{example}</li>
                            ))}
                          </ul>
                        )}
                      </div>
                    )}

                    {quickNotes.length > 0 && (
                      <div className="rounded-md border border-slate-200 p-3 dark:border-slate-700">
                        <p className="font-semibold">Notes</p>
                        <ul className="mt-2 space-y-1 text-sm">
                          {quickNotes.map((note, index) => (
                            <li key={`${note}-${index}`} className="rounded-md bg-slate-50 px-2 py-1 dark:bg-slate-800/60">
                              {note}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    <div className="rounded-md border border-slate-200 p-3 dark:border-slate-700">
                      <p className="text-sm font-semibold text-slate-700 dark:text-slate-200">Did we get this right?</p>
                      <div className="mt-2 flex gap-2">
                        <Button
                          type="button"
                          variant={feedback === "up" ? "primary" : "secondary"}
                          onClick={() => handleFeedback("up")}
                        >
                          👍 Thumbs up
                        </Button>
                        <Button
                          type="button"
                          variant={feedback === "down" ? "danger" : "ghost"}
                          onClick={() => handleFeedback("down")}
                        >
                          👎 Thumbs down
                        </Button>
                      </div>
                      {feedback && (
                        <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">
                          Thanks! We&apos;ll adapt future suggestions {feedback === "up" ? "to match this preference." : "and dial this back."}
                        </p>
                      )}
                    </div>
                  </div>
                )}

                <div className="mt-6 flex justify-end gap-3">
                  <Button type="button" variant="secondary" onClick={onClose}>
                    Close
                  </Button>
                  <Button type="button" onClick={handleSubmit} disabled={isSubmitting}>
                    {isSubmitting ? "Saving…" : "Save & accept"}
                  </Button>
                </div>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  );
}
