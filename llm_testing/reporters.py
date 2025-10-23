from __future__ import annotations
from typing import Any, Dict
import json
from pathlib import Path


def write_markdown(run_dir: str, out_path: str) -> None:
    d = Path(run_dir)
    lines = ["# LLM Evals Report\n"]
    for p in sorted(d.glob("*.graded.json")):
        with open(p, "r") as f:
            data = json.load(f)
        name = p.stem.replace(".graded", "")
        scores = data.get("evaluation", {}).get("scores", {})
        lines.append(f"- {name}: {scores}\n")
    with open(out_path, "w") as f:
        f.write("\n".join(lines))
