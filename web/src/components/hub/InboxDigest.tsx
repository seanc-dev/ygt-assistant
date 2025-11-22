import { useMemo, useCallback } from "react";
import { useRouter } from "next/router";
import { Panel, Stack, Heading, Text, Badge } from "@lucid-work/ui";
import { Button } from "@lucid-work/ui/primitives/Button";
import { getInboxDigest, type InboxDigestItem } from "../../lib/hubSelectors";
import { useFocusContextStore } from "../../state/focusContextStore";

export function InboxDigest() {
  const router = useRouter();
  const { pushFocus } = useFocusContextStore();
  const digest = useMemo(() => getInboxDigest(), []);

  const openTriage = useCallback(() => {
    pushFocus({ type: "triage" }, { source: "hub" });
    router.push("/workroom");
  }, [pushFocus, router]);

  const handleOpenItem = useCallback(
    (item: InboxDigestItem) => {
      if (item.relatedTaskId) {
        pushFocus({ type: "task", id: item.relatedTaskId }, { source: "hub" });
      } else {
        pushFocus({ type: "today" }, { source: "hub" });
      }
      router.push("/workroom");
    },
    [pushFocus, router]
  );

  return (
    <Panel>
      <Stack gap="md">
        <div className="flex items-center justify-between">
          <Heading as="h2" variant="title">
            Inbox Digest
          </Heading>
          <Button size="sm" variant="outline" onClick={openTriage} data-testid="open-triage-cta">
            Open Full Triage in Workroom
          </Button>
        </div>
        {digest.length === 0 ? (
          <Text variant="muted">No new updates.</Text>
        ) : (
          <div className="flex flex-col gap-3" data-testid="inbox-groups">
            {digest.map((group) => (
              <div key={group.source} className="rounded-lg border border-slate-200 bg-white">
                <div className="flex items-center justify-between border-b border-slate-100 px-3 py-2">
                  <Text variant="body" className="font-semibold">
                    {group.label}
                  </Text>
                  <Badge color="gray" variant="soft">
                    {group.items.length}
                  </Badge>
                </div>
                <div className="flex flex-col divide-y divide-slate-100">
                  {group.items.map((item) => (
                    <button
                      type="button"
                      key={item.id}
                      onClick={() => handleOpenItem(item)}
                      className="flex flex-col items-start gap-1 px-3 py-2 text-left hover:bg-slate-50"
                    >
                      <Text variant="body" className="font-semibold">
                        {item.subject}
                      </Text>
                      <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500">
                        <Badge color="gray" variant="outline">
                          {group.label}
                        </Badge>
                        {item.timestamp && <span>{new Date(item.timestamp).toLocaleTimeString()}</span>}
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </Stack>
    </Panel>
  );
}
