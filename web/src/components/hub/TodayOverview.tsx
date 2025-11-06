import { useState, useCallback } from "react";
import { Panel, Stack, Text, Button, Heading } from "@ygt-assistant/ui";
import { useToday, useSettings } from "../../hooks/useHubData";
import { Schedule } from "./Schedule";
import { AltPlansPanel } from "../AltPlansPanel";
import { Toast } from "../Toast";
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

  // Calculate workload gauge
  const workHours = settings?.work_hours;
  const calculateWorkload = () => {
    if (!schedule || !workHours) return { planned: 0, available: 8, percentage: 0 };
    
    const startHour = parseInt(workHours.start.split(":")[0]);
    const endHour = parseInt(workHours.end.split(":")[0]);
    const availableHours = endHour - startHour;
    
    let plannedMinutes = 0;
    schedule.events?.forEach((event: any) => {
      const start = new Date(event.start);
      const end = new Date(event.end);
      plannedMinutes += (end.getTime() - start.getTime()) / (1000 * 60);
    });
    schedule.blocks?.forEach((block: any) => {
      const start = new Date(block.start);
      const end = new Date(block.end);
      plannedMinutes += (end.getTime() - start.getTime()) / (1000 * 60);
    });
    
    const plannedHours = plannedMinutes / 60;
    const percentage = Math.min((plannedHours / availableHours) * 100, 100);
    
    return { planned: plannedHours, available: availableHours, percentage };
  };

  const workload = calculateWorkload();

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

      {/* Right: Workload Gauge */}
      <Panel>
        <Stack gap="md">
          <Heading as="h2" variant="title">
            Workload
          </Heading>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <Text variant="body">Planned</Text>
              <Text variant="body" className="font-medium">
                {workload.planned.toFixed(1)}h / {workload.available}h
              </Text>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-4 overflow-hidden">
              <div
                className={`h-full transition-all ${
                  workload.percentage > 90
                    ? "bg-red-500"
                    : workload.percentage > 70
                    ? "bg-yellow-500"
                    : "bg-green-500"
                }`}
                style={{ width: `${workload.percentage}%` }}
              />
            </div>
            <Text variant="caption" className="text-xs text-gray-600">
              {workload.percentage > 90
                ? "Overloaded - consider alternatives"
                : workload.percentage > 70
                ? "Heavy day - review schedule"
                : "Manageable workload"}
            </Text>
          </div>
        </Stack>
      </Panel>
      {toast && <Toast message={toast} onClose={() => setToast("")} />}
    </div>
  );
}

