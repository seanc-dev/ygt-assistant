import { useEffect, useState } from "react";
import { Heading, Panel, Stack, Text, Button, useTheme, type ThemePreference } from "@lucid-work/ui";
import { Layout } from "../../components/Layout";
import { api } from "../../lib/api";
import { SettingsForm } from "../../components/SettingsForm";
import { HotkeysSettingsModal } from "../../components/HotkeysSettingsModal";

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
    hotkeys?: { [key: string]: string };
  };
}

interface SettingsResponse {
  ok: boolean;
  work_hours: UserSettings["work_hours"];
  time_zone: string;
  day_shape: UserSettings["day_shape"];
  translation: UserSettings["translation"];
  trust_level: UserSettings["trust_level"];
  ui_prefs: UserSettings["ui_prefs"];
}

export default function SettingsPage() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [settings, setSettings] = useState<UserSettings | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [showHotkeysModal, setShowHotkeysModal] = useState(false);
  const { theme, setTheme, resolvedTheme } = useTheme();

  const loadSettings = async () => {
    try {
      const data = await api.settings();
      setSettings(data as SettingsResponse);
      setLoading(false);
    } catch (err) {
      console.error("Failed to load settings:", err);
      setError("Failed to load settings");
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSettings();
  }, []);

  const handleSave = async (updatedSettings: UserSettings) => {
    setSaving(true);
    setError(null);
    setSuccess(false);

    try {
      await api.updateSettings(updatedSettings);
      setSettings(updatedSettings);
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch (err: any) {
      console.error("Failed to save settings:", err);
      setError(err.message || "Failed to save settings");
    } finally {
      setSaving(false);
    }
  };

  const handleSaveHotkeys = async (hotkeys: { [key: string]: string }) => {
    if (!settings) return;
    setSaving(true);
    setError(null);
    setSuccess(false);

    try {
      const updatedSettings = {
        ...settings,
        ui_prefs: {
          ...settings.ui_prefs,
          hotkeys,
        },
      };
      await api.updateSettings(updatedSettings);
      setSettings(updatedSettings);
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch (err: any) {
      console.error("Failed to save hotkeys:", err);
      setError(err.message || "Failed to save hotkeys");
    } finally {
      setSaving(false);
    }
  };

  return (
    <Layout>
      <Stack gap="lg">
        <div className="flex flex-col gap-2">
          <Heading as="h1" variant="display">
            Settings
          </Heading>
          <Text variant="muted">
            Work hours, translation rules, trust level, and UI preferences.
          </Text>
        </div>

        {error && (
          <Panel className="bg-red-50 border-red-200">
            <Text variant="body" className="text-red-600">
              {error}
            </Text>
          </Panel>
        )}

        {success && (
          <Panel className="bg-green-50 border-green-200">
            <Text variant="body" className="text-green-600">
              Settings saved successfully!
            </Text>
          </Panel>
        )}

        {/* Theme Selector */}
        <Panel>
          <div className="mb-4">
            <Text variant="label" className="text-sm font-medium">
              Theme
            </Text>
            <Text variant="caption" className="text-xs text-[var(--lw-neutral-muted)] mt-1">
              Choose your preferred color theme and accessibility options
            </Text>
          </div>
          <div className="mt-4">
            <select
              value={theme}
              onChange={(e) => setTheme(e.target.value as ThemePreference)}
              className="w-full border border-[var(--lw-border)] rounded-md px-3 py-2 text-sm bg-[var(--lw-surface)] text-[var(--lw-neutral-text)] focus:outline-none focus:ring-2 focus:ring-[var(--lw-primary)] focus:ring-opacity-40"
              style={{
                borderRadius: "var(--lw-radius-sm)",
              }}
            >
              <option value="system">System (Auto)</option>
              <option value="light">Light</option>
              <option value="dark">Dark</option>
              <option value="high-contrast">High Contrast</option>
              <option value="color-blind">Color Blind Safe</option>
            </select>
            <Text variant="caption" className="text-xs text-[var(--lw-neutral-muted)] mt-2">
              {theme === "system" ? (
                <>Currently using: {resolvedTheme === "dark" ? "Dark" : "Light"} mode (based on system preference)</>
              ) : (
                <>Active theme: {theme === "high-contrast" ? "High Contrast" : theme === "color-blind" ? "Color Blind Safe" : theme === "dark" ? "Dark" : "Light"}</>
              )}
            </Text>
          </div>
        </Panel>

        <Panel>
          <div className="flex justify-between items-center mb-4">
            <div>
              <Text variant="label" className="text-sm font-medium">
                Keyboard Shortcuts
              </Text>
              <Text variant="caption" className="text-xs text-[var(--lw-neutral-muted)] mt-1">
                Configure keyboard shortcuts for common actions
              </Text>
            </div>
            <Button variant="outline" onClick={() => setShowHotkeysModal(true)}>
              Configure Hotkeys
            </Button>
          </div>
        </Panel>

        {loading && !settings ? (
          <Panel>
            <Text variant="muted">Loading settings...</Text>
          </Panel>
        ) : settings ? (
          <SettingsForm settings={settings} onSave={handleSave} saving={saving} />
        ) : (
          <Panel>
            <Text variant="muted">No settings available.</Text>
          </Panel>
        )}
      </Stack>

      {showHotkeysModal && settings && (
        <HotkeysSettingsModal
          hotkeys={settings.ui_prefs?.hotkeys || {}}
          onSave={handleSaveHotkeys}
          onClose={() => setShowHotkeysModal(false)}
        />
      )}
    </Layout>
  );
}
