import type { NextApiRequest, NextApiResponse } from "next";
import { vi } from "vitest";
import handler from "@/pages/api/workroom/context-space";
import {
  mockContextSpaceByAnchor,
  resetMockContextSpaceStore,
} from "@/data/mockWorkroomData";

type MockResponse = NextApiResponse & {
  statusCode: number;
  jsonPayload: any;
};

const createResponse = (): MockResponse => {
  const res: Partial<MockResponse> = {
    statusCode: 200,
    jsonPayload: undefined,
    setHeader: vi.fn(),
    end: vi.fn(),
    status(code: number) {
      this.statusCode = code;
      return this as MockResponse;
    },
    json(payload: any) {
      this.jsonPayload = payload;
      return this as MockResponse;
    },
  };
  return res as MockResponse;
};

describe("/api/workroom/context-space", () => {
  beforeEach(() => {
    resetMockContextSpaceStore();
  });

  it("returns stored context space for a known anchor", () => {
    const req = {
      method: "GET",
      query: { anchorType: "task", anchorId: "task-1" },
    } as unknown as NextApiRequest;
    const res = createResponse();

    handler(req, res);

    expect(res.statusCode).toBe(200);
    expect(res.jsonPayload?.contextSpace?.summary).toContain("Drafting new workroom UX");
    expect(res.jsonPayload?.contextSpace?.highlights).toContain("Sync with design");
  });

  it("returns default empty context space when none is stored", () => {
    const req = {
      method: "GET",
      query: { anchorType: "task", anchorId: "missing-task" },
    } as unknown as NextApiRequest;
    const res = createResponse();

    handler(req, res);

    expect(res.statusCode).toBe(200);
    expect(res.jsonPayload?.contextSpace?.summary).toBeNull();
    expect(res.jsonPayload?.contextSpace?.highlights).toEqual([]);
    expect(res.jsonPayload?.contextSpace?.questions).toEqual([]);
  });

  it("saves context space while stripping unknown fields", () => {
    const req = {
      method: "POST",
      body: {
        anchorType: "project",
        anchorId: "alpha",
        contextSpace: {
          summary: "Alpha overview",
          highlights: ["Key milestone"],
          questions: ["What is the next deliverable?"],
          ignoredField: "remove me",
        },
      },
    } as unknown as NextApiRequest;
    const res = createResponse();

    handler(req, res);

    expect(res.statusCode).toBe(200);
    expect(res.jsonPayload?.contextSpace).toMatchObject({
      anchor: { type: "project", id: "alpha" },
      summary: "Alpha overview",
      highlights: ["Key milestone"],
      questions: ["What is the next deliverable?"],
    });
    expect(res.jsonPayload?.contextSpace?.ignoredField).toBeUndefined();
    expect(mockContextSpaceByAnchor["project:alpha"].summary).toBe("Alpha overview");
  });
});
