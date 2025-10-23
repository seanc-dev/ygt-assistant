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
        new = src.replace(
            "Tone: {tone or 'neutral'}", "Tone: {tone or 'calm'}"
        ).replace("Quick update", "Quick, calm update")
        if new != src:
            llm_py.write_text(new)
            edited.append(str(llm_py))
    return edited


def _current_branch() -> str:
    return (
        subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, check=True
        )
        .stdout.decode()
        .strip()
    )


def apply_changes(run_id: str, edited_files: List[str], fixes: List[str], *, direct: bool) -> None:
    base_branch = _current_branch()
    subprocess.run(["git", "add", *edited_files], check=True)
    msg = f"chore(llm): prompt tweaks from eval run {run_id}\n\n" + "\n".join(
        f"- {f}" for f in fixes
    )
    if direct:
        # Commit directly on the current branch (feature branches preferred)
        subprocess.run(["git", "commit", "-m", msg], check=True)
        subprocess.run(["git", "push"], check=True)
        return

    # Otherwise create a short-lived branch and open a PR against the current branch
    branch = f"fix/llm-prompt-{run_id}"
    subprocess.run(["git", "checkout", "-b", branch], check=True)
    subprocess.run(["git", "commit", "-m", msg], check=True)
    subprocess.run(["git", "push", "-u", "origin", branch], check=True)
    body = "\n".join(
        [
            f"Auto-patch from eval run {run_id}.",
            "Fixes:",
            *[f"- {f}" for f in fixes],
            "\nRequires two local passes before merge.",
        ]
    )
    subprocess.run(
        [
            "gh",
            "pr",
            "create",
            "--base",
            base_branch,
            "--head",
            branch,
            "--title",
            f"LLM prompt tweaks ({run_id})",
            "--body",
            body,
        ],
        check=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_id")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--direct", action="store_true", help="Commit directly on current branch (default when not on main)")
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
        # Default behavior: direct commit when current branch != main, else PR
        cur = _current_branch()
        direct = args.direct or (cur != "main")
        apply_changes(args.run_id, edited, fixes_all, direct=direct)
    else:
        print("No changes applied.")


if __name__ == "__main__":
    main()
