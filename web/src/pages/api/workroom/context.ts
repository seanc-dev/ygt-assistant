import type { NextApiRequest, NextApiResponse } from "next";
import { buildWorkroomContext } from "../../../data/mockWorkroomData";
import type { FocusAnchorType } from "../../../lib/focusContext";
import type { WorkroomContext } from "../../../lib/workroomContext";

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  const anchorType = (req.query.anchorType || req.body?.anchorType) as FocusAnchorType | undefined;
  const anchorIdInput = (req.query.anchorId || req.body?.anchorId) as string | undefined;

  if (!anchorType) {
    res.status(400).json({ error: "anchorType is required" });
    return;
  }

  const anchorId = anchorType === "portfolio" ? anchorIdInput || "my_work" : anchorIdInput;
  if (!anchorId && anchorType !== "portfolio") {
    res.status(400).json({ error: "anchorId is required" });
    return;
  }

  const workroomContext: WorkroomContext | null = buildWorkroomContext({ type: anchorType, id: anchorId });

  if (!workroomContext) {
    res.status(404).json({ error: "Anchor not found" });
    return;
  }

  res.status(200).json({ workroomContext });
}
