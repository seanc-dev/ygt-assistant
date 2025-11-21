import { Button } from "@lucid-work/ui/primitives/Button";
import { Text } from "@lucid-work/ui";
import { useFocusContextStore } from "../../state/focusContextStore";

export function FocusStackRail() {
  const { stack, popFocus } = useFocusContextStore();

  return (
    <div className="flex h-full flex-col gap-3 rounded-lg border border-slate-200 bg-white p-3 shadow-sm">
      <Text variant="body" className="text-sm font-semibold text-slate-700">
        Focus stack
      </Text>
      {stack.length === 0 ? (
        <Text variant="caption" className="text-xs text-slate-500">
          No previous focus yet
        </Text>
      ) : (
        <div className="flex flex-col gap-2">
          <Text variant="caption" className="text-xs text-slate-500">
            {stack.length} item{stack.length === 1 ? "" : "s"}
          </Text>
          <Button variant="outline" size="sm" onClick={popFocus}>
            Back to previous
          </Button>
        </div>
      )}
    </div>
  );
}
