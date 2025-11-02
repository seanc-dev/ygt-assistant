import { useState, useEffect } from "react";
import { Button, Panel, Stack, Text, Heading } from "@ygt-assistant/ui";
import { formatKeyCombo } from "../hooks/useHotkeys";

interface HotkeysSettingsModalProps {
  hotkeys: { [key: string]: string };
  onSave: (hotkeys: { [key: string]: string }) => void;
  onClose: () => void;
}

const HOTKEY_LABELS: { [key: string]: string } = {
  approve: "Approve/Reply",
  edit: "Edit",
  defer: "Defer",
  add_to_today: "Add to Today",
  open_workroom: "Open in Workroom",
  collapse: "Collapse",
  kanban_toggle: "Kanban Toggle",
  settings: "Open Settings",
};

const DEFAULT_HOTKEYS: { [key: string]: string } = {
  approve: "a",
  edit: "e",
  defer: "d",
  add_to_today: "t",
  open_workroom: "o",
  collapse: "Escape",
  kanban_toggle: "Meta+k",
  settings: "Meta+,",
};

export function HotkeysSettingsModal({
  hotkeys,
  onSave,
  onClose,
}: HotkeysSettingsModalProps) {
  const [editingKey, setEditingKey] = useState<string | null>(null);
  const [localHotkeys, setLocalHotkeys] = useState<{ [key: string]: string }>(hotkeys);

  useEffect(() => {
    setLocalHotkeys(hotkeys);
  }, [hotkeys]);

  const handleKeyDown = (event: React.KeyboardEvent, action: string) => {
    event.preventDefault();
    event.stopPropagation();

    const modifiers: string[] = [];
    if (event.metaKey) modifiers.push("Meta");
    if (event.ctrlKey) modifiers.push("Control");
    if (event.altKey) modifiers.push("Alt");
    if (event.shiftKey) modifiers.push("Shift");

    const key = event.key === " " ? "Space" : event.key;
    const combo = modifiers.length > 0 ? `${modifiers.join("+")}+${key}` : key;

    setLocalHotkeys((prev) => ({
      ...prev,
      [action]: combo,
    }));
    setEditingKey(null);
  };

  const handleReset = (action: string) => {
    setLocalHotkeys((prev) => ({
      ...prev,
      [action]: DEFAULT_HOTKEYS[action] || "",
    }));
  };

  const handleResetAll = () => {
    setLocalHotkeys(DEFAULT_HOTKEYS);
  };

  const handleSave = () => {
    onSave(localHotkeys);
    onClose();
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="hotkeys-modal-title"
    >
      <Panel
        className="w-full max-w-2xl max-h-[80vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <Stack gap="lg">
          <div>
            <Heading as="h2" id="hotkeys-modal-title">
              Configure Keyboard Shortcuts
            </Heading>
            <Text variant="muted" className="mt-2">
              Click on a key combination to edit it. Press the keys you want to use.
            </Text>
          </div>

          <div className="space-y-2">
            {Object.entries(HOTKEY_LABELS).map(([action, label]) => (
              <div
                key={action}
                className="flex items-center justify-between p-3 border rounded"
                role="group"
                aria-label={`${label} shortcut configuration`}
              >
                <div>
                  <Text variant="label" className="text-sm font-medium">
                    {label}
                  </Text>
                </div>
                <div className="flex items-center gap-2">
                  {editingKey === action ? (
                    <input
                      type="text"
                      autoFocus
                      onKeyDown={(e) => handleKeyDown(e, action)}
                      onBlur={() => setEditingKey(null)}
                      placeholder="Press keys..."
                      className="border rounded px-2 py-1 text-sm w-32"
                      aria-label={`Edit ${label} shortcut`}
                    />
                  ) : (
                    <>
                      <Button
                        variant="secondary"
                        onClick={() => setEditingKey(action)}
                        className="text-xs"
                        aria-label={`Current shortcut: ${formatKeyCombo(localHotkeys[action] || DEFAULT_HOTKEYS[action] || "")}`}
                      >
                        {formatKeyCombo(localHotkeys[action] || DEFAULT_HOTKEYS[action] || "")}
                      </Button>
                      <Button
                        variant="ghost"
                        onClick={() => handleReset(action)}
                        className="text-xs"
                        aria-label={`Reset ${label} to default`}
                      >
                        Reset
                      </Button>
                    </>
                  )}
                </div>
              </div>
            ))}
          </div>

          <div className="flex justify-between items-center pt-4 border-t">
            <Button variant="ghost" onClick={handleResetAll}>
              Reset All to Defaults
            </Button>
            <div className="flex gap-2">
              <Button variant="secondary" onClick={onClose}>
                Cancel
              </Button>
              <Button onClick={handleSave}>Save</Button>
            </div>
          </div>
        </Stack>
      </Panel>
    </div>
  );
}

