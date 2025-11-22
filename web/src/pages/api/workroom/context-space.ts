import type { NextApiRequest, NextApiResponse } from "next";

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== "POST") {
    res.status(405).json({ ok: false, error: "Method not allowed" });
    return;
  }

  const entries = Array.isArray(req.body?.entries) ? req.body.entries : [];
  res.status(200).json({ ok: true, added: entries.length });
}

