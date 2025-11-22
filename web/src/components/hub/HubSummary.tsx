import { useMemo } from "react";
import { Panel, Stack, Text, Badge, Heading } from "@lucid-work/ui";
import { useProfile, useSettings, useSummary, useWhatNextSurface } from "../../hooks/useHubData";
import { parseInteractiveSurfaces } from "../../lib/llm/surfaces";
import { AssistantSurfacesRenderer } from "../assistant/AssistantSurfacesRenderer";

function getGreeting(): string {
  const hour = new Date().getHours();
  if (hour < 12) return "Good morning";
  if (hour < 18) return "Good afternoon";
  return "Good evening";
}

function getStatusChip(label: string, count: number, tone: "success" | "warning" | "danger" | "neutral" = "neutral") {
  if (count === 0) return null;
  return (
    <Badge tone={tone}>
      {label}: {count}
    </Badge>
  );
}

interface HubSummaryProps {
  actionCount?: number;
  meetingsToday?: number;
  syncState?: "synced" | "syncing" | "error";
  trustMode?: "training_wheels" | "standard" | "autonomous";
}

export function HubSummary({ actionCount, meetingsToday, syncState, trustMode }: HubSummaryProps) {
  const { data: profile } = useProfile();
  const { data: settings } = useSettings();
  const { data: summary } = useSummary();
  const { data: whatNextData } = useWhatNextSurface();
  const whatNextSurface = useMemo(() => {
    if (!whatNextData?.surface) {
      return null;
    }
    return parseInteractiveSurfaces([whatNextData.surface])[0] ?? null;
  }, [whatNextData]);

  const userName = profile?.name || profile?.email?.split("@")[0] || "there";
  const greeting = getGreeting();

  // Check if weather/news are enabled in settings
  const showWeather = settings?.ui_prefs?.brief?.weather ?? false;
  const showNews = settings?.ui_prefs?.brief?.news ?? false;

  const weather = summary?.weather;
  const news = summary?.news;

  return (
    <Panel>
      <Stack gap="md">
        <div>
          <Heading as="h1" variant="display">
            {greeting}, {userName}
          </Heading>
        </div>

        {whatNextSurface && (
          <AssistantSurfacesRenderer surfaces={[whatNextSurface]} />
        )}

        {(showWeather && weather) || (showNews && news && news.length > 0) ? (
          <div className="flex flex-wrap gap-2 text-sm text-gray-600">
            {showWeather && weather && (
              <Text variant="caption">
                {weather.condition}, {weather.temp} in {weather.location}
              </Text>
            )}
            {showNews && news && news.length > 0 && (
              <Text variant="caption">
                Top news: {news[0]?.title}
              </Text>
            )}
          </div>
        ) : null}

        <div className="flex flex-wrap gap-2">
          {getStatusChip("Actions", actionCount || 0, actionCount && actionCount > 5 ? "warning" : "neutral")}
          {getStatusChip("Meetings today", meetingsToday || 0, "neutral")}
          {syncState && (
            <Badge tone={syncState === "synced" ? "success" : syncState === "error" ? "danger" : "warning"}>
              {syncState === "synced" ? "Synced" : syncState === "error" ? "Sync error" : "Syncing..."}
            </Badge>
          )}
          {trustMode && (
            <Badge tone="neutral">
              Trust: {trustMode.replace("_", " ")}
            </Badge>
          )}
        </div>
      </Stack>
    </Panel>
  );
}

