import { Stack, Heading, Text, Panel, Button } from "@lucid-work/ui";
import { Layout } from "../../components/Layout";
import { useSummary } from "../../hooks/useHubData";
import { useState } from "react";

export default function BriefPage() {
  const { data: brief, isLoading, mutate } = useSummary();
  const [refreshing, setRefreshing] = useState(false);

  const handleRefresh = async () => {
    setRefreshing(true);
    await mutate();
    setTimeout(() => setRefreshing(false), 500);
  };

  return (
    <Layout>
      <Stack gap="lg">
        <div className="flex justify-between items-center">
          <div>
            <Heading as="h1" variant="display">
              Brief
            </Heading>
            <Text variant="muted">
              Today&apos;s orientation with weather and news
            </Text>
          </div>
          <Button variant="outline" onClick={handleRefresh} disabled={refreshing}>
            {refreshing ? "Refreshing..." : "Refresh"}
          </Button>
        </div>

        {isLoading && !brief ? (
          <Panel>
            <Text variant="muted">Loading brief...</Text>
          </Panel>
        ) : brief ? (
          <Stack gap="md">
            {/* Summary */}
            <Panel>
              <Stack gap="sm">
                <Text variant="label" className="text-sm font-medium">
                  Summary
                </Text>
                <Text variant="body">{brief.summary || "No summary available."}</Text>
                {brief.date && (
                  <Text variant="caption" className="text-xs text-gray-500">
                    {new Date(brief.date).toLocaleDateString("en-US", {
                      weekday: "long",
                      year: "numeric",
                      month: "long",
                      day: "numeric",
                    })}
                  </Text>
                )}
              </Stack>
            </Panel>

            {/* Weather */}
            {brief.weather && (
              <Panel>
                <Stack gap="sm">
                  <Text variant="label" className="text-sm font-medium">
                    Weather
                  </Text>
                  <div className="flex items-center gap-4">
                    <Text variant="body" className="text-2xl">
                      {brief.weather.condition}
                    </Text>
                    <Text variant="body" className="text-xl">
                      {brief.weather.temp}
                    </Text>
                    {brief.weather.location && (
                      <Text variant="muted" className="text-sm">
                        {brief.weather.location}
                      </Text>
                    )}
                  </div>
                </Stack>
              </Panel>
            )}

            {/* News */}
            {brief.news && brief.news.length > 0 && (
              <Panel>
                <Stack gap="sm">
                  <Text variant="label" className="text-sm font-medium">
                    News
                  </Text>
                  <Stack gap="xs">
                    {brief.news.map((item: any, idx: number) => (
                      <div key={idx} className="border-l-2 border-blue-200 pl-3 py-1">
                        <Text variant="body" className="font-medium">
                          {item.title}
                        </Text>
                        {item.summary && (
                          <Text variant="muted" className="text-sm mt-1">
                            {item.summary}
                          </Text>
                        )}
                        {item.source && (
                          <Text variant="caption" className="text-xs text-gray-500 mt-1">
                            {item.source}
                          </Text>
                        )}
                      </div>
                    ))}
                  </Stack>
                </Stack>
              </Panel>
            )}

            {/* Tone indicator */}
            {brief.tone && (
              <Panel className="bg-gray-50">
                <Text variant="caption" className="text-xs text-gray-600">
                  Tone: <span className="capitalize">{brief.tone}</span>
                </Text>
              </Panel>
            )}
          </Stack>
        ) : (
          <Panel>
            <Text variant="muted">No brief data available.</Text>
          </Panel>
        )}
      </Stack>
    </Layout>
  );
}
