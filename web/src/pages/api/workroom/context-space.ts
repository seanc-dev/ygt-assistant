import type { NextApiRequest, NextApiResponse } from "next";
import type { FocusAnchorType } from "../../../lib/focusContext";
import { getMockContextSpace, saveMockContextSpace } from "../../../data/mockWorkroomData";

const validAnchorTypes: FocusAnchorType[] = ["task", "event", "project", "portfolio", "today", "triage"];

const parseAnchor = (req: NextApiRequest) => {
  const query = req.query ?? {};
  const anchorType = (query.anchorType || req.body?.anchorType) as FocusAnchorType | undefined;
  const anchorIdInput = (query.anchorId || req.body?.anchorId) as string | undefined;

  if (!anchorType || !validAnchorTypes.includes(anchorType)) {
    return { error: "anchorType is required" } as const;
  }

  const anchorId =
    anchorType === "portfolio"
      ? anchorIdInput || "my_work"
      : anchorType === "today" || anchorType === "triage"
        ? anchorIdInput || anchorType
        : anchorIdInput;
  if (!anchorId && anchorType !== "portfolio" && anchorType !== "today" && anchorType !== "triage") {
    return { error: "anchorId is required" } as const;
  }

  return { anchor: { type: anchorType, id: anchorId } } as const;
};

const sanitizeContextSpaceInput = (input: unknown) => {
  if (input === null || typeof input !== "object") return null;
  const payload = input as Record<string, unknown>;
  const sanitized: Record<string, unknown> = {};
  if (payload.summary === null || typeof payload.summary === "string") {
    sanitized.summary = payload.summary;
  }
  if (Array.isArray(payload.highlights)) {
    sanitized.highlights = payload.highlights.filter((item): item is string => typeof item === "string");
  }
  if (Array.isArray(payload.questions)) {
    sanitized.questions = payload.questions.filter((item): item is string => typeof item === "string");
  }
  return sanitized;
};

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  // Handle POST with entries array (for workroomApi.updateContextSpace)
  if (req.method === "POST" && Array.isArray(req.body?.entries)) {
    const entries = req.body.entries;
    res.status(200).json({ ok: true, added: entries.length });
    return;
  }

  // Handle GET/POST with anchor-based queries (for useWorkroomContextSpace)
  const parsedAnchor = parseAnchor(req);
  if ("error" in parsedAnchor) {
    res.status(400).json({ error: parsedAnchor.error });
    return;
  }

  const { anchor } = parsedAnchor;

  if (req.method === "GET") {
    const contextSpace = getMockContextSpace(anchor);
    res.status(200).json({ contextSpace });
    return;
  }

  if (req.method === "POST") {
    const sanitizedContextSpace = sanitizeContextSpaceInput(req.body?.contextSpace);
    if (!sanitizedContextSpace) {
      res.status(400).json({ error: "contextSpace is required" });
      return;
    }
    const contextSpace = saveMockContextSpace(anchor, sanitizedContextSpace);
    res.status(200).json({ contextSpace });
    return;
  }

  res.setHeader("Allow", "GET, POST");
  res.status(405).end("Method Not Allowed");
}
