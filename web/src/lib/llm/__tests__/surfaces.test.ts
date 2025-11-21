import { describe, it, expect, vi, beforeEach } from "vitest";
import {
  parseInteractiveSurfaces,
  SurfaceOpTrigger,
  clearSurfaceCache,
} from "../surfaces";

describe("parseInteractiveSurfaces", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    clearSurfaceCache(); // Clear cache before each test
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
      {
        surface_id: "s-3",
        kind: "context_add_v1",
        title: "Attach context",
        payload: {
          headline: "Quick links",
          items: [
            {
              contextId: "doc-123",
              label: "Product brief",
              sourceType: "doc",
              summary: "Use this when writing the update",
              addOp: "[op v:1 type:\"add_context\" id:\"doc-123\"]",
            },
          ],
        },
      },
    ];

    const surfaces = parseInteractiveSurfaces(raw);
    expect(surfaces).toHaveLength(3);
    expect(surfaces[0].kind).toBe("what_next_v1");
    expect(surfaces[1].kind).toBe("priority_list_v1");
    expect(surfaces[2].kind).toBe("context_add_v1");
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

  it("memoizes parsed surfaces by surface_id and payload hash", () => {
    const raw = {
      surface_id: "s-cached",
      kind: "what_next_v1",
      title: "Cached Surface",
      payload: {
        primary: {
          headline: "Test headline",
        },
      },
    };

    // First parse
    const surfaces1 = parseInteractiveSurfaces([raw]);
    expect(surfaces1).toHaveLength(1);
    const firstSurface = surfaces1[0];

    // Second parse with identical input - should use cache
    const surfaces2 = parseInteractiveSurfaces([raw]);
    expect(surfaces2).toHaveLength(1);
    // Should be the same object reference (cached)
    expect(surfaces2[0]).toBe(firstSurface);
  });

  it("re-parses when surface_id changes", () => {
    const raw1 = {
      surface_id: "s-1",
      kind: "what_next_v1",
      title: "Surface 1",
      payload: {
        primary: {
          headline: "Same payload",
        },
      },
    };
    const raw2 = {
      surface_id: "s-2",
      kind: "what_next_v1",
      title: "Surface 2",
      payload: {
        primary: {
          headline: "Same payload",
        },
      },
    };

    const surfaces1 = parseInteractiveSurfaces([raw1]);
    const surfaces2 = parseInteractiveSurfaces([raw2]);

    expect(surfaces1).toHaveLength(1);
    expect(surfaces2).toHaveLength(1);
    expect(surfaces1[0].surface_id).toBe("s-1");
    expect(surfaces2[0].surface_id).toBe("s-2");
    // Different surface_ids should produce different objects
    expect(surfaces1[0]).not.toBe(surfaces2[0]);
  });

  it("re-parses when payload changes for same surface_id", () => {
    const raw1 = {
      surface_id: "s-same",
      kind: "what_next_v1",
      title: "Surface",
      payload: {
        primary: {
          headline: "Original",
        },
      },
    };
    const raw2 = {
      surface_id: "s-same",
      kind: "what_next_v1",
      title: "Surface",
      payload: {
        primary: {
          headline: "Modified",
        },
      },
    };

    const surfaces1 = parseInteractiveSurfaces([raw1]);
    const surfaces2 = parseInteractiveSurfaces([raw2]);

    expect(surfaces1).toHaveLength(1);
    expect(surfaces2).toHaveLength(1);
    expect(surfaces1[0].payload.primary.headline).toBe("Original");
    expect(surfaces2[0].payload.primary.headline).toBe("Modified");
    // Different payloads should produce different objects
    expect(surfaces1[0]).not.toBe(surfaces2[0]);
  });

  it("handles surfaces without surface_id (no caching)", () => {
    const raw = {
      kind: "what_next_v1",
      title: "No ID",
      payload: {
        primary: {
          headline: "Test",
        },
      },
    };

    const surfaces1 = parseInteractiveSurfaces([raw]);
    const surfaces2 = parseInteractiveSurfaces([raw]);

    expect(surfaces1).toHaveLength(0); // Missing surface_id is invalid
  });
});

