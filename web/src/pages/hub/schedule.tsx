import { Stack, Heading, Text, Panel, Button } from "@ygt-assistant/ui";
import { Layout } from "../../components/Layout";
import { useToday, useSettings } from "../../hooks/useHubData";
import { Schedule } from "../../components/hub/Schedule";
import { AltPlansPanel } from "../../components/AltPlansPanel";
import { api } from "../../lib/api";
import { useState, useCallback } from "react";

export default function SchedulePage() {
  const { data: schedule, isLoading, mutate } = useToday();
  const { data: settings } = useSettings();
  const [alternatives, setAlternatives] = useState<any>(null);
  const [showAlternatives, setShowAlternatives] = useState(false);
  const [expandedBlockId, setExpandedBlockId] = useState<string | null>(null);

  const handleSuggestAlternatives = useCallback(async () => {
    try {
      const data = await api.scheduleAlternatives({
        existing_events: schedule?.events || [],
        proposed_blocks: schedule?.blocks || [],
      });
      setAlternatives(data);
      setShowAlternatives(true);
    } catch (err) {
      console.error("Failed to load alternatives:", err);
    }
  }, [schedule]);

  const handleEditInChat = useCallback((blockId: string) => {
    setExpandedBlockId(expandedBlockId === blockId ? null : blockId);
  }, [expandedBlockId]);

  const handleUpdateEvent = useCallback(async (id: string, updates: { start?: string; end?: string; title?: string; note?: string }) => {
    try {
      await api.updateEventFull(id, updates);
      mutate();
    } catch (err) {
      console.error("Failed to update event:", err);
    }
  }, [mutate]);

  const handleDuplicateEvent = useCallback(async (id: string) => {
    // TODO: Implement duplicate logic
  }, []);

  const handleDeleteEvent = useCallback(async (id: string) => {
    // TODO: Implement delete logic
  }, []);

  return (
    <Layout>
      <Stack gap="lg">
        <div className="flex justify-between items-center">
          <div>
            <Heading as="h1" variant="display">
              Schedule
            </Heading>
            <Text variant="muted">
              Today&apos;s schedule with existing events and proposed blocks
            </Text>
          </div>
          <Button variant="outline" onClick={handleSuggestAlternatives}>
            Generate Alternatives
          </Button>
        </div>

        {isLoading && !schedule ? (
          <Panel>
            <Text variant="muted">Loading schedule...</Text>
          </Panel>
        ) : schedule ? (
          <>
            <Panel>
              <Schedule
                events={schedule.events || []}
                blocks={schedule.blocks || []}
                onEditInChat={handleEditInChat}
                onUpdateEvent={handleUpdateEvent}
                onDuplicateEvent={handleDuplicateEvent}
                onDeleteEvent={handleDeleteEvent}
              />
            </Panel>

            {showAlternatives && alternatives && (
              <AltPlansPanel
                plans={alternatives.plans || []}
                overload={alternatives.overload}
              />
            )}
          </>
        ) : (
          <Panel>
            <Text variant="muted">No schedule data available.</Text>
          </Panel>
        )}
      </Stack>
    </Layout>
  );
}
