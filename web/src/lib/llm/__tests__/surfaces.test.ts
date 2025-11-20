import { describe, it, expect, vi, beforeEach } from "vitest";
import {
  parseInteractiveSurfaces,
  SurfaceOpTrigger,
} from "../surfaces";

describe("parseInteractiveSurfaces", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("returns typed surfaces for valid payloads", () => {
    const raw = [
      {
        surface_id: "s-1",
        kind: "what_next_v1",
        title: "What's Next",
        payload: {
          primary: {
            headline: "Focus on pitch deck",
            body: "Estimate 45 min",
            primaryAction: {
              label: "Open task",
              navigateTo: { destination: "workroom_task", taskId: "task-1" },
            },
          },
        },
      },
      {
        surface_id: "s-2",
        kind: "priority_list_v1",
        title: "Top priorities",
        payload: {
          items: [
            {
              rank: 1,
              taskId: "task-1",
              label: "Prepare pitch",
              quickActions: [
                { label: "Mark doing", opToken: "[op v:1 type:\"update_task_status\"]" },
              ] as SurfaceOpTrigger[],
            },
          ],
        },
      },
    ];

    const surfaces = parseInteractiveSurfaces(raw);
    expect(surfaces).toHaveLength(2);
    expect(surfaces[0].kind).toBe("what_next_v1");
    expect(surfaces[1].kind).toBe("priority_list_v1");
  });

  it("drops unknown kinds and logs warning", () => {
    const warn = vi.spyOn(console, "warn").mockImplementation(() => {});
    const surfaces = parseInteractiveSurfaces([
      {
        surface_id: "s-x",
        kind: "unknown",
        title: "Nope",
        payload: {},
      },
    ]);
    expect(surfaces).toHaveLength(0);
    expect(warn).toHaveBeenCalled();
  });

  it("drops malformed payloads without throwing", () => {
    const warn = vi.spyOn(console, "warn").mockImplementation(() => {});
    const surfaces = parseInteractiveSurfaces([
      {
        surface_id: "s-1",
        kind: "what_next_v1",
        title: "Missing primary",
        payload: {},
      },
      {
        surface_id: "s-2",
        kind: "today_schedule_v1",
        title: "Missing blocks",
        payload: {},
      },
    ]);
    expect(surfaces).toHaveLength(0);
    expect(warn).toHaveBeenCalledTimes(2);
  });
});

