import { useEffect, useState } from "react";
import { Heading, Panel, Stack, Text } from "@ygt-assistant/ui";
import { Layout } from "../../components/Layout";
import { api } from "../../lib/api";

interface BriefResponse {
  ok: boolean;
  date: string;
  summary: string;
  weather?: {
    condition: string;
    temp: string;
    location: string;
  };
  news?: Array<{
    title: string;
    summary: string;
    source: string;
  }>;
  tone: string;
}

export default function BriefPage() {
  const [loading, setLoading] = useState(true);
  const [brief, setBrief] = useState<BriefResponse | null>(null);

  useEffect(() => {
    api
      .briefToday()
      .then((data) => {
        setBrief(data as BriefResponse);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  return (
    <Layout>
      <Stack gap="lg">
        <div className="flex flex-col gap-2">
          <Heading as="h1" variant="display">
            Brief
          </Heading>
          <Text variant="muted">
            Daily orientation with optional weather and news.
          </Text>
        </div>

        {loading && !brief ? (
          <Panel>
            <Text variant="muted">Loading brief...</Text>
          </Panel>
        ) : brief ? (
          <Stack gap="md">
            <Panel>
              <Text variant="body">{brief.summary}</Text>
            </Panel>

            {brief.weather && (
              <Panel>
                <div className="font-medium text-sm mb-2">Weather</div>
                <Text variant="body">
                  {brief.weather.condition}, {brief.weather.temp} in{" "}
                  {brief.weather.location}
                </Text>
              </Panel>
            )}

            {brief.news && brief.news.length > 0 && (
              <Panel>
                <div className="font-medium text-sm mb-2">Top News</div>
                <Stack gap="sm">
                  {brief.news.map((item, idx) => (
                    <div key={idx}>
                      <Text variant="label" className="text-sm">
                        {item.title}
                      </Text>
                      <Text variant="caption" className="text-xs">
                        {item.summary}
                      </Text>
                      <Text variant="caption" className="text-xs text-gray-500">
                        {item.source}
                      </Text>
                    </div>
                  ))}
                </Stack>
              </Panel>
            )}
          </Stack>
        ) : (
          <Panel>
            <Text variant="muted">No brief available.</Text>
          </Panel>
        )}
      </Stack>
    </Layout>
  );
}
