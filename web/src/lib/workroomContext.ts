import type { TaskStatus } from "../hooks/useWorkroomStore";

export type WorkroomContextAnchor =
  | {
      type: "task";
      id: string;
      title: string;
      status?: TaskStatus;
      priority?: string;
      linkedEventId?: string | null;
    }
  | {
      type: "event";
      id: string;
      title: string;
      start?: string;
      end?: string;
      linkedTaskIds?: string[];
    }
  | {
      type: "project";
      id: string;
      name: string;
    }
  | {
      type: "portfolio";
      id: "my_work";
      label: string;
    };

export type WorkroomNeighborhood = {
  tasks?: Array<{ id: string; title: string; status?: TaskStatus }>;
  events?: Array<{ id: string; title: string; start?: string; end?: string }>;
  docs?: Array<{ id: string; title: string }>;
  queueItems?: Array<{ id: string; subject: string }>;
};

export type WorkroomContext = {
  anchor: WorkroomContextAnchor;
  neighborhood: WorkroomNeighborhood;
  // Future expansion points
  // schedule?: ...
  // surfaceInput?: ...
};
