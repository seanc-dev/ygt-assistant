from __future__ import annotations
from typing import List
import argparse
import json
import os
from pathlib import Path

from llm_testing.harness import run_scenario
from llm_testing.evaluator import evaluate


def run(paths: List[str]) -> str:
    run_id = None
    for p in paths:
        res = run_scenario(p)
        run_id = res["run_id"]
        graded_path = Path(res["report"]).with_suffix(".graded.json")
        ev = evaluate(res["report"])
        with open(graded_path, "w") as f:
            json.dump({"evaluation": ev}, f, indent=2)
    return run_id or ""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--scenarios", nargs="*")
    parser.add_argument(
        "--live",
        action="store_true",
        help="Run scenarios against live LLM provider (sets LLM_TESTING_MODE=false)",
    )
    args = parser.parse_args()

    if args.live:
        os.environ["LLM_TESTING_MODE"] = "false"

    if args.all:
        paths = sorted(str(p) for p in Path("llm_testing/scenarios").glob("*.yaml"))
    else:
        paths = args.scenarios
    run_id = run(paths)
    print(run_id)


if __name__ == "__main__":
    main()
