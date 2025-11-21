import { useState, useCallback } from "react";
import { Panel, Stack, Text, Heading } from "@lucid-work/ui";
import { Button } from "@lucid-work/ui/primitives/Button";
import { useToday, useSettings } from "../../hooks/useHubData";
import { Schedule } from "./Schedule";
import { AltPlansPanel } from "../AltPlansPanel";
import { Toast } from "../Toast";
import { WorkloadPanel } from "./WorkloadPanel";
import { api } from "../../lib/api";

interface TodayOverviewProps {
  onEditInChat?: (blockId: string) => void;
}

export function TodayOverview({ onEditInChat }: TodayOverviewProps) {
  const { data: schedule, isLoading, mutate } = useToday();
  const { data: settings } = useSettings();
  const [alternatives, setAlternatives] = useState<any>(null);
  const [showAlternatives, setShowAlternatives] = useState(false);
  const [expandedBlockId, setExpandedBlockId] = useState<string | null>(null);
  const [toast, setToast] = useState<string>("");

  const handleSuggestAlternatives = useCallback(async () => {
    try {
      const data = await api.scheduleAlternatives({
        existing_events: schedule?.events || [],
        proposed_blocks: schedule?.blocks || [],
      });
      setAlternatives(data);
      setShowAlternatives(true);
      
      // Show toast notification
      if (data?.plans && data.plans.length > 0) {
        setToast(`Found ${data.plans.length} alternative schedule${data.plans.length > 1 ? "s" : ""}`);
      }
    } catch (err) {
      console.error("Failed to load alternatives:", err);
      setToast("Failed to load alternatives. Please try again.");
    }
  }, [schedule]);

  const handleEditInChat = useCallback((blockId: string) => {
    setExpandedBlockId(expandedBlockId === blockId ? null : blockId);
    onEditInChat?.(blockId);
  }, [expandedBlockId, onEditInChat]);

  const handleUpdateEvent = useCallback(async (id: string, updates: { start?: string; end?: string; title?: string; note?: string }) => {
    try {
      if (updates.start || updates.end) {
        await api.updateEventFull(id, updates);
      } else if (updates.title || updates.note) {
        await api.updateEventFull(id, updates);
      }
      // Refresh schedule data
      mutate();
    } catch (err) {
      console.error("Failed to update event:", err);
      setToast("Failed to update event. Please try again.");
    }
  }, [mutate]);

  const handleDuplicateEvent = useCallback(async (id: string) => {
    // TODO: Implement duplicate logic
    setToast("Duplicate functionality coming soon");
  }, []);

  const handleDeleteEvent = useCallback(async (id: string) => {
    // TODO: Implement delete logic
    setToast("Delete functionality coming soon");
  }, []);

  const handleAddFocusBlock = useCallback(() => {
    // TODO: Implement add focus block logic
    setToast("Add focus block functionality coming soon");
  }, []);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
      {/* Left: Day Timeline */}
      <Panel>
        <Stack gap="md">
          <div className="flex justify-between items-center">
            <Heading as="h2" variant="title">
              Today&apos;s Schedule
            </Heading>
            <Button variant="outline" onClick={handleSuggestAlternatives} size="sm">
              Suggest 3 Alternatives
            </Button>
          </div>

          {isLoading && !schedule ? (
            <Text variant="muted">Loading schedule...</Text>
          ) : schedule ? (
            <Schedule
              events={schedule.events || []}
              blocks={schedule.blocks || []}
              onEditInChat={handleEditInChat}
              onUpdateEvent={handleUpdateEvent}
              onDuplicateEvent={handleDuplicateEvent}
              onDeleteEvent={handleDeleteEvent}
            />
          ) : (
            <Text variant="muted">No schedule data available.</Text>
          )}

          {showAlternatives && alternatives && (
            <AltPlansPanel
              plans={alternatives.plans || []}
              overload={alternatives.overload}
            />
          )}
        </Stack>
      </Panel>

      {/* Right: Workload Intelligence Panel */}
      <WorkloadPanel onAddFocusBlock={handleAddFocusBlock} />
      {toast && <Toast message={toast} onClose={() => setToast("")} />}
    </div>
  );
}

