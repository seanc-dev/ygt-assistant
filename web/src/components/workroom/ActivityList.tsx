import { Text } from "@ygt-assistant/ui";

interface ActivityListProps {
  taskId: string;
}

export function ActivityList({ taskId }: ActivityListProps) {
  // TODO: Implement activity log
  return (
    <div className="p-4">
      <Text variant="muted" className="text-sm">
        Activity log coming soon
      </Text>
    </div>
  );
}

