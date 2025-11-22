import { Panel, Stack, Text, Heading, Button } from "@lucid-work/ui";
import { useRecent } from "../../hooks/useHubData";
import { useRouter } from "next/router";
import { useFocusContextStore } from "../../state/focusContextStore";

interface RecentItem {
  id: string;
  title: string;
  source: "outlook" | "teams" | "docs";
  preview?: string;
  timestamp?: string;
  thread_id?: string;
}

interface RecentResponse {
  ok: boolean;
  items: RecentItem[];
}

export function QuickReview() {
  const router = useRouter();
  const { data: recentData } = useRecent();
  const recent = recentData as RecentResponse | undefined;
  const { pushFocus } = useFocusContextStore();

  const items = recent?.items || [];
  const displayItems = items.slice(0, 3);

  const getSourceColor = (source: string) => {
    switch (source) {
      case "outlook":
        return "bg-blue-100 text-blue-800 border-blue-200";
      case "teams":
        return "bg-purple-100 text-purple-800 border-purple-200";
      case "docs":
        return "bg-green-100 text-green-800 border-green-200";
      default:
        return "bg-gray-100 text-gray-800 border-gray-200";
    }
  };

  const handleOpenInWorkroom = (item: RecentItem) => {
    pushFocus(
      { type: "task", id: item.id },
      { source: "hub_surface", surfaceKind: "quick_review", surfaceId: item.id }
    );
    router.push("/workroom");
  };

  if (displayItems.length === 0) {
    return null; // Hide if no items
  }

  return (
    <Panel>
      <Stack gap="md">
        <div className="flex justify-between items-center">
          <Heading as="h2" variant="title">
            Quick Review
          </Heading>
          <Button
            variant="outline"
            size="sm"
            onClick={() => router.push("/history")}
          >
            Yesterday&apos;s Wrap-up →
          </Button>
        </div>

        <div className="space-y-3">
          {displayItems.map((item) => (
            <div
              key={item.id}
              className="border rounded-lg p-3 hover:bg-gray-50 transition-colors cursor-pointer"
              onClick={() => handleOpenInWorkroom(item)}
            >
              <div className="flex items-center justify-between mb-2">
                <span
                  className={`text-xs px-2 py-1 rounded border ${getSourceColor(item.source)}`}
                >
                  {item.source.toUpperCase()}
                </span>
                {item.timestamp && (
                  <Text variant="caption" className="text-xs text-gray-500">
                    {new Date(item.timestamp).toLocaleDateString()}
                  </Text>
                )}
              </div>
              <Text variant="body" className="text-sm font-medium mb-1">
                {item.title}
              </Text>
              {item.preview && (
                <Text variant="caption" className="text-xs text-gray-600 line-clamp-2">
                  {item.preview}
                </Text>
              )}
            </div>
          ))}
        </div>

        <div className="pt-2 border-t">
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              pushFocus(
                { type: "portfolio", id: "my_work" },
                { source: "hub_surface", surfaceKind: "quick_review" }
              );
              router.push("/workroom");
            }}
            className="w-full"
          >
            Open My Work board
          </Button>
        </div>
      </Stack>
    </Panel>
  );
}

