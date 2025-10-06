#!/usr/bin/env python3
import os
import re
import shlex
import subprocess
from pathlib import Path


WHITELIST = {
    "USE_DB",
    "SUPABASE_URL",
    "SUPABASE_SERVICE_KEY",
    "ADMIN_UI_ORIGIN",
    "CLIENT_UI_ORIGIN",
    "ADMIN_EMAIL",
    "ADMIN_SECRET",
    "ENCRYPTION_KEY",
    "NOTION_CLIENT_ID",
    "NOTION_CLIENT_SECRET",
    "NOTION_REDIRECT_URI",
    "NYLAS_CLIENT_ID",
    "NYLAS_CLIENT_SECRET",
    "NYLAS_API_URL",
    "NYLAS_REDIRECT_URI",
    "VERIFY_NYLAS",
    "DRY_RUN_DEFAULT",
    "MOCK_OAUTH",
    "POSTMARK_SERVER_TOKEN",
    "POSTMARK_FROM_EMAIL",
    "POSTMARK_MESSAGE_STREAM",
    "USE_POSTMARK",
    "USE_SMTP",
    "CALENDAR_NAME",
}


def parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not line or line.lstrip().startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        if k not in WHITELIST:
            continue
        v = v.rstrip("\r\n").strip()
        if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
            v = v[1:-1]
        values.setdefault(k, v)
    return values


def gh(cmd: list[str], input_str: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(["gh", *cmd], input=input_str.encode() if input_str is not None else None, check=True)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    env_paths = [repo_root / ".env", repo_root / ".env.local"]
    merged: dict[str, str] = {}
    for p in env_paths:
        merged.update(parse_env_file(p))

    if not merged:
        print("No whitelisted keys found in .env/.env.local.")
        return

    # Ensure gh is authenticated
    try:
        gh(["auth", "status"])
    except subprocess.CalledProcessError as e:
        raise SystemExit("gh is not authenticated. Run `gh auth login` and retry.") from e

    # Push each secret using gh CLI; safer than REST since gh handles encryption
    for k, v in merged.items():
        print(f"Setting GitHub Actions secret: {k}")
        gh(["secret", "set", k, "--app", "actions", "--body", v])

    print("All secrets set in GitHub Actions.")


if __name__ == "__main__":
    main()


