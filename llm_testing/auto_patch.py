from __future__ import annotations
from typing import Any, Dict, List
import argparse
import json
import os
from pathlib import Path
import re
import subprocess


def _is_true(v: str | None) -> bool:
    return (v or "").strip().lower() in {"1", "true", "yes", "on"}


def load_reports(run_id: str) -> List[Path]:
    d = Path("llm_testing") / "reports" / run_id
    return sorted(d.glob("*.graded.json"))


def infer_prompt_fixes(report_path: Path) -> List[str]:
    with open(report_path, "r") as f:
        data = json.load(f)
    ev = data.get("evaluation", {})
    ok = bool(ev.get("ok", False))
    rationale = ev.get("rationale", "")
    fixes: List[str] = []
    if ok:
        return fixes
    if re.search(r"tone", rationale, re.I):
        fixes.append("Adjust default tone to 'calm' in services/llm.py draft_email")
    if re.search(r"clarity", rationale, re.I):
        fixes.append("Shorten default subject/body phrasing in draft_email")
    if re.search(r"safety|unapproved|booking", rationale, re.I):
        fixes.append("Ensure safe policy: don't schedule externally without approval")
    if not fixes:
        fixes.append("Improve rubric alignment phrasing in summarise_and_propose")
    return fixes


def apply_minimal_diffs() -> List[str]:
    # Simple targeted edit: switch default tone to 'calm' and tweak subject
    edited: List[str] = []
    llm_py = Path("services/llm.py")
    if llm_py.exists():
        src = llm_py.read_text()
        new = src.replace("Tone: {tone or 'neutral'}", "Tone: {tone or 'calm'}").replace("Quick update", "Quick, calm update")
        if new != src:
            llm_py.write_text(new)
            edited.append(str(llm_py))
    return edited


def open_branch_and_pr(run_id: str, edited_files: List[str], fixes: List[str]) -> None:
    branch = f"fix/llm-prompt-{run_id}"
    subprocess.run(["git", "checkout", "-b", branch], check=True)
    subprocess.run(["git", "add", *edited_files], check=True)
    msg = f"chore(llm): prompt tweaks from eval run {run_id}\n\n" + "\n".join(f"- {f}" for f in fixes)
    subprocess.run(["git", "commit", "-m", msg], check=True)
    subprocess.run(["git", "push", "-u", "origin", branch], check=True)
    body = "\n".join([
        f"Auto-patch from eval run {run_id}.",
        "Fixes:",
        *[f"- {f}" for f in fixes],
        "\nRequires two local passes before merge.",
    ])
    subprocess.run([
        "gh", "pr", "create",
        "--base", "main",
        "--head", branch,
        "--title", f"LLM prompt tweaks ({run_id})",
        "--body", body,
    ], check=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_id")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    reports = load_reports(args.run_id)
    fixes_all: List[str] = []
    for r in reports:
        fixes_all.extend(infer_prompt_fixes(r))
    if args.dry_run:
        print("\n".join(fixes_all))
        return
    edited = apply_minimal_diffs()
    if edited:
        open_branch_and_pr(args.run_id, edited, fixes_all)
    else:
        print("No changes applied.")


if __name__ == "__main__":
    main()


