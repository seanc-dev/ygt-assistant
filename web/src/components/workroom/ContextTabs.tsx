import { useState, type ReactNode } from "react";
import { Text } from "@ygt-assistant/ui";

export type ContextTabId = "neighborhood" | "context" | "docs";

interface ContextTabsProps {
  neighborhood: ReactNode;
  context: ReactNode;
  docs: ReactNode;
  initialTab?: ContextTabId;
}

export function ContextTabs({
  neighborhood,
  context,
  docs,
  initialTab = "neighborhood",
}: ContextTabsProps) {
  const [activeTab, setActiveTab] = useState<ContextTabId>(initialTab);

  const renderContent = () => {
    switch (activeTab) {
      case "context":
        return context;
      case "docs":
        return docs;
      case "neighborhood":
      default:
        return neighborhood;
    }
  };

  const tabs: Array<{ id: ContextTabId; label: string; badge?: string }> = [
    { id: "neighborhood", label: "Neighborhood" },
    { id: "context", label: "Context" },
    { id: "docs", label: "Docs" },
  ];

  return (
    <div className="flex h-full flex-col rounded-lg border border-slate-200 bg-white shadow-sm">
      <div className="flex items-center justify-between border-b border-slate-200 px-3 py-2">
        <Text variant="body" className="text-sm font-semibold text-slate-800">
          Right rail
        </Text>
      </div>
      <div className="flex items-center gap-1 border-b border-slate-200 px-2 py-1">
        {tabs.map((tab) => {
          const isActive = tab.id === activeTab;
          return (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveTab(tab.id)}
              className={`rounded-md px-3 py-2 text-xs font-medium transition ${
                isActive
                  ? "bg-slate-900 text-white shadow-sm"
                  : "text-slate-700 hover:bg-slate-50"
              }`}
              aria-pressed={isActive}
            >
              {tab.label}
            </button>
          );
        })}
      </div>
      <div className="flex-1 overflow-y-auto p-3" data-testid={`context-tab-${activeTab}`}>
        {renderContent()}
      </div>
    </div>
  );
}
