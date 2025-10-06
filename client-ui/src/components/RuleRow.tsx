import { Rule } from "../lib/types";
import { Button } from "./Button";

interface RuleRowProps {
  rule: Rule;
  onEdit: (rule: Rule) => void;
  onToggle: (rule: Rule, enabled: boolean) => void;
}

export function RuleRow({ rule, onEdit, onToggle }: RuleRowProps) {
  const conditionSummary = rule.conditions.length
    ? rule.conditions
        .map((condition, index) => {
          const description = `${condition.field} ${condition.op} ${condition.value}`;
          return index === 0 ? description : ` and ${description}`;
        })
        .join("")
    : "any action";

  return (
    <div
      className="flex items-start justify-between rounded-lg border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-700 dark:bg-slate-900"
      role="listitem"
    >
      <div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            className="focus-outline inline-flex items-center rounded-full border border-slate-300 bg-slate-100 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-slate-600 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-200"
            aria-pressed={rule.enabled}
            onClick={() => onToggle(rule, !rule.enabled)}
          >
            {rule.enabled ? "Enabled" : "Disabled"}
          </button>
          <span className="text-xs font-medium uppercase tracking-wide text-slate-500 dark:text-slate-400">
            Priority {rule.priority}
          </span>
        </div>
        {rule.name && (
          <p className="mt-2 text-sm font-semibold text-slate-900 dark:text-slate-100">{rule.name}</p>
        )}
        <p className="mt-2 text-sm font-medium text-slate-900 dark:text-slate-100">
          If {conditionSummary} → <span className="capitalize">{rule.outcome}</span>
        </p>
        <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-600 dark:text-slate-400">
          {rule.conditions.map((condition, index) => (
            <li key={index}>
              <span className="font-medium">{condition.field}</span> {condition.op}{" "}
              <span className="font-mono">{condition.value}</span>
            </li>
          ))}
        </ul>
        <p className="mt-3 text-sm text-slate-700 dark:text-slate-300">
          Outcome: <span className="font-semibold capitalize">{rule.outcome}</span>
        </p>
      </div>
      <Button onClick={() => onEdit(rule)} variant="secondary">
        Edit
      </Button>
    </div>
  );
}
