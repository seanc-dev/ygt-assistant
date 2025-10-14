import Head from "next/head";
import { GetServerSideProps } from "next";
import { getServerSession } from "next-auth";
import { useSession } from "next-auth/react";
import { useMemo, useState } from "react";
import {
  DndContext,
  PointerSensor,
  closestCenter,
  useSensor,
  useSensors,
  DragEndEvent,
} from "@dnd-kit/core";
import {
  SortableContext,
  arrayMove,
  useSortable,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { authOptions } from "./api/auth/[...nextauth]";
import { NavBar } from "../components/NavBar";
import { Button } from "../components/Button";
import { Label } from "../components/Form/Label";
import { RuleRow } from "../components/RuleRow";
import { RuleEditorModal } from "../components/RuleEditorModal";
import { Textarea } from "../components/Form/Textarea";
import { api } from "../lib/api";
import { queryKeys } from "../lib/queryKeys";
import { Rule, RuleCondition, RuleSuggestion } from "../lib/types";

export const getServerSideProps: GetServerSideProps = async (context) => {
  if (process.env.RUN_E2E === "true") {
    return { props: {} };
  }
  const session = await getServerSession(context.req, context.res, authOptions);
  if (!session) {
    return {
      redirect: {
        destination: "/login",
        permanent: false,
      },
    };
  }
  return { props: {} };
};

function SortableRule({ rule, onEdit, onToggle }: {
  rule: Rule;
  onEdit: (rule: Rule) => void;
  onToggle: (rule: Rule, enabled: boolean) => void;
}) {
  const { attributes, listeners, setNodeRef, transform, transition } = useSortable({ id: rule.id });

  return (
    <div
      ref={setNodeRef}
      style={{ transform: CSS.Transform.toString(transform), transition }}
      className="cursor-grab"
      {...attributes}
      {...listeners}
    >
      <RuleRow rule={rule} onEdit={onEdit} onToggle={onToggle} />
    </div>
  );
}

export default function RulesPage() {
  const { status } = useSession();
  const queryClient = useQueryClient();
  const [selectedRule, setSelectedRule] = useState<Rule | undefined>();
  const [isModalOpen, setModalOpen] = useState(false);
  const [suggestPrompt, setSuggestPrompt] = useState("");
  const [suggestSample, setSuggestSample] = useState("");
  const [suggestions, setSuggestions] = useState<RuleSuggestion[]>([]);
  const [testInput, setTestInput] = useState(
    '{\n  "subject": "Invoice reminder",\n  "body": "Hi team, invoice #123 is due tomorrow"\n}'
  );
  const [testResults, setTestResults] = useState<
    | { matches: { rule: Rule; confidence: number }[]; error?: string }
    | null
  >(null);

  const rulesQuery = useQuery({
    queryKey: queryKeys.rules,
    queryFn: () => api.rules.list(),
    enabled: status === "authenticated",
  });

  const rules = rulesQuery.data ?? [];

  const sensors = useSensors(useSensor(PointerSensor));

  const createRuleMutation = useMutation({
    mutationFn: (input: {
      actionType: Rule["actionType"];
      outcome: Rule["outcome"];
      conditions: RuleCondition[];
      enabled: boolean;
    }) =>
      api.rules.create({
        ...input,
        priority: rules.length + 1,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.rules });
    },
  });

  const updateRuleMutation = useMutation({
    mutationFn: ({ id, patch }: { id: string; patch: Partial<Rule> }) => api.rules.update(id, patch),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.rules });
    },
  });

  const reorderMutation = useMutation({
    mutationFn: (order: string[]) => api.rules.reorder(order),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.rules });
    },
  });

  const suggestMutation = useMutation({
    mutationFn: (input: { description?: string; sample?: string }) =>
      api.rules.suggest(input),
    onSuccess: (data) => {
      setSuggestions(data);
    },
  });

  const handleEdit = (rule: Rule) => {
    setSelectedRule(rule);
    setModalOpen(true);
  };

  const handleNewRule = () => {
    setSelectedRule(undefined);
    setModalOpen(true);
  };

  const handleToggle = (rule: Rule, enabled: boolean) => {
    updateRuleMutation.mutate({ id: rule.id, patch: { enabled } });
  };

  const handleSave = async (input: {
    actionType: Rule["actionType"];
    outcome: Rule["outcome"];
    conditions: RuleCondition[];
    enabled: boolean;
  }) => {
    if (selectedRule) {
      await updateRuleMutation.mutateAsync({ id: selectedRule.id, patch: input });
    } else {
      await createRuleMutation.mutateAsync(input);
    }
  };

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    if (!over || active.id === over.id) return;
    const oldIndex = rules.findIndex((rule) => rule.id === active.id);
    const newIndex = rules.findIndex((rule) => rule.id === over.id);
    if (oldIndex === -1 || newIndex === -1) return;
    const reordered = arrayMove(rules, oldIndex, newIndex).map((rule, index) => ({
      ...rule,
      priority: index + 1,
    }));
    queryClient.setQueryData(queryKeys.rules, reordered);
    reorderMutation.mutate(reordered.map((rule) => rule.id));
  };

  const handleSuggest = () => {
    suggestMutation.mutate({
      description: suggestPrompt || undefined,
      sample: suggestSample || undefined,
    });
  };

  const evaluateRules = () => {
    let payload: Record<string, unknown> | string = testInput;
    try {
      payload = JSON.parse(testInput);
    } catch {
      // keep as string
    }
    const getFieldValue = (field: string) => {
      if (typeof payload === "string") {
        return payload;
      }
      const value = (payload as Record<string, unknown>)[field];
      if (value == null) return "";
      return String(value);
    };
    const asText = typeof payload === "string" ? payload.toLowerCase() : JSON.stringify(payload).toLowerCase();

    const matches = rules
      .map((rule) => {
        let satisfied = 0;
        for (const condition of rule.conditions) {
          const source = getFieldValue(condition.field).toString().toLowerCase();
          const comparator = condition.value.toLowerCase();
          let isMatch = false;
          switch (condition.op) {
            case "includes":
              isMatch = source.includes(comparator);
              break;
            case "eq":
              isMatch = source === comparator;
              break;
            case "neq":
              isMatch = source !== comparator;
              break;
            case "regex":
              try {
                isMatch = new RegExp(condition.value).test(getFieldValue(condition.field).toString());
              } catch {
                isMatch = false;
              }
              break;
            default:
              isMatch = asText.includes(comparator);
          }
          if (isMatch) satisfied += 1;
          else return null;
        }
        const confidence = rule.conditions.length
          ? Math.round((satisfied / rule.conditions.length) * 100) / 100
          : 1;
        return { rule, confidence };
      })
      .filter((value): value is { rule: Rule; confidence: number } => value !== null);

    setTestResults({ matches });
  };

  const topMatches = useMemo(() => testResults?.matches ?? [], [testResults]);

  return (
    <>
      <Head>
        <title>Rules</title>
      </Head>
      <div className="min-h-screen bg-slate-50">
        <NavBar />
        <main className="mx-auto max-w-4xl px-4 py-8 sm:px-6">
          <div className="flex items-center justify-between gap-3">
            <div>
              <h1 className="text-2xl font-semibold text-slate-900">Rules</h1>
              <p className="text-sm text-slate-600">
                Rules run from top to bottom. Drag to reorder and toggle to pause.
              </p>
            </div>
            <Button onClick={handleNewRule}>New rule</Button>
          </div>

          <section className="mt-6 grid gap-6 lg:grid-cols-2">
            <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-700 dark:bg-slate-900">
              <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">LLM rule suggestions</h2>
              <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
                Describe what you want to automate or paste an example email. CoachFlow suggests ready-to-apply rules.
              </p>
              <div className="mt-4 space-y-3">
                <div>
                  <Label htmlFor="rule-suggest-prompt">Goal</Label>
                  <Textarea
                    id="rule-suggest-prompt"
                    rows={3}
                    value={suggestPrompt}
                    onChange={(event) => setSuggestPrompt(event.target.value)}
                  />
                </div>
                <div>
                  <Label htmlFor="rule-suggest-sample">Sample email</Label>
                  <Textarea
                    id="rule-suggest-sample"
                    rows={4}
                    value={suggestSample}
                    onChange={(event) => setSuggestSample(event.target.value)}
                  />
                </div>
              </div>
              <div className="mt-4 flex items-center gap-3">
                <Button type="button" onClick={handleSuggest} disabled={suggestMutation.isPending}>
                  {suggestMutation.isPending ? "Generating…" : "Suggest rules"}
                </Button>
                {suggestMutation.isError && (
                  <p className="text-sm text-red-500">Unable to fetch suggestions. Try again.</p>
                )}
              </div>
            </div>
            <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-700 dark:bg-slate-900">
              <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">Rule testbed</h2>
              <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
                Paste a JSON payload or plain text. We&apos;ll show which rules would trigger and their confidence.
              </p>
              <Textarea
                className="mt-3"
                rows={6}
                value={testInput}
                onChange={(event) => setTestInput(event.target.value)}
              />
              <div className="mt-3 flex items-center justify-between">
                <Button type="button" variant="secondary" onClick={evaluateRules}>
                  Run test
                </Button>
                <span className="text-xs text-slate-500 dark:text-slate-400">
                  Matches: {topMatches.length}
                </span>
              </div>
              {topMatches.length > 0 && (
                <ul className="mt-3 space-y-2">
                  {topMatches.map(({ rule, confidence }) => (
                    <li
                      key={rule.id}
                      className="rounded-md border border-slate-200 bg-slate-50 p-3 text-sm dark:border-slate-700 dark:bg-slate-800"
                    >
                      <p className="font-semibold text-slate-800 dark:text-slate-200">{rule.actionType} → {rule.outcome}</p>
                      <p className="text-xs text-slate-500 dark:text-slate-400">Confidence {Math.round(confidence * 100)}%</p>
                    </li>
                  ))}
                </ul>
              )}
              {topMatches.length === 0 && testResults && (
                <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">No rules matched this sample yet.</p>
              )}
            </div>
          </section>

          {suggestions.length > 0 && (
            <section className="mt-6 space-y-3">
              <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">Suggested rules</h2>
              <div className="grid gap-3 lg:grid-cols-2">
                {suggestions.map((suggestion) => (
                  <div
                    key={suggestion.id}
                    className="flex h-full flex-col justify-between rounded-lg border border-primary-100 bg-primary-50 p-4 shadow-sm dark:border-primary-500/30 dark:bg-primary-500/10"
                  >
                    <div>
                      <h3 className="text-base font-semibold text-primary-800 dark:text-primary-200">
                        {suggestion.title}
                      </h3>
                      <p className="mt-1 text-sm text-primary-700/80 dark:text-primary-200/80">{suggestion.summary}</p>
                      <p className="mt-2 text-xs uppercase tracking-wide text-primary-700/70 dark:text-primary-200/70">
                        Confidence {Math.round(suggestion.confidence * 100)}%
                      </p>
                      {suggestion.hints && suggestion.hints.length > 0 && (
                        <ul className="mt-2 list-disc space-y-1 pl-4 text-xs text-primary-700/80 dark:text-primary-200/80">
                          {suggestion.hints.map((hint, index) => (
                            <li key={index}>{hint}</li>
                          ))}
                        </ul>
                      )}
                    </div>
                    <div className="mt-4 flex items-center gap-2">
                      <Button
                        type="button"
                        onClick={() =>
                          void handleSave({
                            actionType: suggestion.rule.actionType,
                            outcome: suggestion.rule.outcome,
                            conditions: suggestion.rule.conditions,
                            enabled: suggestion.rule.enabled,
                          })
                        }
                      >
                        Apply rule
                      </Button>
                      <Button
                        type="button"
                        variant="ghost"
                        onClick={() => {
                          setSelectedRule({
                            ...suggestion.rule,
                            id: suggestion.id,
                            priority: rules.length + 1,
                          } as Rule);
                          setModalOpen(true);
                        }}
                      >
                        Preview
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}

          <section className="mt-6" aria-live="polite" aria-busy={rulesQuery.isLoading}>
            {rulesQuery.isLoading ? (
              <p className="text-sm text-slate-600">Loading rules…</p>
            ) : rules.length === 0 ? (
              <p className="text-sm text-slate-600">No rules yet. Create one to automate triage.</p>
            ) : (
              <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
                <SortableContext items={rules.map((rule) => rule.id)} strategy={verticalListSortingStrategy}>
                  <div role="list" className="mt-4 space-y-3">
                    {rules.map((rule) => (
                      <SortableRule key={rule.id} rule={rule} onEdit={handleEdit} onToggle={handleToggle} />
                    ))}
                  </div>
                </SortableContext>
              </DndContext>
            )}
          </section>
        </main>
        <RuleEditorModal
          open={isModalOpen}
          rule={selectedRule}
          onClose={() => setModalOpen(false)}
          onSave={handleSave}
        />
      </div>
    </>
  );
}
