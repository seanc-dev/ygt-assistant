import { Dialog, Transition } from "@headlessui/react";
import { Fragment, useEffect, useMemo, useState } from "react";
import { Rule, RuleCondition, RuleOutcome } from "../lib/types";
import { Button } from "./Button";
import { Label } from "./Form/Label";
import { Field } from "./Form/Field";

interface RuleEditorModalProps {
  open: boolean;
  rule?: Rule;
  onClose: () => void;
  onSave: (input: {
    actionType: Rule["actionType"];
    outcome: RuleOutcome;
    conditions: RuleCondition[];
    enabled: boolean;
  }) => Promise<void>;
}

const defaultCondition: RuleCondition = {
  field: "title",
  op: "includes",
  value: "",
};

export function RuleEditorModal({ open, rule, onClose, onSave }: RuleEditorModalProps) {
  const [actionType, setActionType] = useState<Rule["actionType"]>(rule?.actionType ?? "any");
  const [outcome, setOutcome] = useState<RuleOutcome>(rule?.outcome ?? "hold");
  const [conditions, setConditions] = useState<RuleCondition[]>(rule?.conditions ?? [defaultCondition]);
  const [enabled, setEnabled] = useState<boolean>(rule?.enabled ?? true);
  const [errors, setErrors] = useState<string[]>([]);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (!open) return;
    setActionType(rule?.actionType ?? "any");
    setOutcome(rule?.outcome ?? "hold");
    setConditions(rule?.conditions ?? [defaultCondition]);
    setEnabled(rule?.enabled ?? true);
    setErrors([]);
  }, [open, rule]);

  const hasConditionErrors = useMemo(
    () =>
      conditions.some((condition) => !condition.field.trim() || !condition.value.trim()),
    [conditions]
  );

  const handleSave = async () => {
    const summary: string[] = [];
    if (!conditions.length) {
      summary.push("Add at least one condition.");
    }
    if (hasConditionErrors) {
      summary.push("Each condition needs a field and value.");
    }
    if (!outcome) {
      summary.push("Choose an outcome.");
    }
    if (summary.length > 0) {
      setErrors(summary);
      return;
    }

    setIsSaving(true);
    try {
      await onSave({ actionType, outcome, conditions, enabled });
      onClose();
    } catch (error) {
      setErrors([error instanceof Error ? error.message : "Unable to save rule"]);
    } finally {
      setIsSaving(false);
    }
  };

  const updateCondition = (index: number, patch: Partial<RuleCondition>) => {
    setConditions((prev) => {
      const next = [...prev];
      next[index] = { ...next[index], ...patch };
      return next;
    });
  };

  const removeCondition = (index: number) => {
    setConditions((prev) => prev.filter((_, idx) => idx !== index));
  };

  const addCondition = () => {
    setConditions((prev) => [...prev, { ...defaultCondition }]);
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
              <Dialog.Panel className="w-full max-w-2xl rounded-lg bg-white p-6 shadow-xl dark:bg-slate-900">
                <Dialog.Title className="text-lg font-semibold text-slate-900 dark:text-slate-100">
                  {rule ? "Edit rule" : "New rule"}
                </Dialog.Title>
                <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
                  Rules run in priority order. Turn off anything you no longer need.
                </p>

                {errors.length > 0 && (
                  <div
                    className="mt-4 rounded-md border border-red-200 bg-red-50 p-3 dark:border-red-700 dark:bg-red-900/30"
                    role="alert"
                    aria-live="assertive"
                  >
                    <p className="text-sm font-semibold text-red-700 dark:text-red-300">Fix the following:</p>
                    <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-red-700 dark:text-red-300">
                      {errors.map((error, index) => (
                        <li key={index}>{error}</li>
                      ))}
                    </ul>
                  </div>
                )}

                <div className="mt-4 space-y-6">
                  <div className="grid gap-4 sm:grid-cols-2">
                    <div>
                      <Label htmlFor="rule-action-type">Action type</Label>
                      <select
                        id="rule-action-type"
                        value={actionType}
                        onChange={(event) => setActionType(event.target.value as Rule["actionType"])}
                        className="focus-outline mt-1 block w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-900 dark:text-slate-100"
                      >
                        <option value="any">Any</option>
                        <option value="email">Email</option>
                        <option value="calendar">Calendar</option>
                        <option value="task">Task</option>
                        <option value="other">Other</option>
                      </select>
                    </div>
                    <div>
                      <Label htmlFor="rule-outcome">Outcome</Label>
                      <select
                        id="rule-outcome"
                        value={outcome}
                        onChange={(event) => setOutcome(event.target.value as RuleOutcome)}
                        className="focus-outline mt-1 block w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-900 dark:text-slate-100"
                      >
                        <option value="accept">Accept</option>
                        <option value="hold">Hold</option>
                        <option value="decline">Decline</option>
                      </select>
                    </div>
                  </div>

                  <div>
                    <div className="flex items-center justify-between">
                      <Label>Conditions</Label>
                      <Button type="button" variant="ghost" onClick={addCondition}>
                        Add condition
                      </Button>
                    </div>
                    <div className="mt-3 space-y-3">
                      {conditions.map((condition, index) => (
                        <div
                          key={index}
                          className="grid gap-3 rounded-md border border-slate-200 p-3 sm:grid-cols-[1fr_auto_1fr_auto] dark:border-slate-700"
                        >
                          <div>
                            <Label htmlFor={`rule-field-${index}`}>Field</Label>
                            <Field
                              id={`rule-field-${index}`}
                              value={condition.field}
                              onChange={(event) =>
                                updateCondition(index, { field: event.target.value })
                              }
                              invalid={!condition.field}
                            />
                          </div>
                          <div>
                            <Label htmlFor={`rule-operator-${index}`}>Operator</Label>
                            <select
                              id={`rule-operator-${index}`}
                              value={condition.op}
                              onChange={(event) =>
                                updateCondition(index, { op: event.target.value as RuleCondition["op"] })
                              }
                              className="focus-outline mt-1 block w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-900 dark:text-slate-100"
                            >
                              <option value="eq">Equals</option>
                              <option value="neq">Does not equal</option>
                              <option value="lt">Before</option>
                              <option value="gt">After</option>
                              <option value="includes">Includes</option>
                              <option value="regex">Matches regex</option>
                            </select>
                          </div>
                          <div>
                            <Label htmlFor={`rule-value-${index}`}>Value</Label>
                            <Field
                              id={`rule-value-${index}`}
                              value={condition.value}
                              onChange={(event) =>
                                updateCondition(index, { value: event.target.value })
                              }
                              invalid={!condition.value}
                            />
                          </div>
                          <div className="flex items-end justify-end">
                            <Button
                              type="button"
                              variant="ghost"
                              onClick={() => removeCondition(index)}
                              disabled={conditions.length === 1}
                            >
                              Remove
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <input
                      id="rule-enabled"
                      type="checkbox"
                      checked={enabled}
                      onChange={(event) => setEnabled(event.target.checked)}
                      className="h-4 w-4 rounded border-slate-300 text-primary-600 focus:ring-primary-500 dark:border-slate-600 dark:bg-slate-900 dark:checked:bg-primary-500"
                    />
                    <Label htmlFor="rule-enabled" className="!m-0">
                      Enable rule
                    </Label>
                  </div>
                </div>

                <div className="mt-6 flex justify-end gap-3">
                  <Button type="button" variant="secondary" onClick={onClose}>
                    Cancel
                  </Button>
                  <Button type="button" onClick={handleSave} disabled={isSaving}>
                    {isSaving ? "Saving…" : "Save rule"}
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
