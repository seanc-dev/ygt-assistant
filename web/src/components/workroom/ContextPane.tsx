import { useState } from "react";
import { Text } from "@ygt-assistant/ui";
import {
  Document24Regular,
  Mail24Regular,
  Calendar24Regular,
  Link24Regular,
} from "@fluentui/react-icons";
import { useWorkroomStore } from "../../hooks/useWorkroomStore";

interface Reference {
  id: string;
  type: "document" | "email" | "event" | "file" | "task";
  title: string;
  preview?: string;
}

interface ContextPaneProps {
  projectId?: string;
  taskId?: string;
  projectTitle?: string;
  taskTitle?: string;
  open: boolean;
  onToggle: () => void;
  onInsertReference?: (ref: Reference) => void;
}

export function ContextPane({
  projectId,
  taskId,
  projectTitle,
  taskTitle,
  open,
  onToggle,
  onInsertReference,
}: ContextPaneProps) {
  const { setPrimaryView } = useWorkroomStore();
  const [activeSection, setActiveSection] = useState<
    "referenced" | "suggested" | "pinned" | "search"
  >("referenced");
  const [references, setReferences] = useState<Reference[]>([]);
  const [suggested, setSuggested] = useState<Reference[]>([]);
  const [pinned, setPinned] = useState<Reference[]>([]);

  // Determine scope label
  const scopeLabel =
    taskId && taskTitle
      ? `Context — Task: ${taskTitle}`
      : projectId && projectTitle
      ? `Context — Project: ${projectTitle}`
      : "Context";

  if (!open) {
    return null;
  }

  const handleDragStart = (ref: Reference) => {
    // Store reference data for drop
    if (typeof window !== "undefined") {
      (window as any).__draggedReference = ref;
    }
  };

  const getIcon = (type: Reference["type"]) => {
    switch (type) {
      case "document":
        return Document24Regular;
      case "email":
        return Mail24Regular;
      case "event":
        return Calendar24Regular;
      default:
        return Link24Regular;
    }
  };

  return (
    <div
      className="flex-1 flex flex-col border-l border-slate-200 bg-slate-50 min-h-0 h-100"
      style={{ width: "260px" }}
    >
      {/* Header */}
      <div className="p-3 border-b border-slate-200 flex items-center">
        <Text variant="label" className="text-sm font-medium">
          {scopeLabel}
        </Text>
      </div>

      {/* Tabs */}
      <div
        className="flex border-b border-slate-200"
        style={{ overflowX: "auto" }}
      >
        {[
          { id: "referenced", label: "Referenced" },
          { id: "suggested", label: "Suggested" },
          { id: "pinned", label: "Pinned" },
          { id: "search", label: "Search" },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveSection(tab.id as typeof activeSection)}
            className={`px-3 py-2 text-xs font-medium border-b-2 transition-colors ${
              activeSection === tab.id
                ? "border-blue-500 text-blue-600"
                : "border-transparent text-slate-600 hover:text-slate-900"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-3">
        {!taskId ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="border-2 border-dashed border-slate-300 rounded-lg p-6 max-w-sm">
              <Text variant="muted" className="text-sm mb-2">
                Context is only available for tasks.
              </Text>
              <button
                onClick={() => setPrimaryView("kanban")}
                className="text-xs text-sky-600 hover:text-sky-700 underline mt-2"
              >
                Open Kanban
              </button>
            </div>
          </div>
        ) : (
          <>
            {activeSection === "referenced" && (
              <div className="space-y-2">
                {references.length === 0 ? (
                  <div className="border-2 border-dashed border-slate-300 rounded-lg p-6 text-center">
                    <Text variant="muted" className="text-xs">
                      No references yet. Drag items here or click to add.
                    </Text>
                  </div>
                ) : (
                  references.map((ref) => {
                    const Icon = getIcon(ref.type);
                    return (
                      <div
                        key={ref.id}
                        draggable
                        onDragStart={() => handleDragStart(ref)}
                        onClick={() => onInsertReference?.(ref)}
                        className="p-2 rounded border border-slate-200 bg-white hover:bg-slate-50 cursor-move"
                      >
                        <div className="flex items-center gap-2">
                          <Icon className="w-4 h-4 text-slate-600" />
                          <div className="flex-1 min-w-0">
                            <Text
                              variant="body"
                              className="text-xs font-medium"
                            >
                              {ref.title}
                            </Text>
                            {ref.preview && (
                              <Text
                                variant="caption"
                                className="text-xs text-slate-500"
                              >
                                {ref.preview}
                              </Text>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            )}

            {activeSection === "suggested" && (
              <div className="space-y-2">
                {suggested.length === 0 ? (
                  <Text variant="muted" className="text-xs">
                    No suggestions available.
                  </Text>
                ) : (
                  suggested.map((ref) => {
                    const Icon = getIcon(ref.type);
                    return (
                      <div
                        key={ref.id}
                        draggable
                        onDragStart={() => handleDragStart(ref)}
                        onClick={() => onInsertReference?.(ref)}
                        className="p-2 rounded border border-slate-200 bg-white hover:bg-slate-50 cursor-move"
                      >
                        <div className="flex items-center gap-2">
                          <Icon className="w-4 h-4 text-slate-600" />
                          <div className="flex-1 min-w-0">
                            <Text
                              variant="body"
                              className="text-xs font-medium"
                            >
                              {ref.title}
                            </Text>
                          </div>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            )}

            {activeSection === "pinned" && (
              <div className="space-y-2">
                {pinned.length === 0 ? (
                  <Text variant="muted" className="text-xs">
                    No pinned items.
                  </Text>
                ) : (
                  pinned.map((ref) => {
                    const Icon = getIcon(ref.type);
                    return (
                      <div
                        key={ref.id}
                        draggable
                        onDragStart={() => handleDragStart(ref)}
                        onClick={() => onInsertReference?.(ref)}
                        className="p-2 rounded border border-slate-200 bg-white hover:bg-slate-50 cursor-move"
                      >
                        <div className="flex items-center gap-2">
                          <Icon className="w-4 h-4 text-slate-600" />
                          <div className="flex-1 min-w-0">
                            <Text
                              variant="body"
                              className="text-xs font-medium"
                            >
                              {ref.title}
                            </Text>
                          </div>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            )}

            {activeSection === "search" && (
              <div>
                <input
                  type="text"
                  placeholder="Search..."
                  className="w-full px-2 py-1 text-xs border border-slate-300 rounded"
                />
                <Text variant="muted" className="text-xs mt-2 block">
                  Search functionality coming soon.
                </Text>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
