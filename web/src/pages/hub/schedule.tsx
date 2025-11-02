import { useEffect, useState } from "react";
import { Heading, Panel, Stack, Text, Button } from "@ygt-assistant/ui";
import { Layout } from "../../components/Layout";
import { api } from "../../lib/api";
import { ScheduleDayView } from "../../components/ScheduleDayView";
import { AltPlansPanel } from "../../components/AltPlansPanel";
import { CompactChat } from "../../components/CompactChat";

interface ScheduleEvent {
  id: string;
  title: string;
  start: string;
  end: string;
  link?: string;
}

interface ScheduleBlock {
  id: string;
  kind: "focus" | "admin" | "meeting";
  tasks: string[];
  start: string;
  end: string;
  priority: string;
}

interface ScheduleResponse {
  ok: boolean;
  events: ScheduleEvent[];
  blocks: ScheduleBlock[];
  date: string;
}

export default function SchedulePage() {
  const [loading, setLoading] = useState(true);
  const [schedule, setSchedule] = useState<ScheduleResponse | null>(null);
  const [alternatives, setAlternatives] = useState<any>(null);
  const [expandedBlockId, setExpandedBlockId] = useState<string | null>(null);
  const [showAlternatives, setShowAlternatives] = useState(false);

  const loadSchedule = async () => {
    try {
      const data = await api.scheduleToday();
      setSchedule(data as ScheduleResponse);
      setLoading(false);
    } catch (err) {
      console.error("Failed to load schedule:", err);
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSchedule();
  }, []);

  const handleViewAlternatives = async () => {
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
  };

  const handleEditInChat = (blockId: string) => {
    setExpandedBlockId(expandedBlockId === blockId ? null : blockId);
  };

  return (
    <Layout>
      <Stack gap="lg">
        <div className="flex flex-col gap-2">
          <Heading as="h1" variant="display">
            Schedule
          </Heading>
          <Text variant="muted">
            Today-first schedule merged with existing calendar events.
          </Text>
        </div>

        <div className="flex gap-2">
          <Button variant="secondary" onClick={handleViewAlternatives}>
            View Alternatives
          </Button>
        </div>

        {showAlternatives && alternatives && (
          <AltPlansPanel
            plans={alternatives.plans || []}
            overload={alternatives.overload}
          />
        )}

        {loading && !schedule ? (
          <Panel>
            <Text variant="muted">Loading schedule...</Text>
          </Panel>
        ) : schedule ? (
          <ScheduleDayView
            events={schedule.events}
            blocks={schedule.blocks}
            onEditInChat={handleEditInChat}
            expandedBlockId={expandedBlockId}
          />
        ) : (
          <Panel>
            <Text variant="muted">No schedule data available.</Text>
          </Panel>
        )}

        {expandedBlockId && (
          <Panel>
            <CompactChat threadId={expandedBlockId} />
          </Panel>
        )}
      </Stack>
    </Layout>
  );
}
