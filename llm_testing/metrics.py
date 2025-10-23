from __future__ import annotations
from typing import Any, Dict, List
import json
import os
from pathlib import Path


def aggregate(run_dir: str) -> Dict[str, Any]:
    d = Path(run_dir)
    scores: List[float] = []
    for p in d.glob("*.graded.json"):
        with open(p, "r") as f:
            data = json.load(f)
        s = data.get("evaluation", {}).get("scores", {})
        # average
        vals = [float(v) for v in s.values()] or [0.0]
        scores.append(sum(vals) / len(vals))
    avg = sum(scores) / len(scores) if scores else 0.0
    return {"avg": avg, "count": len(scores)}


def gate(avg: float, threshold: float) -> int:
    return 0 if avg >= threshold else 1
