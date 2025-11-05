import { useState, useEffect } from "react";
import { Button, Stack, Text, Panel } from "@lucid-work/ui";

interface UserSettings {
  work_hours: {
    start: string;
    end: string;
  };
  time_zone: string;
  day_shape: {
    morning_focus: boolean;
    focus_block_lengths_min: number[];
    focus_block_max_minutes: number;
    lunch_window: {
      start: string;
      end: string;
      min_minutes: number;
      max_minutes: number;
    };
    meeting_avoid_windows: Array<{
      start: string;
      end: string;
    }>;
    buffer_minutes: {
      min: number;
      max: number;
    };
  };
  translation: {
    default: "llm" | "azure";
    fallback: "llm" | "azure";
    rules: {
      outbound: "auto" | "prompt" | "off";
      inbound: "auto" | "prompt" | "off";
      internal: "auto" | "prompt" | "off";
      external: "auto" | "prompt" | "off";
    };
  };
  trust_level: "training_wheels" | "standard" | "autonomous";
  ui_prefs: {
    thread_open_behavior: string;
    brief: {
      weather: boolean;
      news: boolean;
      tone: string;
    };
  };
}

interface SettingsFormProps {
  settings: UserSettings;
  onSave: (settings: UserSettings) => void;
  saving: boolean;
}

// Common IANA timezones
const COMMON_TIMEZONES = [
  "UTC",
  "America/New_York",
  "America/Chicago",
  "America/Denver",
  "America/Los_Angeles",
  "America/Phoenix",
  "America/Anchorage",
  "Pacific/Honolulu",
  "Europe/London",
  "Europe/Paris",
  "Europe/Berlin",
  "Europe/Rome",
  "Asia/Tokyo",
  "Asia/Shanghai",
  "Asia/Hong_Kong",
  "Asia/Dubai",
  "Asia/Kolkata",
  "Australia/Sydney",
  "Australia/Melbourne",
  "Pacific/Auckland",
];

export function SettingsForm({ settings, onSave, saving }: SettingsFormProps) {
  const [formData, setFormData] = useState<UserSettings>(settings);

  useEffect(() => {
    setFormData(settings);
  }, [settings]);

  const updateField = (path: string[], value: any) => {
    const newData = { ...formData };
    let current: any = newData;
    for (let i = 0; i < path.length - 1; i++) {
      current = current[path[i]];
    }
    current[path[path.length - 1]] = value;
    setFormData(newData);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave(formData);
  };

  return (
    <form onSubmit={handleSubmit}>
      <Stack gap="lg">
        {/* Work Hours */}
        <Panel>
          <div className="mb-4">
            <Text variant="label" className="text-sm font-medium">
              Work Hours
            </Text>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-gray-600 mb-1 block">Start Time</label>
              <input
                type="time"
                value={formData.work_hours.start}
                onChange={(e) => updateField(["work_hours", "start"], e.target.value)}
                required
                className="w-full border rounded px-3 py-2 text-sm"
              />
            </div>
            <div>
              <label className="text-xs text-gray-600 mb-1 block">End Time</label>
              <input
                type="time"
                value={formData.work_hours.end}
                onChange={(e) => updateField(["work_hours", "end"], e.target.value)}
                required
                className="w-full border rounded px-3 py-2 text-sm"
              />
            </div>
          </div>
        </Panel>

        {/* Time Zone */}
        <Panel>
          <div className="mb-4">
            <Text variant="label" className="text-sm font-medium">
              Time Zone
            </Text>
          </div>
          <select
            value={formData.time_zone}
            onChange={(e) => updateField(["time_zone"], e.target.value)}
            className="w-full border rounded px-3 py-2 text-sm"
          >
            {COMMON_TIMEZONES.map((tz) => (
              <option key={tz} value={tz}>
                {tz}
              </option>
            ))}
          </select>
        </Panel>

        {/* Day Shape */}
        <Panel>
          <div className="mb-4">
            <Text variant="label" className="text-sm font-medium">
              Day Shape
            </Text>
          </div>
          <Stack gap="md">
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={formData.day_shape.morning_focus}
                onChange={(e) =>
                  updateField(["day_shape", "morning_focus"], e.target.checked)
                }
                className="rounded"
              />
              <label className="text-sm">Morning focus</label>
            </div>

            <div>
              <label className="text-xs text-gray-600 mb-1 block">
                Focus Block Lengths (minutes, comma-separated)
              </label>
              <input
                type="text"
                value={formData.day_shape.focus_block_lengths_min.join(", ")}
                onChange={(e) => {
                  const values = e.target.value
                    .split(",")
                    .map((v) => parseInt(v.trim()))
                    .filter((v) => !isNaN(v));
                  updateField(["day_shape", "focus_block_lengths_min"], values);
                }}
                placeholder="90, 60"
                className="w-full border rounded px-3 py-2 text-sm"
              />
            </div>

            <div>
              <label className="text-xs text-gray-600 mb-1 block">
                Focus Block Max (minutes)
              </label>
              <input
                type="number"
                min="30"
                value={formData.day_shape.focus_block_max_minutes}
                onChange={(e) =>
                  updateField(
                    ["day_shape", "focus_block_max_minutes"],
                    parseInt(e.target.value)
                  )
                }
                className="w-full border rounded px-3 py-2 text-sm"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-xs text-gray-600 mb-1 block">
                  Lunch Window Start
                </label>
                <input
                  type="time"
                  value={formData.day_shape.lunch_window.start}
                  onChange={(e) =>
                    updateField(["day_shape", "lunch_window", "start"], e.target.value)
                  }
                  className="w-full border rounded px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="text-xs text-gray-600 mb-1 block">
                  Lunch Window End
                </label>
                <input
                  type="time"
                  value={formData.day_shape.lunch_window.end}
                  onChange={(e) =>
                    updateField(["day_shape", "lunch_window", "end"], e.target.value)
                  }
                  className="w-full border rounded px-3 py-2 text-sm"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-xs text-gray-600 mb-1 block">
                  Lunch Min Minutes
                </label>
                <input
                  type="number"
                  value={formData.day_shape.lunch_window.min_minutes}
                  onChange={(e) =>
                    updateField(
                      ["day_shape", "lunch_window", "min_minutes"],
                      parseInt(e.target.value)
                    )
                  }
                  className="w-full border rounded px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="text-xs text-gray-600 mb-1 block">
                  Lunch Max Minutes
                </label>
                <input
                  type="number"
                  value={formData.day_shape.lunch_window.max_minutes}
                  onChange={(e) =>
                    updateField(
                      ["day_shape", "lunch_window", "max_minutes"],
                      parseInt(e.target.value)
                    )
                  }
                  className="w-full border rounded px-3 py-2 text-sm"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-xs text-gray-600 mb-1 block">
                  Buffer Min (minutes)
                </label>
                <input
                  type="number"
                  value={formData.day_shape.buffer_minutes.min}
                  onChange={(e) =>
                    updateField(
                      ["day_shape", "buffer_minutes", "min"],
                      parseInt(e.target.value)
                    )
                  }
                  className="w-full border rounded px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="text-xs text-gray-600 mb-1 block">
                  Buffer Max (minutes)
                </label>
                <input
                  type="number"
                  value={formData.day_shape.buffer_minutes.max}
                  onChange={(e) =>
                    updateField(
                      ["day_shape", "buffer_minutes", "max"],
                      parseInt(e.target.value)
                    )
                  }
                  className="w-full border rounded px-3 py-2 text-sm"
                />
              </div>
            </div>
          </Stack>
        </Panel>

        {/* Translation */}
        <Panel>
          <div className="mb-4">
            <Text variant="label" className="text-sm font-medium">
              Translation
            </Text>
          </div>
          <Stack gap="md">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-xs text-gray-600 mb-1 block">Default</label>
                <select
                  value={formData.translation.default}
                  onChange={(e) =>
                    updateField(["translation", "default"], e.target.value)
                  }
                  className="w-full border rounded px-3 py-2 text-sm"
                >
                  <option value="llm">LLM</option>
                  <option value="azure">Azure</option>
                </select>
              </div>
              <div>
                <label className="text-xs text-gray-600 mb-1 block">Fallback</label>
                <select
                  value={formData.translation.fallback}
                  onChange={(e) =>
                    updateField(["translation", "fallback"], e.target.value)
                  }
                  className="w-full border rounded px-3 py-2 text-sm"
                >
                  <option value="llm">LLM</option>
                  <option value="azure">Azure</option>
                </select>
              </div>
            </div>

            <div>
              <label className="text-xs text-gray-600 mb-2 block">Translation Rules</label>
              <div className="space-y-2">
                {(["outbound", "inbound", "internal", "external"] as const).map((rule) => (
                  <div key={rule} className="flex items-center justify-between">
                    <label className="text-sm capitalize">{rule}</label>
                    <select
                      value={formData.translation.rules[rule]}
                      onChange={(e) =>
                        updateField(["translation", "rules", rule], e.target.value)
                      }
                      className="border rounded px-2 py-1 text-sm"
                    >
                      <option value="auto">Auto</option>
                      <option value="prompt">Prompt</option>
                      <option value="off">Off</option>
                    </select>
                  </div>
                ))}
              </div>
            </div>
          </Stack>
        </Panel>

        {/* Trust Level */}
        <Panel>
          <div className="mb-4">
            <Text variant="label" className="text-sm font-medium">
              Trust Level
            </Text>
          </div>
          <select
            value={formData.trust_level}
            onChange={(e) => updateField(["trust_level"], e.target.value)}
            className="w-full border rounded px-3 py-2 text-sm"
          >
            <option value="training_wheels">Training Wheels</option>
            <option value="standard">Standard</option>
            <option value="autonomous">Autonomous</option>
          </select>
        </Panel>

        {/* UI Preferences */}
        <Panel>
          <div className="mb-4">
            <Text variant="label" className="text-sm font-medium">
              UI Preferences
            </Text>
          </div>
          <Stack gap="md">
            <div>
              <label className="text-xs text-gray-600 mb-1 block">
                Thread Open Behavior
              </label>
              <select
                value={formData.ui_prefs.thread_open_behavior}
                onChange={(e) =>
                  updateField(["ui_prefs", "thread_open_behavior"], e.target.value)
                }
                className="w-full border rounded px-3 py-2 text-sm"
              >
                <option value="new_tab">New Tab</option>
                <option value="same_tab">Same Tab</option>
              </select>
            </div>

            <div>
              <label className="text-xs text-gray-600 mb-2 block">Brief Preferences</label>
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={formData.ui_prefs.brief.weather}
                    onChange={(e) =>
                      updateField(["ui_prefs", "brief", "weather"], e.target.checked)
                    }
                    className="rounded"
                  />
                  <label className="text-sm">Show weather</label>
                </div>
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={formData.ui_prefs.brief.news}
                    onChange={(e) =>
                      updateField(["ui_prefs", "brief", "news"], e.target.checked)
                    }
                    className="rounded"
                  />
                  <label className="text-sm">Show news</label>
                </div>
                <div>
                  <label className="text-xs text-gray-600 mb-1 block">Tone</label>
                  <select
                    value={formData.ui_prefs.brief.tone}
                    onChange={(e) =>
                      updateField(["ui_prefs", "brief", "tone"], e.target.value)
                    }
                    className="w-full border rounded px-3 py-2 text-sm"
                  >
                    <option value="neutral">Neutral</option>
                    <option value="professional">Professional</option>
                    <option value="casual">Casual</option>
                  </select>
                </div>
              </div>
            </div>
          </Stack>
        </Panel>

        {/* Save Button */}
        <div className="flex justify-end">
          <Button type="submit" disabled={saving}>
            {saving ? "Saving..." : "Save Settings"}
          </Button>
        </div>
      </Stack>
    </form>
  );
}
